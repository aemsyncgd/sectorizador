import csv
import re
import unicodedata
from collections import Counter

def normalizar_texto(texto):
    """Elimina acentos y convierte a minúsculas para comparaciones robustas."""
    if not texto: return ""
    texto = str(texto).lower()
    # Eliminar acentos
    texto = "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto.strip()

def extraer_zonas(direccion):
    """Extrae posibles nombres de sectores, calles o urbanizaciones de una dirección."""
    # Patrones comunes en direcciones venezolanas
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

def main():
    archivo_csv = 'lista-direcciones-ejemplo.csv'
    clientes = []
    
    try:
        with open(archivo_csv, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clientes.append(row)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo_csv}")
        return

    # 1. Analizar zonas y agrupar
    todas_las_zonas = []
    for c in clientes:
        c['Zonas_Detectadas'] = extraer_zonas(c.get('Dirección', ''))
        todas_las_zonas.extend(c['Zonas_Detectadas'])

    conteo_zonas = Counter(todas_las_zonas)
    
    print("\n" + "="*50)
    print(" ANALIZADOR DE SECTORES (Expert Mode)")
    print("="*50)
    print(f"Total de clientes analizados: {len(clientes)}")
    print("\nResumen de zonas detectadas (Top 10):")
    for zona, count in conteo_zonas.most_common(10):
        print(f" - {zona:30} | {count} clientes")
    print("="*50)

    # 2. Interacción de búsqueda
    print("\n¿Qué zona o calle deseas filtrar? (Ej: Mariño, Naranjillos, Mangos)")
    print("Presiona Enter para ver todos los sectores detectados.")
    busqueda = input(">> ").strip()
    
    if not busqueda:
        # Si no hay búsqueda, mostramos todo el resumen extendido
        print("\nLista completa de zonas:")
        for zona, count in conteo_zonas.most_common():
            print(f" - {zona:30} | {count}")
        return

    termino_norm = normalizar_texto(busqueda)
    afectados = []

    for c in clientes:
        dir_norm = normalizar_texto(c.get('Dirección', ''))
        if termino_norm in dir_norm:
            afectados.append(c)

    # 3. Mostrar resultados
    print("\n" + "*"*50)
    print(f" RESULTADOS PARA: {busqueda.upper()}")
    print("*"*50)
    
    if not afectados:
        print("No se encontraron clientes en esa zona.")
    else:
        print(f"Se encontraron {len(afectados)} clientes afectados:")
        print("-" * 80)
        print(f"{'Nombre':35} | {'Dirección'}")
        print("-" * 80)
        for a in afectados:
            # Limpiar nombre de posibles comillas extra
            nombre = a.get('Nombre', 'N/A').strip("'\" ")
            direccion = a.get('Dirección', 'N/A')[:80] + "..." if len(a.get('Dirección', '')) > 80 else a.get('Dirección', 'N/A')
            print(f"{nombre:35} | {direccion}")
        
        print("-" * 80)
        
        # Opción de exportar
        guardar = input("\n¿Deseas guardar estos resultados en un archivo CSV? (s/n): ").lower()
        if guardar == 's':
            nombre_salida = f"afectados_{normalizar_texto(busqueda).replace(' ', '_')}.csv"
            with open(nombre_salida, 'w', newline='', encoding='utf-8') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=['Nombre', 'Cédula', 'Email', 'Dirección'])
                writer.writeheader()
                for a in afectados:
                    # Limpiamos antes de guardar
                    row_clean = {k: v for k, v in a.items() if k != 'Zonas_Detectadas'}
                    writer.writerow(row_clean)
            print(f"\n[OK] Archivo guardado como: {nombre_salida}")

if __name__ == "__main__":
    main()