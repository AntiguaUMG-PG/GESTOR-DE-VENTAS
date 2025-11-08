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

// Variables globales
let dataTable;
let clientesData = [];
let municipiosData = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Inicializando página de clientes...');
    
    // Cargar datos iniciales
    cargarClientes();
    cargarDropdowns();
    
    // Configurar event listeners para formularios
    setupFormularios();
});

// Función principal para cargar clientes
async function cargarClientes() {
    console.log('📊 Cargando clientes desde la API...');
    
    try {
        mostrarLoading(true);
        
        const response = await fetch('/listado_clientes');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        clientesData = await response.json();
        console.log(`✅ Clientes cargados: ${clientesData.length} registros`);
        
        // Actualizar estadísticas
        actualizarEstadisticas();
        
        // Inicializar DataTable
        inicializarDataTable();
        
        mostrarLoading(false);
        
    } catch (error) {
        console.error('❌ Error al cargar clientes:', error);
        mostrarError(true);
        mostrarLoading(false);
    }
}

// Inicializar DataTable
function inicializarDataTable() {
    // Destruir tabla existente si existe
    if (dataTable) {
        dataTable.destroy();
    }

    dataTable = $('#clientesTable').DataTable({
        data: clientesData,
        columns: [
            { data: 'Codigo' },
            { data: 'Nombre' },
            { data: 'Nombre_Negocio' },
            { data: 'NIT' },
            { data: 'Telefono' },
            { data: 'Municipio' },
            { data: 'Departamento' },
            { 
                data: 'Saldo',
                render: function(data) {
                    return `Q. ${parseFloat(data || 0).toFixed(2)}`;
                }
            }
        ],
        pageLength: 10,
        lengthMenu: [[5, 10, 25, 50], [5, 10, 25, 50]],
        language: {
            processing: "Procesando...",
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ a _END_ de _TOTAL_ clientes",
            infoEmpty: "Mostrando 0 a 0 de 0 clientes",
            infoFiltered: "(filtrado de _MAX_ clientes totales)",
            paginate: {
                first: "Primero",
                last: "Último",
                next: "Siguiente",
                previous: "Anterior"
            },
            zeroRecords: "No se encontraron clientes",
            emptyTable: "No hay clientes disponibles"
        },
        order: [[1, 'asc']], // Ordenar por nombre
        responsive: true,
        dom: '<"row"<"col-sm-6"l><"col-sm-6"f>>rt<"row"<"col-sm-6"i><"col-sm-6"p>>',
    });

    // Event listener para seleccionar fila
    $('#clientesTable tbody').on('click', 'tr', function() {
        const data = dataTable.row(this).data();
        if (data) {
            mostrarDetallesCliente(data);
            // Resaltar fila seleccionada
            $('#clientesTable tbody tr').removeClass('table-active');
            $(this).addClass('table-active');
        }
    });

    // Mostrar la tabla
    document.getElementById('clientesTableContainer').style.display = 'block';
}

// Mostrar/ocultar loading
function mostrarLoading(mostrar) {
    const spinner = document.getElementById('loadingSpinner');
    const tabla = document.getElementById('clientesTableContainer');
    
    if (mostrar) {
        spinner.style.display = 'flex';
        tabla.style.display = 'none';
    } else {
        spinner.style.display = 'none';
    }
}

// Mostrar/ocultar error
function mostrarError(mostrar) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.style.display = mostrar ? 'block' : 'none';
}

// Recargar clientes
function recargarClientes() {
    mostrarError(false);
    cargarClientes();
}

// Actualizar estadísticas
function actualizarEstadisticas() {
    const total = clientesData.length;
    const activos = clientesData.filter(c => c.Saldo >= 0).length;
    
    document.getElementById('totalClientes').textContent = total;
    document.getElementById('clientesActivos').textContent = activos;
}

