// Toggle del menú en móvil
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

let dataTable;
let productosData = [];

document.addEventListener('DOMContentLoaded', function () {
console.log('🚀 Inicializando página de productos');

// Inicializar DataTable
dataTable = $('#productosTable').DataTable({
    "processing": true,
    "ajax": {
        "url": '/api/productos',  // Corregido: usar el endpoint correcto
        "type": "GET",
        "dataSrc": function(data) {
            console.log('📦 Productos recibidos:', data.length);
            productosData = data;
            actualizarEstadisticas(data);
            return data;
        },
        "error": function(xhr, error, thrown) {
            console.error('Error AJAX:', error, thrown);
            console.error('Response:', xhr.responseText);
            
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'No se pudieron cargar los productos. Verifique la conexión a la base de datos.',
                confirmButtonColor: '#5271ff'
            });
        }
    },
    "columns": [
        { "data": "Codigo" },
        { "data": "Nombre" },
        { "data": "Marca" },
        { 
            "data": "Existencia",
            "render": function(data, type, row) {
                let badgeClass = 'stock-high';
                if (data == 0) badgeClass = 'stock-zero';
                else if (data < 10) badgeClass = 'stock-low';
                else if (data < 50) badgeClass = 'stock-medium';
                
                return `<span class="badge stock-badge ${badgeClass}">${data}</span>`;
            }
        },
        { 
            "data": "Precio",
            "render": function(data) {
                return `Q. ${parseFloat(data || 0).toFixed(2)}`;
            }
        },
        
    ],
    "pageLength": 10,
    "lengthMenu": [[5, 10, 15, 20, 25], [5, 10, 15, 20, 25]],
    "language": {
        "processing": "Cargando productos...",
        "search": "Buscar:",
        "lengthMenu": "Mostrar _MENU_ productos",
        "info": "Mostrando _START_ a _END_ de _TOTAL_ productos",
        "infoEmpty": "No hay productos disponibles",
        "infoFiltered": "(filtrado de _MAX_ productos totales)",
        "paginate": {
            "first": "Primero",
            "last": "Último",
            "next": "→",
            "previous": "←"
        },
        "zeroRecords": "No se encontraron productos",
        "emptyTable": "No hay productos en la base de datos"
    },
    "order": [[1, "asc"]], // Ordenar por nombre
    "responsive": true
});

// Evento de clic en las filas para mostrar detalles
$('#productosTable tbody').on('click', 'tr', function() {
    if ($(this).hasClass('selected')) {
        $(this).removeClass('selected');
        limpiarDetalles();
    } else {
        dataTable.$('tr.selected').removeClass('selected');
        $(this).addClass('selected');
        
        const data = dataTable.row(this).data();
        if (data) {
            mostrarDetallesProducto(data);
        }
    }
});

// Event listener para el formulario de inserción
document.getElementById('formInsertar').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const producto = Object.fromEntries(formData);
    
    // Validar datos
    if (!producto.NOMBRE_PRODUCTO || !producto.UNIDAD_MEDIDA || !producto.MARCA) {
        Swal.fire({
            icon: 'warning',
            title: 'Campos requeridos',
            text: 'Por favor complete todos los campos obligatorios',
            confirmButtonColor: '#5271ff'
        });
        return;
    }

    insertarProducto(producto);
});

// Cargar marcas para el modal
cargarMarcas();
});

// Cargar marcas cuando se abre el modal
document.getElementById('modalInsertar').addEventListener('show.bs.modal', function () {
console.log('Modal abierto, cargando marcas...');
cargarMarcas();
});

async function insertarProducto(productoData) {
try {
    const response = await fetch('/api/productos/insertar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(productoData)
    });

    if (response.ok) {
        const result = await response.json();
        
        // Cerrar modal
        const modalInsertar = bootstrap.Modal.getInstance(document.getElementById('modalInsertar'));
        modalInsertar.hide();
        
        // Limpiar formulario
        document.getElementById('formInsertar').reset();
        
        // Actualizar tabla
        refreshData();
        
        Swal.fire({
            icon: 'success',
            title: 'Éxito',
            text: 'Producto agregado correctamente',
            confirmButtonColor: '#5271ff'
        });
    } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al insertar producto');
    }
} catch (error) {
    console.error('Error:', error);
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'No se pudo agregar el producto: ' + error.message,
        confirmButtonColor: '#5271ff'
    });
}
}

