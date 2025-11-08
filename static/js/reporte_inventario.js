function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Cerrar sidebar al hacer click fuera en móvil
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    }
});

let reporteData = [];
let dataTable = null;

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    // Establecer fecha actual
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('fechaReporte').value = hoy;
    
    // Cargar reporte
    cargarReporte();
    cargarProductosCriticos();
});

// Cargar reporte
async function cargarReporte() {
    const fecha = document.getElementById('fechaReporte').value;
    
    try {
        mostrarLoading(true);
        
        // Cargar datos del reporte
        const response = await fetch(`/reporte/inventario-vs-pedidos?fecha=${fecha}`);
        if (!response.ok) throw new Error('Error al cargar reporte');
        
        reporteData = await response.json();
        
        // Cargar resumen
        const resumenResponse = await fetch(`/reporte/resumen-inventario?fecha=${fecha}`);
        const resumen = await resumenResponse.json();
        
        // Actualizar estadísticas
        actualizarEstadisticas(resumen);
        
        // Actualizar tabla
        actualizarTabla();
        
        // Actualizar fecha mostrada
        document.getElementById('fechaReporteMostrar').textContent = fecha;
        
        mostrarLoading(false);
        
    } catch (error) {
        console.error('Error al cargar reporte:', error);
        mostrarLoading(false);
        alert('Error al cargar el reporte');
    }
}

// Actualizar estadísticas
function actualizarEstadisticas(resumen) {
    document.getElementById('totalProductos').textContent = resumen.total_productos_vendidos;
    document.getElementById('productosSuficientes').textContent = resumen.productos_con_inventario_suficiente;
    document.getElementById('productosInsuficientes').textContent = resumen.productos_con_inventario_insuficiente;
    document.getElementById('unidadesFaltantes').textContent = resumen.total_unidades_faltantes;
}

// Actualizar tabla
function actualizarTabla() {
    // Destruir tabla existente
    if (dataTable) {
        dataTable.destroy();
    }

    dataTable = $('#reporteTable').DataTable({
        data: reporteData,
        columns: [
            { data: 'codigo_producto' },
            { data: 'nombre_producto' },
            { data: 'marca' },
            { data: 'unidad_medida' },
            { data: 'inventario_actual' },
            { data: 'cantidad_vendida' },
            { 
                data: 'faltante',
                render: function(data) {
                    return data > 0 ? `<span class="badge badge-insufficient">${data}</span>` : '-';
                }
            },
            { 
                data: 'estado',
                render: function(data) {
                    const badgeClass = data === 'INSUFICIENTE' ? 'badge-insufficient' : 'badge-sufficient';
                    return `<span class="badge ${badgeClass}">${data}</span>`;
                }
            }
        ],
        pageLength: 25,
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]],
        language: {
            processing: "Procesando...",
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ a _END_ de _TOTAL_ productos",
            infoEmpty: "Mostrando 0 productos",
            infoFiltered: "(filtrado de _MAX_ productos totales)",
            paginate: {
                first: "Primero",
                last: "Último",
                next: "Siguiente",
                previous: "Anterior"
            },
            zeroRecords: "No se encontraron productos con ventas en esta fecha",
            emptyTable: "No hay datos disponibles"
        },
        order: [[7, 'desc'], [1, 'asc']], // Ordenar por faltante descendente, luego por nombre
        rowCallback: function(row, data) {
            if (data.faltante > 0) {
                $(row).addClass('table-insufficient');
            }
        }
    });
}

// Cargar productos críticos
async function cargarProductosCriticos() {
    try {
        const response = await fetch('/reporte/productos-criticos?limite=10');
        const productos = await response.json();
        
        const container = document.getElementById('productosCriticos');
        
        if (productos.length === 0) {
            container.innerHTML = '<p class="text-success"><i class="fas fa-check-circle"></i> No hay productos con inventario crítico</p>';
            return;
        }
        
        let html = '<div class="row">';
        productos.forEach(producto => {
            const alertClass = producto.nivel_alerta === 'CRITICO' ? 'alert-danger' : 'alert-warning';
            html += `
                <div class="col-md-6 mb-2">
                    <div class="alert ${alertClass} mb-0">
                        <strong>${producto.nombre_producto}</strong> 
                        <span class="badge bg-dark float-end">${producto.existencia} ${producto.medida}</span>
                        <br><small class="text-muted">${producto.marca} - Cod: ${producto.codigo_producto}</small>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error al cargar productos críticos:', error);
    }
}

// Generar PDF
function generarPDF() {
    const fecha = document.getElementById('fechaReporte').value;
    window.open(`/imprimir_reporte_inventario?fecha=${fecha}`, '_blank');
}

// Mostrar/ocultar loading
function mostrarLoading(mostrar) {
    const overlay = document.getElementById('loadingOverlay');
    if (mostrar) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}