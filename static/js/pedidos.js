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

function toggleSubmenu(submenuId, chevronId) {
    const submenu = document.getElementById(submenuId);
    const chevron = document.getElementById(chevronId);
    
    submenu.classList.toggle('active');
    chevron.classList.toggle('active');
} 

jQuery.noConflict(); // Activa el modo no conflicto


(function($) { 
$(document).ready(function() {
    const clientesModal = document.getElementById('clientesModal')
    clientesModal.addEventListener('show.bs.modal', function () {
        $.ajax({
            url: '/listado_clientes',
            method: 'GET',
            success: function(data) {
                var clientesTable = $('#clientesTable tbody');
                clientesTable.empty();
                data.forEach(function(cliente) {
                    var row = '<tr>' +
                        '<td>' + cliente.Codigo + '</td>' +
                        '<td>' + cliente.Nombre + '</td>' +
                        '<td>' + cliente.Nombre_Negocio + '</td>' +
                        '<td>' + cliente.NIT + '</td>' +
                        '<td>' + cliente.Direccion + '</td>' +
                        '<td>' + cliente.Municipio + '</td>' +
                        '<td><button type="button" class="btn btn-primary seleccionar-cliente" data-bs-dismiss="modal" data-codigo="' + cliente.Codigo + '" data-nombre="' + cliente.Nombre + '" data-nombre_negocio="' + cliente.Nombre_Negocio + '" data-nit="' + cliente.NIT + '" data-direccion="' + cliente.Direccion + '" data-municipio="' + cliente.Municipio + '">Seleccionar</button></td>' +
                        '</tr>';
                    clientesTable.append(row);
                });
            },
            error: function() {
                alert('Error al cargar los clientes');
            }
        });
    });


    // Evento para seleccionar un cliente y llenar los campos del formulario
    $(document).on('click', '.seleccionar-cliente', function() {
        var codigo = $(this).data('codigo');
        var nombre = $(this).data('nombre');
        var nombreNegocio = $(this).data('nombre_negocio');
        var nit = $(this).data('nit');
        var direccion = $(this).data('direccion');
        var municipio = $(this).data('municipio');

        $('#codigoCliente').val(codigo);
        $('#nombreCliente').val(nombre);
        $('#nombreNegocio').val(nombreNegocio);
        $('#nitCliente').val(nit);
        $('#direccionCliente').val(direccion);
        $('#municipioCliente').val(municipio);

        $('#clientesModal').modal('hide');
    });

    // Evento para buscar clientes en la tabla
    $('#buscarCliente').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('#clientesTable tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
});
})(jQuery);




// Script para el modal de pedidos
jQuery.noConflict(); // Activa el modo no conflicto

(function($) { 
    $(document).ready(function() {
        const pedidosModal = document.getElementById('pedidosModal')
        
        // Función para cargar pedidos con filtros opcionales
        function cargarPedidos(fechaInicio = '', fechaFin = '') {
            // Construir URL con parámetros
            let url = '/listado_pedidos';
            let params = [];
            
            if (fechaInicio) {
                params.push('fecha_inicio=' + fechaInicio);
            }
            if (fechaFin) {
                params.push('fecha_fin=' + fechaFin);
            }
            
            if (params.length > 0) {
                url += '?' + params.join('&');
            }
            
            $.ajax({
                url: url,
                method: 'GET',
                success: function(data) {
                    console.log('Datos recibidos:', data);
                    
                    // Destruir DataTable si existe
                    if ($.fn.DataTable.isDataTable('#pedidosTable')) {
                        $('#pedidosTable').DataTable().destroy();
                    }
                    
                    var pedidosTable = $('#pedidosTable tbody');
                    pedidosTable.empty();
                    
                    if (!data || data.length === 0) {
                        pedidosTable.append('<tr><td colspan="8" class="text-center">No hay pedidos en el rango de fechas seleccionado</td></tr>');
                        return;
                    }
                    
                    data.forEach(function(pedido) {
                        try {
                            let fecha = 'N/A';
                            if (pedido.FECHA) {
                                try {
                                    fecha = new Date(pedido.FECHA).toLocaleDateString('es-GT', {
                                        year: 'numeric',
                                        month: '2-digit',
                                        day: '2-digit'
                                    });
                                } catch (e) {
                                    console.error('Error al formatear fecha:', e);
                                    fecha = pedido.FECHA;
                                }
                            }
                            
                            let total = '0.00';
                            try {
                                total = parseFloat(pedido.TOTAL_DOCUMENTO || 0).toFixed(2);
                            } catch (e) {
                                console.error('Error al formatear total:', e);
                            }
                            
                            var row = '<tr>' +
                                '<td>' + (pedido.NUMERO_PEDIDO || 'N/A') + '</td>' +
                                '<td>' + fecha + '</td>' +
                                '<td>' + (pedido.NOMBRE_CLIENTE || 'N/A') + '</td>' +
                                '<td>' + (pedido.NIT || 'N/A') + '</td>' +
                                '<td>' + (pedido.DIRECCION || 'N/A') + '</td>' +
                                '<td>Q. ' + total + '</td>' +
                                '<td>' + (pedido.ESTADO || 'N/A') + '</td>' +
                                '<td>' +
                                '<button type="button" class="btn btn-info btn-sm ver-detalle" ' +
                                'data-pedido="' + pedido.NUMERO_PEDIDO + '">' +
                                '<i class="fas fa-eye"></i></button> ' +
                                '<button type="button" class="btn btn-warning btn-sm editar-pedido" ' +
                                'data-pedido="' + pedido.NUMERO_PEDIDO + '" data-bs-dismiss="modal">' +
                                '<i class="fas fa-edit"></i></button> ' +
                                '<button type="button" class="btn btn-success btn-sm imprimir-pedido" ' +
                                'data-pedido="' + pedido.NUMERO_PEDIDO + '">' +
                                '<i class="fas fa-print"></i></button>' +
                                '</td>' +
                                '</tr>';
                            pedidosTable.append(row);
                        } catch (error) {
                            console.error('Error al procesar pedido:', pedido, error);
                        }
                    });

                    // Inicializar DataTable
                    $('#pedidosTable').DataTable({
                        language: {
                            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json'
                        },
                        order: [[0, 'desc']],
                        pageLength: 10,
                        responsive: true
                    });
                },
                error: function(xhr, status, error) {
                    console.error('Error en AJAX:', {xhr, status, error});
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error al cargar los pedidos: ' + error,
                        confirmButtonColor: '#5271ff'
                    });
                }
            });
        }

        // Cargar pedidos al abrir el modal
        pedidosModal.addEventListener('show.bs.modal', function () {
            // Establecer fecha de hoy por defecto
            const hoy = new Date().toISOString().split('T')[0];
            $('#fechaInicio').val(hoy);
            $('#fechaFin').val(hoy);
            
            // Cargar pedidos del día
            cargarPedidos(hoy, hoy);
        });

        // Evento del botón buscar
        $('#buscarPedidos').on('click', function() {
            const fechaInicio = $('#fechaInicio').val();
            const fechaFin = $('#fechaFin').val();
            
            if (fechaInicio && fechaFin && fechaInicio > fechaFin) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Fechas inválidas',
                    text: 'La fecha de inicio no puede ser mayor a la fecha fin',
                    confirmButtonColor: '#5271ff'
                });
                return;
            }
            
            cargarPedidos(fechaInicio, fechaFin);
        });

        // Evento para ver detalles del pedido
        $(document).on('click', '.ver-detalle', function() {
            var numeroPedido = $(this).data('pedido');
            
            $.ajax({
                url: '/detalle_pedido/' + numeroPedido,
                method: 'GET',
                success: function(data) {
                    let detalleHtml = '<table class="table">' +
                        '<thead><tr>' +
                        '<th>Producto</th>' +
                        '<th>Cantidad</th>' +
                        '<th>Precio Unit.</th>' +
                        '<th>Total</th>' +
                        '</tr></thead><tbody>';
                    
                    data.forEach(function(detalle) {
                        detalleHtml += '<tr>' +
                            '<td>' + detalle.NOMBRE_PRODUCTO + '</td>' +
                            '<td>' + detalle.CANTIDAD + '</td>' +
                            '<td>Q. ' + parseFloat(detalle.PRECIO_UNITARIO).toFixed(2) + '</td>' +
                            '<td>Q. ' + parseFloat(detalle.TOTAL_LINEA).toFixed(2) + '</td>' +
                            '</tr>';
                    });
                    
                    detalleHtml += '</tbody></table>';
                    
                    Swal.fire({
                        title: 'Detalle del Pedido #' + numeroPedido,
                        html: detalleHtml,
                        width: '800px',
                        confirmButtonColor: '#5271ff'
                    });
                },
                error: function() {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error al cargar los detalles del pedido',
                        confirmButtonColor: '#5271ff'
                    });
                }
            });
        });

        // Evento para editar pedido
        $(document).on('click', '.editar-pedido', function() {
            var numeroPedido = $(this).data('pedido');
            
            $.ajax({
                url: '/obtener_pedido_completo/' + numeroPedido,
                method: 'GET',
                success: function(data) {
                    // Cargar datos del encabezado
                    $('#numeroPedido').text(data.encabezado.NUMERO_PEDIDO);
                    $('#codigoCliente').val(data.encabezado.CODIGO_CLIENTE);
                    $('#nombreCliente').val(data.encabezado.NOMBRE_CLIENTE);
                    $('#nombreNegocio').val(data.encabezado.NOMBRE_NEGOCIO || '');
                    $('#nitCliente').val(data.encabezado.NIT);
                    $('#direccionCliente').val(data.encabezado.DIRECCION);
                    $('#municipioCliente').val(data.encabezado.MUNICIPIO || '');
                    $('#comentarios').val(data.encabezado.COMENTARIOS || '');
                    
                    // Limpiar tabla de detalles
                    $('#detalleOrden tbody').empty();
                    
                    // Cargar productos del pedido
                    data.detalle.forEach(function(item) {
                        var newRow = `<tr>
                            <td>${item.CODIGO_PRODUCTO}</td>
                            <td>${item.NOMBRE_PRODUCTO}</td>
                            <td>${item.UNIDAD_MEDIDA}</td>
                            <td contenteditable="true">${item.CANTIDAD}</td>
                            <td contenteditable="true">${parseFloat(item.PRECIO_UNITARIO).toFixed(2)}</td>
                            <td>${parseFloat(item.TOTAL_LINEA).toFixed(2)}</td>
                            <td>
                                <button type="button" class="btn btn-danger btn-sm eliminarProducto">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>`;
                        $('#detalleOrden tbody').append(newRow);
                    });
                    
                    actualizarTotalGeneral();
                    
                    // Cambiar el botón de registrar por actualizar
                    $('#registrarPedido').hide();
                    $('#actualizarPedido').show();
                    $('#cancelarEdicion').show();
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'Pedido Cargado',
                        text: 'Puede modificar los datos del pedido',
                        confirmButtonColor: '#5271ff',
                        timer: 1000
                    });
                },
                error: function() {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error al cargar el pedido',
                        confirmButtonColor: '#5271ff'
                    });
                }
            });
        });

        // Evento para imprimir pedido
        $(document).on('click', '.imprimir-pedido', function() {
            var numeroPedido = $(this).data('pedido');
            window.open('/imprimir_pedido/' + numeroPedido, '_blank');
        });

        // Evento para buscar pedidos en la tabla
        $('#buscarPedido').on('keyup', function() {
            var value = $(this).val().toLowerCase();
            $('#pedidosTable tbody tr').filter(function() {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
            });
        });
    });
})(jQuery);