function actualizarEstadisticas(productos) {
const total = productos.length;
const conStock = productos.filter(p => p.Existencia > 0).length;
const stockBajo = productos.filter(p => p.Existencia > 0 && p.Existencia < 20).length;
const sinStock = productos.filter(p => p.Existencia == 0).length;

document.getElementById('totalProductos').textContent = total;
document.getElementById('productosStock').textContent = conStock;
document.getElementById('stockBajo').textContent = stockBajo;
document.getElementById('sinStock').textContent = sinStock;
}

function mostrarDetallesProducto(producto) {
const stockStatus = producto.Existencia == 0 ? 'Sin Stock' : 
                    producto.Existencia < 10 ? 'Stock Bajo' : 
                    producto.Existencia < 50 ? 'Stock Medio' : 'Stock Alto';

const stockClass = producto.Existencia == 0 ? 'danger' : 
                    producto.Existencia < 10 ? 'warning' : 
                    producto.Existencia < 50 ? 'info' : 'success';

document.getElementById('productoDetalles').innerHTML = `
    <div class="card border-0">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <h5 class="card-title mb-0">
                    <i class="fas fa-box text-primary"></i> 
                    ${producto.Nombre}
                </h5>
                <span class="badge bg-${stockClass}">${stockStatus}</span>
            </div>
            
            <div class="row g-3">
                <div class="col-12">
                    <h6 class="text-muted mb-2">Información General</h6>
                    <p class="mb-1"><strong>Código:</strong> ${producto.Codigo}</p>
                    <p class="mb-1"><strong>Presentación:</strong> ${producto.Medida}</p>
                    <p class="mb-1"><strong>Marca:</strong> ${producto.Marca}</p>
                </div>
                
                <div class="col-6">
                    <p class="mb-0"><strong>Stock:</strong> ${producto.Existencia}</p>
                </div>
                
                <div class="col-6">
                    <p class="mb-0"><strong>Precio:</strong> Q. ${parseFloat(producto.Precio).toFixed(2)}</p>
                </div>
            </div>
            
            <div class="d-grid gap-2 d-md-flex justify-content-md-end mt-3">
                <button type="button" class="btn btn-warning btn-sm" onclick="editarProducto(${producto.Codigo})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button type="button" class="btn btn-danger btn-sm" onclick="eliminarProducto(${producto.Codigo}, '${producto.Nombre}')">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
    </div>
`;
}

function limpiarDetalles() {
document.getElementById('productoDetalles').innerHTML = `
    <div class="text-center text-muted py-4">
        <i class="fas fa-mouse-pointer fa-3x mb-3"></i>
        <p>Seleccione un producto de la tabla para ver sus detalles</p>
    </div>
`;
}

async function cargarMarcas() {
try {
const response = await fetch('/api/marcas');
if (response.ok) {
    const marcas = await response.json();
    const select = document.querySelector('select[name="MARCA"]');
    select.innerHTML = '<option value="">Seleccione una marca</option>';
    marcas.forEach(marca => {
        select.innerHTML += `<option value="${marca.id}">${marca.nombre}</option>`;
    });
} else {
    console.error('Error al cargar marcas:', response.status);
}
} catch (error) {
console.error('Error al cargar marcas:', error);
// Fallback con marcas básicas
const select = document.querySelector('select[name="MARCA"]');
select.innerHTML = `
    <option value="">Seleccione una marca</option>
    <option value="1">ADAMS</option>
    <option value="2">BEST</option>
    <option value="3">MARINELA</option>
    <option value="4">BIMBO</option>
    <option value="59">SIN MARCA</option>
`;
}
}

function refreshData() {
console.log('Actualizando datos...');
dataTable.ajax.reload();
limpiarDetalles();
}

function editarProducto(codigo) {
const producto = productosData.find(p => p.Codigo == codigo);
if (!producto) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'Producto no encontrado',
        confirmButtonColor: '#5271ff'
    });
    return;
}

