// Colores de clases (deben coincidir con visualize.py)
const CLASS_COLORS = {
    0: "#000000",   // No data
    1: "#006400",   // Tree cover
    2: "#ffbb22",   // Shrubland
    3: "#ffff4c",   // Grassland
    4: "#f096ff",   // Cropland
    5: "#fa0000",   // Built-up
    6: "#b4b4b4",   // Bare / sparse
    7: "#f0f0f0",   // Snow and ice
    8: "#0064c8",   // Open water
    9: "#0096a0",   // Herbaceous wetland
    10: "#00cf75",  // Mangroves
    11: "#fae6a0",  // Moss and lichen
};

// Inicializar mapa
const map = L.map('map').setView([12.55, -81.72], 13);

// Capa base
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
}).addTo(map);

// Capa de imagen Sentinel-2 (opcional, requiere token)
// L.tileLayer('https://services.sentinel-hub.com/ogc/wms/...').addTo(map);

// Función para cargar estadísticas
async function loadStats() {
    const loading = document.getElementById('loading');
    const btn = document.getElementById('btn-stats');
    
    loading.classList.add('active');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('stats-container').innerHTML = 
                `<p style="color: #d32f2f;">${data.error}</p>`;
            return;
        }
        
        // Ordenar por porcentaje
        const sorted = Object.entries(data).sort((a, b) => b[1].percentage - a[1].percentage);
        
        let html = '';
        for (const [className, stats] of sorted) {
            const color = getClassColor(className);
            html += `
                <div class="stat-item" style="border-left-color: ${color};">
                    <span class="label">${className}</span>
                    <span class="value">${stats.percentage}%</span>
                </div>
            `;
        }
        
        document.getElementById('stats-container').innerHTML = html;
        
    } catch (error) {
        document.getElementById('stats-container').innerHTML = 
            `<p style="color: #d32f2f;">Error: ${error.message}</p>`;
    } finally {
        loading.classList.remove('active');
        btn.disabled = false;
    }
}

// Función para cargar mapa interactivo
async function loadMap() {
    const loading = document.getElementById('loading');
    const btn = document.getElementById('btn-map');
    
    loading.classList.add('active');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/map');
        const html = await response.text();
        
        if (html.includes('error')) {
            alert('No hay mapa disponible. Ejecuta el pipeline primero.');
            return;
        }
        
        // Abrir en nueva ventana o mostrar en modal
        const win = window.open('', '_blank');
        win.document.write(html);
        win.document.close();
        
    } catch (error) {
        alert('Error cargando mapa: ' + error.message);
    } finally {
        loading.classList.remove('active');
        btn.disabled = false;
    }
}

// Obtener color por nombre de clase
function getClassColor(className) {
    const colorMap = {
        "No data": "#000000",
        "Tree cover": "#006400",
        "Shrubland": "#ffbb22",
        "Grassland": "#ffff4c",
        "Cropland": "#f096ff",
        "Built-up": "#fa0000",
        "Bare / sparse vegetation": "#b4b4b4",
        "Snow and ice": "#f0f0f0",
        "Open water": "#0064c8",
        "Herbaceous wetland": "#0096a0",
        "Mangroves": "#00cf75",
        "Moss and lichen": "#fae6a0",
    };
    return colorMap[className] || "#999999";
}

// Cargar estadísticas al inicio
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
});