jQuery.noConflict(); // Activa el modo no conflicto  

async function obtenerNumeroPedido() {
    try {
        const response = await fetch('/numero_pedido');
        if (!response.ok) {
            console.error('Error en la respuesta:', response.statusText);
            return;
        }
        const data = await response.json();
        if (data.ultimo_numero_pedido) {
            document.getElementById('numeroPedido').innerText = data.ultimo_numero_pedido;
        }
    } catch (error) {
        console.error('Error al obtener el número de pedido:', error);
    }
}

function formatearFecha(fechaString) {
    const partes = fechaString.split('/');
    return `${partes[2]}-${partes[1]}-${partes[0]}`;
}

async function imprimirPedidosDelDia() {
    try {
        // Obtener la fecha actual en formato YYYY-MM-DD
        const ahora = new Date();
        const offsetGuatemala = -6; // Guatemala es GMT-6
        const fechaGuatemala = new Date(ahora.getTime() + (offsetGuatemala * 60 * 60 * 1000) + (ahora.getTimezoneOffset() * 60 * 1000));
        
        const anio = fechaGuatemala.getFullYear();
        const mes = String(fechaGuatemala.getMonth() + 1).padStart(2, '0');
        const dia = String(fechaGuatemala.getDate()).padStart(2, '0');
        const fechaHoy = `${anio}-${mes}-${dia}`;
        
        // Mostrar un mensaje de carga
        Swal.fire({
            title: 'Generando reporte...',
            text: 'Por favor espere',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        // Abrir la ventana de impresión con los pedidos del día
        window.open('/imprimir_pedidos_del_dia?fecha=' + fechaHoy, '_blank');
        
        // Cerrar el mensaje de carga
        Swal.close();
        
    } catch (error) {
        console.error('Error al imprimir pedidos del día:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo generar el reporte de pedidos',
            confirmButtonColor: '#5271ff'
        });
    }
}

// Función alternativa con selector de fecha
async function imprimirPedidosPorFecha() {
    const { value: fecha } = await Swal.fire({
        title: 'Seleccione la fecha',
        input: 'date',
        inputValue: new Date().toISOString().split('T')[0],
        inputAttributes: {
            max: new Date().toISOString().split('T')[0]
        },
        showCancelButton: true,
        confirmButtonText: 'Imprimir',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#5271ff',
        inputValidator: (value) => {
            if (!value) {
                return 'Debe seleccionar una fecha'
            }
        }
    });
    
    if (fecha) {
        try {
            Swal.fire({
                title: 'Generando reporte...',
                text: 'Por favor espere',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            window.open('/imprimir_pedidos_del_dia?fecha=' + fecha, '_blank');
            Swal.close();
            
        } catch (error) {
            console.error('Error al imprimir pedidos:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo generar el reporte de pedidos',
                confirmButtonColor: '#5271ff'
            });
        }
    }
}


async function verificarExistencia(codigoProducto, cantidad) {
    try {
        const response = await fetch('/verificar_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo_producto: codigoProducto,
                cantidad: cantidad
            })
        });
        return true;
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}

