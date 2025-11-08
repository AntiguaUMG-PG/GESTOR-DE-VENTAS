let dataTable;
let marcasData = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando gestión de marcas');
    cargarMarcas();

    // Event listener para el formulario de inserción
    document.getElementById('formInsertar').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const marca = Object.fromEntries(formData);
        
        if (!marca.NOMBRE_MARCA || !marca.NOMBRE_MARCA.trim()) {
            Swal.fire({
                icon: 'warning',
                title: 'Campo requerido',
                text: 'Por favor ingrese el nombre de la marca',
                confirmButtonColor: '#5271ff'
            });
            return;
        }

        await insertarMarca(marca);
    });
});

// Cargar marcas
async function cargarMarcas() {
    try {
        const response = await fetch('/api/marcas/listado');
        
        if (!response.ok) {
            throw new Error('Error al cargar marcas');
        }

        marcasData = await response.json();
        console.log('📦 Marcas cargadas:', marcasData.length);
        
        actualizarEstadisticas();
        inicializarTabla();
        
    } catch (error) {
        console.error('Error al cargar marcas:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar las marcas',
            confirmButtonColor: '#5271ff'
        });
    }
}

// Inicializar DataTable
function inicializarTabla() {
    if (dataTable) {
        dataTable.destroy();
    }

    dataTable = $('#marcasTable').DataTable({
        data: marcasData,
        columns: [
            { data: 'id' },
            { data: 'nombre' },
            { 
                data: 'productos_count',
                render: function(data) {
                    return `<span class="badge bg-primary">${data || 0}</span>`;
                }
            },
            {
                data: null,
                render: function(data, type, row) {
                    return `
                        <div class="table-actions">
                            <button class="btn btn-warning btn-sm" onclick="editarMarca(${row.id}, '${row.nombre}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarMarca(${row.id}, '${row.nombre}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                }
            }
        ],
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json',
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ marcas",
            info: "Mostrando _START_ a _END_ de _TOTAL_ marcas",
            infoEmpty: "No hay marcas disponibles",
            zeroRecords: "No se encontraron marcas"
        },
        pageLength: 10,
        responsive: true,
        order: [[1, 'asc']]
    });
}

// Actualizar estadísticas
function actualizarEstadisticas() {
    const totalMarcas = marcasData.length;
    const totalProductos = marcasData.reduce((sum, marca) => sum + (marca.productos_count || 0), 0);

    document.getElementById('totalMarcas').textContent = totalMarcas;
    document.getElementById('productosAsociados').textContent = totalProductos;
}

// Insertar marca
async function insertarMarca(marcaData) {
    try {
        const response = await fetch('/api/marcas/insertar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(marcaData)
        });

        if (response.ok) {
            const result = await response.json();
            
            // Cerrar modal
            const modalInsertar = bootstrap.Modal.getInstance(document.getElementById('modalInsertar'));
            modalInsertar.hide();
            
            // Limpiar formulario
            document.getElementById('formInsertar').reset();
            
            // Recargar tabla
            await cargarMarcas();
            
            Swal.fire({
                icon: 'success',
                title: 'Éxito',
                text: 'Marca agregada correctamente',
                confirmButtonColor: '#5271ff',
                timer: 2000
            });
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al insertar marca');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo agregar la marca: ' + error.message,
            confirmButtonColor: '#5271ff'
        });
    }
}

// Editar marca
async function editarMarca(id, nombreActual) {
    const { value: nuevoNombre } = await Swal.fire({
        title: 'Editar Marca',
        html: `
            <div class="text-start">
                <label class="form-label">Nombre de la Marca:</label>
                <input id="editNombre" class="form-control" value="${nombreActual}">
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Guardar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#5271ff',
        preConfirm: () => {
            const nombre = document.getElementById('editNombre').value;
            if (!nombre.trim()) {
                Swal.showValidationMessage('El nombre es requerido');
                return false;
            }
            return nombre.trim();
        }
    });

    if (nuevoNombre) {
        try {
            const response = await fetch('/api/marcas/actualizar', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    id: id,
                    NOMBRE_MARCA: nuevoNombre
                })
            });

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: 'Marca actualizada correctamente',
                    confirmButtonColor: '#5271ff',
                    timer: 2000
                });
                cargarMarcas();
            } else {
                throw new Error('Error al actualizar marca');
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo actualizar la marca',
                confirmButtonColor: '#5271ff'
            });
        }
    }
}

// Eliminar marca
async function eliminarMarca(id, nombre) {
    const result = await Swal.fire({
        title: '¿Está seguro?',
        html: `¿Desea eliminar la marca <strong>${nombre}</strong>?<br><br><small class="text-danger">Nota: Solo se pueden eliminar marcas sin productos asociados.</small>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`/api/marcas/eliminar/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok && data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Eliminado',
                    text: 'La marca ha sido eliminada correctamente',
                    confirmButtonColor: '#5271ff',
                    timer: 2000
                });
                cargarMarcas();
            } else {
                throw new Error(data.error || 'Error al eliminar marca');
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message,
                confirmButtonColor: '#5271ff'
            });
        }
    }
}

// Toggle sidebar en móvil
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('show');
}

// Cerrar sidebar al hacer clic fuera
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    }
});