// Mostrar detalles del cliente
function mostrarDetallesCliente(cliente) {
    const detalleDiv = document.getElementById('clienteDetalle');
    const saldo = parseFloat(cliente.Saldo || 0);
    const saldoColor = saldo >= 0 ? 'success' : 'danger';
    
    detalleDiv.innerHTML = `
        <div class="text-center mb-3">
            <i class="fas fa-user-circle fa-3x text-primary mb-2"></i>
            <h5 class="card-title">${cliente.Nombre}</h5>
            <p class="text-muted">${cliente.Nombre_Negocio}</p>
        </div>
        
        <div class="border-top pt-3">
            <div class="row mb-2">
                <div class="col-4 text-muted">Teléfono:</div>
                <div class="col-8">${cliente.Telefono || 'N/A'}</div>
            </div>
            <div class="row mb-2">
                <div class="col-4 text-muted">Dirección:</div>
                <div class="col-8">${cliente.Direccion || 'N/A'}</div>
            </div>
            <div class="row mb-2">
                <div class="col-4 text-muted">Municipio:</div>
                <div class="col-8">${cliente.Municipio || 'N/A'}</div>
            </div>
            <div class="row mb-2">
                <div class="col-4 text-muted">Departamento:</div>
                <div class="col-8">${cliente.Departamento || 'N/A'}</div>
            </div>
            <div class="row mb-2">
                <div class="col-4 text-muted">Nivel Precio:</div>
                <div class="col-8">${cliente.Nivel_Precio || 'N/A'}</div>
            </div>
            <div class="row mb-3">
                <div class="col-4 text-muted">Saldo:</div>
                <div class="col-8">
                    <span class="badge bg-${saldoColor}">Q. ${saldo.toFixed(2)}</span>
                </div>
            </div>
        </div>
        
        <div class="border-top pt-3">
            <div class="d-grid gap-2">
                <button type="button" class="btn btn-warning btn-sm" onclick="editarCliente(${JSON.stringify(cliente).replace(/"/g, '&quot;')})">
                    <i class="fas fa-edit"></i> Editar Cliente
                </button>
                <button type="button" class="btn btn-danger btn-sm" onclick="eliminarCliente(${cliente.Codigo}, '${cliente.Nombre}')">
                    <i class="fas fa-trash"></i> Eliminar Cliente
                </button>
            </div>
        </div>
    `;
}

// Cargar dropdowns
async function cargarDropdowns() {
    console.log('🔽 Cargando catálogos...');
    
    try {
        // Cargar municipios
        const municipiosResponse = await fetch('/listado_municipios');
        const municipios = await municipiosResponse.json();
        municipiosData = municipios; // Guardar en variable global
        
        // Cargar departamentos
        const departamentosResponse = await fetch('/listado_departamentos');
        const departamentos = await departamentosResponse.json();
        
        // Cargar niveles de precio
        const nivelesResponse = await fetch('/listado_niveles_precio');
        const niveles = await nivelesResponse.json();
        
        // Llenar dropdowns
        llenarDropdowns(municipios, departamentos, niveles);
        
        //Configurar los event listeners para el filtrado
        configurarFiltroMunicipios();
        
        console.log('✅ Catálogos cargados');
        
    } catch (error) {
        console.error('❌ Error al cargar catálogos:', error);
    }
}

// Llenar dropdowns con datos
function llenarDropdowns(municipios, departamentos, niveles) {
    // Municipios
    const municipioSelects = document.querySelectorAll('select[name="Municipio"]');
    municipioSelects.forEach(select => {
        select.innerHTML = '<option value="">Seleccione un municipio</option>';
        municipios.forEach(municipio => {
            select.innerHTML += `<option value="${municipio.id}">${municipio.nombre}</option>`;
        });
    });

    // Departamentos
    const departamentoSelects = document.querySelectorAll('select[name="Departamento"]');
    departamentoSelects.forEach(select => {
        select.innerHTML = '<option value="">Seleccione un departamento</option>';
        departamentos.forEach(departamento => {
            select.innerHTML += `<option value="${departamento.id}">${departamento.nombre}</option>`;
        });
    });

    // Niveles de precio
    const nivelSelects = document.querySelectorAll('select[name="Nivel_Precio"]');
    nivelSelects.forEach(select => {
        select.innerHTML = '<option value="">Seleccione un nivel de precio</option>';
        niveles.forEach(nivel => {
            select.innerHTML += `<option value="${nivel.id}">${nivel.nombre}</option>`;
        });
    });
}