Swal.fire({
    title: 'Editar Producto',
    html: `
        <div class="text-start">
            <div class="mb-3">
                <label class="form-label">Nombre:</label>
                <input id="editNombre" class="form-control" value="${producto.Nombre}">
            </div>
            <div class="mb-3">
                <label class="form-label">Presentacion:</label>
                <input id="editMedida" class="form-control" value="${producto.Medida}">
            </div>
            <div class="mb-3">
                <label class="form-label">Stock:</label>
                <input id="editStock" type="number" class="form-control" value="${producto.Existencia}" min="0">
            </div>
            <div class="mb-3">
                <label class="form-label">Precio:</label>
                <input id="editPrecio" type="number" step="0.01" class="form-control" value="${producto.Precio}" min="0">
            </div>
        </div>
    `,
    showCancelButton: true,
    confirmButtonText: 'Guardar',
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#5271ff',
    preConfirm: () => {
        const nombre = document.getElementById('editNombre').value;
        const stock = document.getElementById('editStock').value;
        const medida = document.getElementById('editMedida').value;
        const precio = document.getElementById('editPrecio').value;

        if (!nombre.trim()) {
            Swal.showValidationMessage('El nombre es requerido');
            return false;
        }

        return {
            Codigo: codigo,
            NOMBRE_PRODUCTO: nombre.trim(),
            EXISTENCIA: parseFloat(stock) || 0,
            UNIDAD_MEDIDA: medida,
            PRECIO: parseFloat(precio) || 0
        };
    }
}).then((result) => {
    if (result.isConfirmed) {
        actualizarProducto(result.value);
    }
});
}

async function actualizarProducto(datosProducto) {
try {
    const response = await fetch('/api/productos/actualizar', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(datosProducto)
    });

    if (response.ok) {
        Swal.fire({
            icon: 'success',
            title: 'Éxito',
            text: 'Producto actualizado correctamente',
            confirmButtonColor: '#5271ff'
        });
        refreshData();
    } else {
        throw new Error('Error al actualizar producto');
    }
} catch (error) {
    console.error('Error:', error);
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'No se pudo actualizar el producto',
        confirmButtonColor: '#5271ff'
    });
}
}

function eliminarProducto(codigo, nombre) {
Swal.fire({
    title: '¿Está seguro?',
    text: `¿Desea eliminar el producto "${nombre}"?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#5271ff',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar'
}).then(async (result) => {
    if (result.isConfirmed) {
        try {
            const response = await fetch(`/api/productos/${codigo}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'Eliminado',
                    text: 'Producto eliminado correctamente',
                    confirmButtonColor: '#5271ff'
                });
                refreshData();
                limpiarDetalles();
            } else {
                throw new Error('Error al eliminar producto');
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo eliminar el producto',
                confirmButtonColor: '#5271ff'
            });
        }
    }
});
}

function toggleSubmenu(submenuId, chevronId) {
    const submenu = document.getElementById(submenuId);
    const chevron = document.getElementById(chevronId);
    
    submenu.classList.toggle('active');
    chevron.classList.toggle('active');
} 

// Configuración común para las gráficas
const chartConfig = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'right',
            labels: {
                boxWidth: 12,
                font: {
                    size: 11
                }
            }
        }
    }
};



// Función para cargar los datos
async function cargarDatos() {
    try {
        // Cargar totales
        const totalesResponse = await fetch('/api/dashboard/totales');
        const totales = await totalesResponse.json();
        
        document.getElementById('totalClientes').textContent = totales.clientes;
        document.getElementById('totalPedidos').textContent = totales.pedidos;
        document.getElementById('totalProductos').textContent = totales.productos;

        // Gráfica de Clientes
        const clientesResponse = await fetch('/api/dashboard/clientes-por-departamento');
        const clientesData = await clientesResponse.json();
        
        new Chart(document.getElementById('clientesChart'), {
            type: 'pie',
            data: {
                labels: clientesData.map(d => d.departamento),
                datasets: [{
                    data: clientesData.map(d => d.total),
                    backgroundColor: [
                        '#4F46E5', '#7C3AED', '#EC4899', '#F59E0B', '#10B981'
                    ]
                }]
            },
            options: {
                ...chartConfig,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            font: { size: 11 }
                        }
                    }
                }
            }
        });

        // Gráfica de Productos
        const productosResponse = await fetch('/api/dashboard/productos-por-marca');
        const productosData = await productosResponse.json();
        
        new Chart(document.getElementById('productosChart'), {
            type: 'bar',
            data: {
                labels: productosData.map(d => d.marca),
                datasets: [{
                    label: 'Productos',
                    data: productosData.map(d => d.total),
                    backgroundColor: 'rgba(79, 70, 229, 0.8)'
                }]
            },
            options: {
                ...chartConfig,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    x: {
                        ticks: {
                            font: { size: 11 }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error al cargar los datos:', error);
    }
}

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', cargarDatos);

// Ajustar tamaño de gráficas cuando se redimensiona la ventana
window.addEventListener('resize', function() {
    const charts = document.querySelectorAll('canvas');
    charts.forEach(chart => {
        if (chart.chart) {
            chart.chart.resize();
        }
    });
});