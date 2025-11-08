let dataTable;
let usuariosData = [];
let perfilesData = [];

// Cargar datos al iniciar
$(document).ready(function() {
    cargarPerfiles();
    cargarUsuarios();
});

// Cargar perfiles
async function cargarPerfiles() {
    try {
        const response = await fetch('/api/perfiles');
        perfilesData = await response.json();
        
        const select = document.getElementById('codigoPerfil');
        select.innerHTML = '<option value="">Seleccione un perfil...</option>';
        
        perfilesData.forEach(perfil => {
            const option = document.createElement('option');
            option.value = perfil.codigo_perfil;
            option.textContent = perfil.descripcion;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error al cargar perfiles:', error);
    }
}

// Cargar usuarios
async function cargarUsuarios() {
    try {
        const response = await fetch('/api/usuarios');
        usuariosData = await response.json();
        
        // Actualizar estadísticas
        actualizarEstadisticas();
        
        // Inicializar DataTable
        if (dataTable) {
            dataTable.destroy();
        }
        
        dataTable = $('#usuariosTable').DataTable({
            data: usuariosData,
            columns: [
                { data: 'codigo_usuario' },
                { data: 'usuario' },
                { data: 'nombre_usuario' },
                { 
                    data: 'perfil_descripcion',
                    render: function(data, type, row) {
                        let badgeClass = '';
                        switch(row.codigo_perfil) {
                            case 1: badgeClass = 'badge-admin'; break;
                            case 2: badgeClass = 'badge-vendedor'; break;
                            case 3: badgeClass = 'badge-logistica'; break;
                            case 4: badgeClass = 'badge-tecnico'; break;
                            default: badgeClass = 'bg-secondary';
                        }
                        return `<span class="badge ${badgeClass}">${data}</span>`;
                    }
                },
                { 
                    data: 'fecha_registro',
                    render: function(data) {
                        return new Date(data).toLocaleDateString('es-GT');
                    }
                },
                {
                    data: null,
                    render: function(data, type, row) {
                        return `
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-info" onclick="editarUsuario(${row.codigo_usuario})" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-warning" onclick="abrirCambiarClave(${row.codigo_usuario})" title="Cambiar contraseña">
                                    <i class="fas fa-key"></i>
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="eliminarUsuario(${row.codigo_usuario})" title="Eliminar">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json'
            },
            responsive: true,
            order: [[0, 'desc']]
        });
        
    } catch (error) {
        console.error('Error al cargar usuarios:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar los usuarios'
        });
    }
}

// Actualizar estadísticas
function actualizarEstadisticas() {
    const total = usuariosData.length;
    const admins = usuariosData.filter(u => u.codigo_perfil === 1).length;
    const vendedores = usuariosData.filter(u => u.codigo_perfil === 2).length;
    const otros = usuariosData.filter(u => u.codigo_perfil > 2).length;
    
    document.getElementById('totalUsuarios').textContent = total;
    document.getElementById('totalAdmins').textContent = admins;
    document.getElementById('totalVendedores').textContent = vendedores;
    document.getElementById('totalOtros').textContent = otros;
}

// Abrir modal para nuevo usuario
function abrirModalNuevoUsuario() {
    document.getElementById('usuarioModalLabel').textContent = 'Nuevo Usuario';
    document.getElementById('formUsuario').reset();
    document.getElementById('codigoUsuario').value = '';
    document.getElementById('modoEdicion').value = 'false';
    document.getElementById('claveGroup').style.display = 'block';
    document.getElementById('clave').required = true;
    
    const modal = new bootstrap.Modal(document.getElementById('usuarioModal'));
    modal.show();
}

// Editar usuario
function editarUsuario(codigo) {
    const usuario = usuariosData.find(u => u.codigo_usuario === codigo);
    
    if (!usuario) return;
    
    document.getElementById('usuarioModalLabel').textContent = 'Editar Usuario';
    document.getElementById('codigoUsuario').value = usuario.codigo_usuario;
    document.getElementById('usuario').value = usuario.usuario;
    document.getElementById('nombreUsuario').value = usuario.nombre_usuario;
    document.getElementById('codigoPerfil').value = usuario.codigo_perfil;
    document.getElementById('modoEdicion').value = 'true';
    document.getElementById('claveGroup').style.display = 'none';
    document.getElementById('clave').required = false;
    
    const modal = new bootstrap.Modal(document.getElementById('usuarioModal'));
    modal.show();
}

// Guardar usuario
async function guardarUsuario() {
    const form = document.getElementById('formUsuario');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const modoEdicion = document.getElementById('modoEdicion').value === 'true';
    const codigo = document.getElementById('codigoUsuario').value;
    const usuario = document.getElementById('usuario').value.trim();
    const clave = document.getElementById('clave').value;
    const nombreUsuario = document.getElementById('nombreUsuario').value.trim();
    const codigoPerfil = document.getElementById('codigoPerfil').value;
    
    // Validaciones
    if (usuario.length < 4) {
        Swal.fire({
            icon: 'warning',
            title: 'Usuario inválido',
            text: 'El usuario debe tener al menos 4 caracteres'
        });
        return;
    }
    
    if (usuario.includes(' ')) {
        Swal.fire({
            icon: 'warning',
            title: 'Usuario inválido',
            text: 'El usuario no puede contener espacios'
        });
        return;
    }
    
    if (!modoEdicion && clave.length < 6) {
        Swal.fire({
            icon: 'warning',
            title: 'Contraseña inválida',
            text: 'La contraseña debe tener al menos 6 caracteres'
        });
        return;
    }
    
    const data = {
        usuario: usuario,
        nombre_usuario: nombreUsuario,
        codigo_perfil: parseInt(codigoPerfil)
    };
    
    if (!modoEdicion) {
        data.clave = clave;
    }
    
    try {
        const url = modoEdicion ? `/api/usuarios/${codigo}` : '/api/usuarios';
        const method = modoEdicion ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: modoEdicion ? 'Usuario actualizado correctamente' : 'Usuario creado correctamente',
                timer: 2000
            });
            
            bootstrap.Modal.getInstance(document.getElementById('usuarioModal')).hide();
            cargarUsuarios();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: result.detail || 'Error al guardar usuario'
            });
        }
        
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión al guardar usuario'
        });
    }
}

// Eliminar usuario
async function eliminarUsuario(codigo) {
    const usuario = usuariosData.find(u => u.codigo_usuario === codigo);
    
    const result = await Swal.fire({
        title: '¿Eliminar usuario?',
        html: `¿Está seguro de eliminar al usuario <strong>${usuario.usuario}</strong>?<br><small class="text-danger">Esta acción no se puede deshacer</small>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });
    
    if (result.isConfirmed) {
        try {
            const response = await fetch(`/api/usuarios/${codigo}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Eliminado!',
                    text: 'Usuario eliminado correctamente',
                    timer: 2000
                });
                cargarUsuarios();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo eliminar el usuario'
                });
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error de conexión al eliminar usuario'
            });
        }
    }
}

// Abrir modal cambiar contraseña
function abrirCambiarClave(codigo) {
    const usuario = usuariosData.find(u => u.codigo_usuario === codigo);
    
    if (!usuario) return;
    
    document.getElementById('codigoUsuarioClave').value = usuario.codigo_usuario;
    document.getElementById('usuarioClave').value = usuario.usuario;
    document.getElementById('nuevaClave').value = '';
    document.getElementById('confirmarClave').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('cambiarClaveModal'));
    modal.show();
}

// Cambiar contraseña
async function cambiarClave() {
    const codigo = document.getElementById('codigoUsuarioClave').value;
    const nuevaClave = document.getElementById('nuevaClave').value;
    const confirmarClave = document.getElementById('confirmarClave').value;
    
    if (nuevaClave.length < 6) {
        Swal.fire({
            icon: 'warning',
            title: 'Contraseña inválida',
            text: 'La contraseña debe tener al menos 6 caracteres'
        });
        return;
    }
    
    if (nuevaClave !== confirmarClave) {
        Swal.fire({
            icon: 'warning',
            title: 'Las contraseñas no coinciden',
            text: 'Por favor verifique que ambas contraseñas sean iguales'
        });
        return;
    }
    
    try {
        const response = await fetch(`/api/usuarios/${codigo}/cambiar-clave`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ clave: nuevaClave })
        });
        
        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: 'Contraseña actualizada correctamente',
                timer: 2000
            });
            bootstrap.Modal.getInstance(document.getElementById('cambiarClaveModal')).hide();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo cambiar la contraseña'
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión al cambiar contraseña'
        });
    }
}

// Toggle password visibility
function togglePassword() {
    const input = document.getElementById('clave');
    const icon = document.getElementById('togglePasswordIcon');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function toggleNewPassword() {
    const input = document.getElementById('nuevaClave');
    const icon = document.getElementById('toggleNewPasswordIcon');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Toggle sidebar en móvil
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Cerrar sidebar al hacer click fuera
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    }
});