function calcularTotal() {
    var cantidad = parseInt(jQuery("#cantidadProducto").val()) || 0;
    var precio = parseFloat(jQuery("#precioProducto").val()) || 0;
    var stockDisponible = parseInt(jQuery("#stockDisponible").val()) || 0;
    
    console.log('Stock disponible al calcular:', stockDisponible); // Debug
    
    
    var total = cantidad * precio;
    jQuery("#totalProducto").val(total.toFixed(2));
}

function actualizarTotalGeneral() {
    var total = 0;
    jQuery("#detalleOrden tbody tr").each(function() {
        var subtotal = parseFloat(jQuery(this).find("td:eq(5)").text()) || 0;
        total += subtotal;
    });
    jQuery("#totalGeneral").text(`Q. ${total.toFixed(2)}`);
}

function limpiarCamposProducto() {
    jQuery("#codigoProducto").val("");
    jQuery("#producto").val("").blur();
    jQuery("#presentacion").val("");
    jQuery("#cantidadProducto").val("");
    jQuery("#precioProducto").val("");
    jQuery("#totalProducto").val("");
    jQuery("#stockDisponible").val("");
}

function limpiarFormulario() {
    jQuery('#codigoCliente').val('');
    jQuery('#nombreCliente').val('');
    jQuery('#nombreNegocio').val('');
    jQuery('#nitCliente').val('');
    jQuery('#direccionCliente').val('');
    jQuery('#municipioCliente').val('');
    jQuery('#detalleOrden tbody').empty();
    jQuery('#totalGeneral').text('Q. 0.00');
    jQuery('#comentarios').val('');
    limpiarCamposProducto();
}