// Configurar filtrado de municipios
function configurarFiltroMunicipios() {
    console.log('⚙️ Configurando filtro de municipios...');
    
    // Para el formulario de INSERTAR
    const deptInsertarSelect = document.querySelector('#formInsertar select[name="Departamento"]');
    const munInsertarSelect = document.querySelector('#formInsertar select[name="Municipio"]');
    
    if (deptInsertarSelect && munInsertarSelect) {
        // Deshabilitar municipio inicialmente
        munInsertarSelect.disabled = true;
        munInsertarSelect.innerHTML = '<option value="">Primero seleccione un departamento</option>';
        
        // Event listener para cambio de departamento
        deptInsertarSelect.addEventListener('change', function() {
            const departamentoId = this.value;
            
            if (departamentoId) {
                filtrarMunicipiosPorDepartamento(departamentoId, munInsertarSelect);
                munInsertarSelect.disabled = false;
            } else {
                munInsertarSelect.innerHTML = '<option value="">Primero seleccione un departamento</option>';
                munInsertarSelect.disabled = true;
            }
        });
    }
    
    // Para el formulario de EDITAR
    const deptEditarSelect = document.querySelector('#formEditar select[name="Departamento"]');
    const munEditarSelect = document.querySelector('#formEditar select[name="Municipio"]');
    
    if (deptEditarSelect && munEditarSelect) {
        // Event listener para cambio de departamento
        deptEditarSelect.addEventListener('change', function() {
            const departamentoId = this.value;
            
            if (departamentoId) {
                filtrarMunicipiosPorDepartamento(departamentoId, munEditarSelect);
                munEditarSelect.disabled = false;
            } else {
                munEditarSelect.innerHTML = '<option value="">Primero seleccione un departamento</option>';
                munEditarSelect.disabled = true;
            }
        });
    }
    
    console.log('✅ Filtro de municipios configurado');
}

// Filtrar municipios por departamento
async function filtrarMunicipiosPorDepartamento(departamentoId, selectElement) {
    console.log('🔍 Filtrando municipios para departamento:', departamentoId);
    
    try {
        // Intentar usar el endpoint específico de filtrado
        const response = await fetch(`/listado_municipios_por_departamento/${departamentoId}`);
        
        if (response.ok) {
            const municipiosFiltrados = await response.json();
            llenarSelectMunicipios(municipiosFiltrados, selectElement);
            console.log(`✅ ${municipiosFiltrados.length} municipios filtrados`);
        } else {
            // Fallback: filtrar localmente si el endpoint falla
            console.log('⚠️ Usando filtrado local de municipios');
            const municipiosFiltrados = todosLosMunicipios.filter(
                m => m.departamento_id == departamentoId
            );
            llenarSelectMunicipios(municipiosFiltrados, selectElement);
        }
    } catch (error) {
        console.error('❌ Error al filtrar municipios:', error);
        // Fallback: filtrar localmente
        const municipiosFiltrados = todosLosMunicipios.filter(
            m => m.departamento_id == departamentoId
        );
        llenarSelectMunicipios(municipiosFiltrados, selectElement);
    }
}

// Llenar select de municipios
function llenarSelectMunicipios(municipios, selectElement) {
    selectElement.innerHTML = '<option value="">Seleccione un municipio</option>';
    municipios.forEach(municipio => {
        selectElement.innerHTML += `<option value="${municipio.id}">${municipio.nombre}</option>`;
    });
}

