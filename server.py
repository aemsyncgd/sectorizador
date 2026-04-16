from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
import io
import re
import unicodedata
from collections import Counter

app = FastAPI()

# Permitir CORS para desarrollo local con Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalizar_texto(texto):
    if not texto: return ""
    texto = str(texto).lower()
    texto = "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto.strip()

def detectar_columna_direccion(headers, first_rows):
    """Detecta automáticamente qué columna tiene las direcciones."""
    keywords = ['direccion', 'ubicacion', 'calle', 'sector', 'address', 'zona']
    
    # 1. Intentar por nombre de encabezado
    for i, h in enumerate(headers):
        h_norm = normalizar_texto(h)
        if any(kw in h_norm for kw in keywords):
            return h

    # 2. Intentar por contenido (si encuentra palabras clave en los datos)
    for h in headers:
        for row in first_rows:
            val = normalizar_texto(row.get(h, ""))
            if any(kw in val for kw in ['sector', 'urb.', 'calle', 'casa', 'av.']):
                return h
                
    return headers[-1] # Fallback a la última columna

def extraer_zonas(direccion):
    patrones = [
        r"(sector|calle|urb\.|urbanización|barrio|residencia|c\.c\.|avenida|av\.)\s+([a-z0-9\sñáéíóú]+?)(?=[,\.]|$)",
    ]
    zonas_encontradas = []
    dir_norm = direccion.lower()
    for patron in patrones:
        matches = re.findall(patron, dir_norm)
        for prefijo, nombre in matches:
            zonas_encontradas.append(f"{prefijo.capitalize()} {nombre.strip().title()}")
    return zonas_encontradas

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")
    
    content = await file.read()
    try:
        # Detectar encoding
        stream = io.StringIO(content.decode('utf-8-sig'))
    except UnicodeDecodeError:
        stream = io.StringIO(content.decode('latin-1'))
    
    reader = csv.DictReader(stream)
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    
    headers = reader.fieldnames
    col_direccion = detectar_columna_direccion(headers, rows[:5])
    
    todas_las_zonas = []
    processed_rows = []
    
    for row in rows:
        direccion = row.get(col_direccion, "")
        zonas = extraer_zonas(direccion)
        todas_las_zonas.extend(zonas)
        # Limpiar datos para el frontend
        clean_row = {k: (v.strip("'\" ") if v else "") for k, v in row.items()}
        clean_row['detected_zones'] = zonas
        clean_row['full_address'] = direccion
        processed_rows.append(clean_row)
        
    conteo_zonas = Counter(todas_las_zonas)
    summary = [{"name": zona, "count": count} for zona, count in conteo_zonas.most_common()]
    
    return {
        "filename": file.filename,
        "address_column": col_direccion,
        "total_clients": len(rows),
        "summary": summary,
        "clients": processed_rows,
        "headers": headers
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