function toggleSubmenu(submenuId, chevronId) {
    const submenu = document.getElementById(submenuId);
    const chevron = document.getElementById(chevronId);
    submenu.classList.toggle('active');
    chevron.classList.toggle('active');
}

document.addEventListener('DOMContentLoaded', function() {
    obtenerNumeroPedido();
    
    const fechaActual = new Date();
    const fechaFormateada = ("0" + fechaActual.getDate()).slice(-2) + "/" + 
                    ("0" + (fechaActual.getMonth() + 1)).slice(-2) + "/" + 
                    fechaActual.getFullYear();
    document.getElementById('fechaPedido').textContent = fechaFormateada;

    jQuery(function($) {
        $("#producto").autocomplete({
            source: function(request, response) {
                $.ajax({
                    url: "/buscar_productos",
                    dataType: "json",
                    data: { term: request.term },
                    success: function(data) {
                        response(data.map(function(item) {
                            return {
                                label: item.Descripcion_producto,
                                value: item.Descripcion_producto,
                                codigo: item.Codigo,
                                presentacion: item.Presentacion,
                                precio: item.Precio,
                                existencia: item.EXISTENCIA
                            };
                        }));
                    },
                    error: function(error) {
                        console.error("Error en la petición:", error);
                    }
                });
            },
            minLength: 2,
            select: function(event, ui) {
                console.log("Existencia del producto:", ui.item.existencia); // Para verificar
                $("#codigoProducto").val(ui.item.codigo);
                $("#presentacion").val(ui.item.presentacion);
                $("#precioProducto").val(ui.item.precio);
                $("#cantidadProducto").val("");
                $("#stockDisponible").val(ui.item.existencia); 

                    // Debug para verificar que se asignó correctamente
    console.log('Stock después de asignar:', $("#stockDisponible").val());
            }
        });

        $("#cantidadProducto").on('input', async function() {
            var cantidad = parseInt($(this).val()) || 0;
            var codigoProducto = $("#codigoProducto").val();
            
            if (cantidad <= 0) return;

            const existenciaValida = await verificarExistencia(codigoProducto, cantidad);
            if (!existenciaValida) {
                $(this).val('');
                return;
            }

            calcularTotal();
        });

        $("#agregarProducto").click(async function() {
            var codigo = $("#codigoProducto").val();
            var producto = $("#producto").val();
            var presentacion = $("#presentacion").val();
            var cantidad = parseInt($("#cantidadProducto").val());
            var precio = parseFloat($("#precioProducto").val());
            
            if (!codigo || !producto || !presentacion || !cantidad || !precio) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Campos incompletos',
                    text: 'Por favor complete todos los campos',
                    confirmButtonColor: '#5271ff'
                });
                return;
            }

            const existenciaValida = await verificarExistencia(codigo, cantidad);
            if (!existenciaValida) return;

            var total = cantidad * precio;
            var newRow = `<tr>
                <td>${codigo}</td>
                <td>${producto}</td>
                <td>${presentacion}</td>
                <td>${cantidad}</td>
                <td>${parseFloat(precio).toFixed(2)}</td>
                <td>${parseFloat(total).toFixed(2)}</td>
                <td>
                    <button type="button" class="btn btn-danger btn-sm eliminarProducto">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;

            $("#detalleOrden tbody").append(newRow);
            limpiarCamposProducto();
            actualizarTotalGeneral();
        });

        $(document).on('click', '.eliminarProducto', function() {
            $(this).closest('tr').remove();
            actualizarTotalGeneral();
        });

        $(document).on('input', '#detalleOrden tbody tr td:nth-child(4)', function() {
            var row = $(this).closest('tr');
            var cantidad = parseFloat($(this).text()) || 0;
            var precio = parseFloat(row.find('td:eq(4)').text()) || 0;
            var nuevoTotal = cantidad * precio;
            
            row.find('td:eq(5)').text(nuevoTotal.toFixed(2));
            actualizarTotalGeneral();
        });

        $(document).on('input', '#detalleOrden tbody tr td:nth-child(5)', function() {
            var row = $(this).closest('tr');
            var cantidad = parseFloat(row.find('td:eq(3)').text()) || 0;
            var precio = parseFloat($(this).text()) || 0;
            var nuevoTotal = cantidad * precio;
            
            row.find('td:eq(5)').text(nuevoTotal.toFixed(2));
            actualizarTotalGeneral();
        });

        $('#registrarPedido').on('click', async function(e) {
            e.preventDefault();
            
            if ($('#detalleOrden tbody tr').length === 0) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Advertencia',
                    text: 'Debe agregar al menos un producto al pedido',
                    confirmButtonColor: '#5271ff'
                });
                return;
            }

            if (!$('#codigoCliente').val()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Advertencia',
                    text: 'Debe seleccionar un cliente',
                    confirmButtonColor: '#5271ff'
                });
                return;
            }

            try {
                const encabezado = {
                    CODIGO_CLIENTE: $('#codigoCliente').val(),
                    CODIGO_USUARIO: 1,
                    FECHA_PEDIDO: formatearFecha($('#fechaPedido').text()),
                    NOMBRE_CLIENTE: $('#nombreCliente').val(),
                    NIT: $('#nitCliente').val(),
                    DIRECCION: $('#direccionCliente').val(),
                    TOTAL_PEDIDO: parseFloat($('#totalGeneral').text().replace('Q. ', '')) || 0,
                    COMENTARIOS: $('#comentarios').val()
                };

                const respEnc = await fetch('/insertar_pedido_enc', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(encabezado)
                });

                if (!respEnc.ok) throw new Error('Error al insertar el encabezado del pedido');

                const resultEnc = await respEnc.json();
                const numeroPedido = resultEnc.numero_pedido;

                const detalles = [];
                const actualizacionesStock = [];

                $('#detalleOrden tbody tr').each(function() {
                    const fila = $(this);
                    const codigoProducto = fila.find('td:eq(0)').text();
                    const cantidad = parseInt(fila.find('td:eq(3)').text());

                    detalles.push({
                        NUMERO_PEDIDO: numeroPedido,
                        CODIGO_PRODUCTO: codigoProducto,
                        NOMBRE_PRODUCTO: fila.find('td:eq(1)').text(),
                        UNIDAD_MEDIDA: fila.find('td:eq(2)').text(),
                        CANTIDAD: cantidad,
                        PRECIO_UNITARIO: parseFloat(fila.find('td:eq(4)').text()),
                        TOTAL: parseFloat(fila.find('td:eq(5)').text())
                    });

                    actualizacionesStock.push({
                        CODIGO_PRODUCTO: codigoProducto,
                        CANTIDAD: cantidad
                    });
                });

                const respDet = await fetch('/insertar_pedido_det', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(detalles)
                });

                if (!respDet.ok) throw new Error('Error al insertar los detalles del pedido');

                const respStock = await fetch('/actualizar_stock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(actualizacionesStock)
                });

                if (!respStock.ok) throw new Error('Error al actualizar el stock de productos');

                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: 'Pedido registrado y stock actualizado exitosamente',
                    confirmButtonColor: '#5271ff'
                }).then((result) => {
                    if (result.isConfirmed) {
                        limpiarFormulario();
                        obtenerNumeroPedido();
                    }
                });

            } catch (error) {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo completar la operación: ' + error.message,
                    confirmButtonColor: '#5271ff'
                });
            }
        });

        $('#actualizarPedido').on('click', async function(e) {
            e.preventDefault();
            
            if ($('#detalleOrden tbody tr').length === 0) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Advertencia',
                    text: 'Debe tener al menos un producto en el pedido',
                    confirmButtonColor: '#5271ff'
                });
                return;
            }

            try {
                const numeroPedido = $('#numeroPedido').text();
                
                const encabezado = {
                    NUMERO_PEDIDO: numeroPedido,
                    CODIGO_CLIENTE: $('#codigoCliente').val(),
                    NOMBRE_CLIENTE: $('#nombreCliente').val(),
                    NIT: $('#nitCliente').val(),
                    DIRECCION: $('#direccionCliente').val(),
                    TOTAL_PEDIDO: parseFloat($('#totalGeneral').text().replace('Q. ', '').replace(',', '')) || 0,
                    COMENTARIOS: $('#comentarios').val()
                };

                const detalles = [];
                $('#detalleOrden tbody tr').each(function() {
                    const fila = $(this);
                    detalles.push({
                        NUMERO_PEDIDO: numeroPedido,
                        CODIGO_PRODUCTO: fila.find('td:eq(0)').text(),
                        NOMBRE_PRODUCTO: fila.find('td:eq(1)').text(),
                        UNIDAD_MEDIDA: fila.find('td:eq(2)').text(),
                        CANTIDAD: parseInt(fila.find('td:eq(3)').text()),
                        PRECIO_UNITARIO: parseFloat(fila.find('td:eq(4)').text()),
                        TOTAL: parseFloat(fila.find('td:eq(5)').text())
                    });
                });

                const response = await fetch('/actualizar_pedido', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ encabezado, detalles })
                });

                if (!response.ok) throw new Error('Error al actualizar el pedido');

                Swal.fire({
                    icon: 'success',
                    title: 'Pedido Actualizado',
                    text: 'El pedido se ha actualizado correctamente',
                    confirmButtonColor: '#5271ff'
                });

                limpiarFormulario();
                $('#actualizarPedido').hide();
                $('#cancelarEdicion').hide();
                $('#registrarPedido').show();
                obtenerNumeroPedido();

            } catch (error) {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo actualizar el pedido',
                    confirmButtonColor: '#5271ff'
                });
            }
        });

        $('#cancelarEdicion').on('click', function(e) {
            e.preventDefault();
            
            Swal.fire({
                title: '¿Cancelar edición?',
                text: 'Los cambios no guardados se perderán',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#5271ff',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, cancelar',
                cancelButtonText: 'No, continuar editando'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Limpiar formulario
                    limpiarFormulario();
                    
                    // Ocultar botones de edición y mostrar el de registrar
                    $('#actualizarPedido').hide();
                    $('#cancelarEdicion').hide();
                    $('#registrarPedido').show();
                    
                    // Obtener nuevo número de pedido
                    obtenerNumeroPedido();
                    
                    Swal.fire({
                        icon: 'info',
                        title: 'Edición cancelada',
                        text: 'El formulario ha sido restaurado',
                        confirmButtonColor: '#5271ff',
                        timer: 2000
                    });
                }
            });
        });
    });
});