import './style.css'

interface Client {
    Nombre?: string;
    Dirección?: string;
    full_address: string;
    detected_zones: string[];
    [key: string]: any;
}

interface SummaryItem {
    name: string;
    count: number;
}

interface UploadResponse {
    filename: string;
    address_column: string;
    total_clients: number;
    summary: SummaryItem[];
    clients: Client[];
    headers: string[];
}

let allClients: Client[] = [];
let currentFilter: string = '';

const fileInput = document.getElementById('csv-upload') as HTMLInputElement;
const fileInfo = document.getElementById('file-info')!;
const zoneList = document.getElementById('zone-list')!;
const searchInput = document.getElementById('search-input') as HTMLInputElement;
const clientsBody = document.getElementById('clients-body')!;
const totalClientsEl = document.getElementById('total-clients')!;
const totalZonesEl = document.getElementById('total-zones')!;
const detectedColEl = document.getElementById('detected-col')!;
const dataStatus = document.getElementById('data-status')!;
const copyListBtn = document.getElementById('copy-list')!;

// Handle File Upload
fileInput.addEventListener('change', async (e) => {
    const file = fileInput.files?.[0];
    if (!file) return;

    fileInfo.textContent = `Analizando: ${file.name}...`;
    dataStatus.textContent = 'Procesando...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error al subir el archivo');

        const data: UploadResponse = await response.json();
        handleDataLoad(data);
    } catch (err) {
        console.error(err);
        dataStatus.textContent = 'Error al procesar archivo';
        fileInfo.textContent = 'Ocurrió un error.';
    }
});

function handleDataLoad(data: UploadResponse) {
    allClients = data.clients;
    fileInfo.textContent = `Archivo: ${data.filename}`;
    totalClientsEl.textContent = data.total_clients.toString();
    totalZonesEl.textContent = data.summary.length.toString();
    detectedColEl.textContent = data.address_column;
    dataStatus.textContent = 'Datos cargados';

    renderZones(data.summary);
    renderTable(allClients);
}

function renderZones(summary: SummaryItem[]) {
    zoneList.innerHTML = '';
    summary.slice(0, 20).forEach(zone => {
        const div = document.createElement('div');
        div.className = 'zone-item';
        div.innerHTML = `
            <span>${zone.name}</span>
            <span class="zone-count">${zone.count}</span>
        `;
        div.onclick = () => {
            searchInput.value = zone.name;
            filterData(zone.name);
        };
        zoneList.appendChild(div);
    });
}

function renderTable(clients: Client[]) {
    clientsBody.innerHTML = '';
    if (clients.length === 0) {
        clientsBody.innerHTML = '<tr><td colspan="2" class="empty-table">No se encontraron resultados</td></tr>';
        return;
    }

    clients.forEach(client => {
        const tr = document.createElement('tr');
        // Limpiamos el nombre de comillas si existen
        const nombre = (client.Nombre || 'N/A').replace(/['"]/g, '');
        tr.innerHTML = `
            <td><strong>${nombre}</strong></td>
            <td>${client.full_address}</td>
        `;
        clientsBody.appendChild(tr);
    });
}

// Search Logic
searchInput.addEventListener('input', (e) => {
    const val = (e.target as HTMLInputElement).value;
    filterData(val);
});

function filterData(query: string) {
    currentFilter = query.toLowerCase();
    const filtered = allClients.filter(c => {
        const searchPool = `${c.Nombre} ${c.full_address}`.toLowerCase();
        // Normalizar simple para la búsqueda en el front
        return searchPool.includes(currentFilter);
    });
    renderTable(filtered);
}

// Copy Logic
copyListBtn.addEventListener('click', () => {
    const query = searchInput.value;
    const filtered = allClients.filter(c => {
        const searchPool = `${c.Nombre} ${c.full_address}`.toLowerCase();
        return searchPool.includes(query.toLowerCase());
    });

    if (filtered.length === 0) return;

    const listText = filtered.map(c => `- ${c.Nombre}: ${c.full_address}`).join('\n');
    navigator.clipboard.writeText(listText);
    
    const originalText = copyListBtn.textContent;
    copyListBtn.textContent = '¡Copiado!';
    copyListBtn.style.background = '#238636';
    setTimeout(() => {
        copyListBtn.textContent = originalText;
        copyListBtn.style.background = '';
    }, 2000);
});