// Configurar formularios
function setupFormularios() {
    // Formulario de inserción
    document.getElementById('formInsertar').addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('📝 Insertando nuevo cliente...');
        
        const formData = new FormData(this);
        const clienteData = Object.fromEntries(formData);
        
        try {
            const response = await fetch('/insertar_cliente', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(clienteData)
            });

            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }

            const result = await response.json();
            
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalInsertar'));
            modal.hide();
            
            // Limpiar formulario
            this.reset();
            
            // Recargar datos
            await cargarClientes();
            
            // Mostrar mensaje de éxito
            Swal.fire({
                icon: 'success',
                title: 'Cliente Agregado',
                text: 'El cliente se ha agregado exitosamente',
                confirmButtonColor: 'var(--primary-blue)'
            });
            
        } catch (error) {
            console.error('❌ Error al insertar cliente:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo agregar el cliente',
                confirmButtonColor: 'var(--primary-blue)'
            });
        }
    });

    // Formulario de edición
    document.getElementById('formEditar').addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('✏️ Actualizando cliente...');
        
        const formData = new FormData(this);
        const clienteData = Object.fromEntries(formData);
        
        try {
            const response = await fetch('/actualizar_cliente', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(clienteData)
            });

            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }

            const result = await response.json();
            
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditar'));
            modal.hide();
            
            // Recargar datos
            await cargarClientes();
            
            // Limpiar panel de detalles
            document.getElementById('clienteDetalle').innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-mouse-pointer fa-3x mb-3"></i>
                    <p>Selecciona un cliente de la lista para ver sus detalles</p>
                </div>
            `;
            
            // Mostrar mensaje de éxito
            Swal.fire({
                icon: 'success',
                title: 'Cliente Actualizado',
                text: 'Los datos del cliente se han actualizado exitosamente',
                confirmButtonColor: 'var(--primary-blue)'
            });
            
        } catch (error) {
            console.error('❌ Error al actualizar cliente:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo actualizar el cliente',
                confirmButtonColor: 'var(--primary-blue)'
            });
        }
    });
}

// Editar cliente
function editarCliente(cliente) {
    console.log('✏️ Editando cliente:', cliente.Codigo);
    
    const form = document.getElementById('formEditar');
    
    // Llenar campos básicos del formulario
    Object.keys(cliente).forEach(key => {
        const input = form.elements[key];
        if (input && input.tagName !== 'SELECT') {
            input.value = cliente[key] || '';
        }
    });
    
    // Manejar selectores especiales con async
    setTimeout(async () => {
        // Buscar IDs de departamento y nivel de precio
        const departamentos = Array.from(form.elements['Departamento'].options);
        const niveles = Array.from(form.elements['Nivel_Precio'].options);
        
        // Seleccionar departamento por nombre
        const deptOption = departamentos.find(opt => opt.text === cliente.Departamento);
        if (deptOption) {
            form.elements['Departamento'].value = deptOption.value;
            
            // Cargar municipios del departamento seleccionado
            const munSelect = form.elements['Municipio'];
            await filtrarMunicipiosPorDepartamento(deptOption.value, munSelect);
            
            // Después de cargar los municipios, seleccionar el correcto
            setTimeout(() => {
                const municipios = Array.from(munSelect.options);
                const munOption = municipios.find(opt => opt.text === cliente.Municipio);
                if (munOption) {
                    munSelect.value = munOption.value;
                }
            }, 100);
        }
        
        // Seleccionar nivel de precio por nombre
        const nivelOption = niveles.find(opt => opt.text === cliente.Nivel_Precio);
        if (nivelOption) {
            form.elements['Nivel_Precio'].value = nivelOption.value;
        }
    }, 100);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalEditar'));
    modal.show();
}

// Eliminar cliente
function eliminarCliente(codigo, nombre) {
    console.log('🗑️ Eliminando cliente:', codigo);
    
    Swal.fire({
        title: '¿Está seguro?',
        text: `¿Desea eliminar el cliente "${nombre}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const response = await fetch(`/eliminar_cliente/${codigo}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }

                const result = await response.json();
                
                // Recargar datos
                await cargarClientes();
                
                // Limpiar panel de detalles
                document.getElementById('clienteDetalle').innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-mouse-pointer fa-3x mb-3"></i>
                        <p>Selecciona un cliente de la lista para ver sus detalles</p>
                    </div>
                `;
                
                // Mostrar mensaje de éxito
                Swal.fire({
                    icon: 'success',
                    title: 'Cliente Eliminado',
                    text: 'El cliente se ha eliminado exitosamente',
                    confirmButtonColor: 'var(--primary-blue)'
                });
                
            } catch (error) {
                console.error('❌ Error al eliminar cliente:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo eliminar el cliente',
                    confirmButtonColor: 'var(--primary-blue)'
                });
            }
        }
    });
}

// Función para toggle de submenús
function toggleSubmenu(submenuId, chevronId) {
    const submenu = document.getElementById(submenuId);
    const chevron = document.getElementById(chevronId);
    submenu.classList.toggle('active');
    chevron.classList.toggle('active');
}

// Recargar página completa
function recargarPagina() {
    window.location.reload();
}

// Exportar a CSV (función adicional)
function exportarCSV() {
    if (clientesData.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Sin Datos',
            text: 'No hay clientes para exportar',
            confirmButtonColor: 'var(--primary-blue)'
        });
        return;
    }

    const csv = convertirACSV(clientesData);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `clientes_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Convertir datos a CSV
function convertirACSV(data) {
    const headers = ['Código', 'Nombre', 'Negocio', 'NIT', 'Teléfono', 'Dirección', 'Municipio', 'Departamento', 'Saldo'];
    const rows = data.map(cliente => [
        cliente.Codigo,
        cliente.Nombre,
        cliente.Nombre_Negocio,
        cliente.NIT,
        cliente.Telefono,
        cliente.Direccion,
        cliente.Municipio,
        cliente.Departamento,
        cliente.Saldo
    ]);

    return [headers, ...rows].map(row => 
        row.map(field => `"${field || ''}"`).join(',')
    ).join('\n');
}