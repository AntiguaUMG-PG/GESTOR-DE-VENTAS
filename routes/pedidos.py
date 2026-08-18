from datetime import datetime, date
from typing import List, Dict, Any

from fastapi import APIRouter, Request, Depends, HTTPException

from database.db import conexion_sql
from auth.security import require_login
from config.templates import templates

router = APIRouter(tags=["pedidos"])

@router.get("/listado_pedidos")
async def get_pedidos_data(
    user: dict = Depends(require_login),
    fecha_inicio: str = None,
    fecha_fin: str = None
):
    """API endpoint para obtener listado de pedidos con filtro opcional de fechas"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Query base
        query = """
            SELECT 
                p.numero_pedido,
                p.fecha,
                p.nombre_cliente,
                p.nit,
                p.direccion,
                COALESCE(p.total_documento, 0) as total_documento,
                p.estado
            FROM pedidos_enc p
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros de fecha si existen
        if fecha_inicio:
            query += " AND DATE(p.fecha) >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND DATE(p.fecha) <= %s"
            params.append(fecha_fin)
        
        query += " ORDER BY p.numero_pedido DESC"
        
        cursor.execute(query, params)
        pedidos = cursor.fetchall()
        
        json_data = [{
            'NUMERO_PEDIDO': row[0],
            'FECHA': row[1].strftime('%d/%m/%Y %H:%M:%S') if row[1] else '',
            'NOMBRE_CLIENTE': row[2],
            'NIT': row[3],
            'DIRECCION': row[4],
            'TOTAL_DOCUMENTO': float(row[5]) if row[5] is not None else 0.0,
            'ESTADO': row[6]
        } for row in pedidos]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener pedidos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener pedidos")
    finally:
        cursor.close()
        connection.close()
        

@router.get("/numero_pedido")
async def get_numero_pedido(user: dict = Depends(require_login)):
    connection = conexion_sql()
    
    if not connection:
        return {"ultimo_numero_pedido": 1}
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COALESCE(MAX(numero_pedido), 0) + 1 FROM pedidos_enc")
        siguiente_numero = cursor.fetchone()[0]
        
        return {"ultimo_numero_pedido": siguiente_numero}
        
    except Exception as e:
        print(f"Error al obtener número de pedido: {e}")
        return {"ultimo_numero_pedido": 1}
    finally:
        cursor.close()
        connection.close()

@router.get("/buscar_productos")
async def buscar_productos(term: str):
    connection = conexion_sql()
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                p.codigo_producto as Codigo,
                p.nombre_producto as Descripcion_producto,
                p.unidad_medida as Presentacion,
                COALESCE(pr.precio, 0) as Precio,
                COALESCE(p.existencia, 0) as EXISTENCIA
            FROM productos p
            LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto 
                AND pr.nivel_precio = 1
            WHERE 
                p.disponible = TRUE
                AND LOWER(p.nombre_producto) LIKE LOWER(%s)
            ORDER BY p.nombre_producto
            LIMIT 20
        """, (f'%{term}%',))
        productos = cursor.fetchall()
        
        json_data = [{
            'Codigo': row[0],
            'Descripcion_producto': row[1],
            'Presentacion': row[2],
            'Precio': float(row[3]) if row[3] is not None else 0.0,
            'EXISTENCIA': int(row[4]) if row[4] is not None else 0
        } for row in productos]
        
        return json_data
        
    except Exception as e:
        print(f"Error al buscar productos: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

@router.post("/verificar_stock")
async def verificar_stock(stock_data: dict):
    connection = conexion_sql()
    
    if not connection:
        return {"success": False, "message": "Error de conexión"}
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT existencia 
            FROM productos 
            WHERE codigo_producto = %s
        """, (stock_data.get('codigo_producto'),))
        
        result = cursor.fetchone()
        
        if result:
            existencia = int(result[0]) if result[0] else 0
            cantidad_solicitada = int(stock_data.get('cantidad', 0))
            
            if cantidad_solicitada > existencia:
                return {
                    "success": False,
                    "message": f"Stock insuficiente. Disponible: {existencia}"
                }
            else:
                return {"success": True, "existencia": existencia}
        else:
            return {"success": False, "message": "Producto no encontrado"}
            
    except Exception as e:
        print(f"Error al verificar stock: {e}")
        return {"success": False, "message": "Error al verificar stock"}
    finally:
        cursor.close()
        connection.close()

@router.post("/insertar_pedido_enc")
async def insertar_pedido_enc(pedido_data: dict):
    """Insertar el encabezado de pedido"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        fecha_str = pedido_data.get('FECHA_PEDIDO')
        if fecha_str and '/' in fecha_str:
            fecha_pedido = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
        else:
            fecha_pedido = datetime.now() 
        
        cursor.execute("""
            INSERT INTO pedidos_enc (
                fecha, codigo_usuario, codigo_cliente, nombre_cliente,
                nit, direccion, total_documento, estado, comentarios
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'ABIERTO', %s)
            RETURNING numero_pedido
        """, (
            fecha_pedido,
            pedido_data.get('CODIGO_USUARIO'),
            pedido_data.get('CODIGO_CLIENTE'),
            pedido_data.get('NOMBRE_CLIENTE'),
            pedido_data.get('NIT'),
            pedido_data.get('DIRECCION'),
            pedido_data.get('TOTAL_PEDIDO'),
            pedido_data.get('COMENTARIOS')
        ))
        
        numero_pedido = cursor.fetchone()[0]
        connection.commit()
        
        return {"success": True, "numero_pedido": numero_pedido}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al insertar pedido: {e}")
        raise HTTPException(status_code=500, detail=f"Error al insertar pedido: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.post("/insertar_pedido_det")
async def insertar_pedido_det(detalles_data: List[Dict[str, Any]]):
    """Insertar los detalles de pedido"""
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        for i, detalle in enumerate(detalles_data):
            print(f"Insertando detalle {i+1}: {detalle}")
            
            cursor.execute("""
                INSERT INTO pedidos_det (
                    numero_pedido, codigo_producto, nombre_producto,
                    unidad_medida, cantidad, precio_unitario, total_linea
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                detalle.get('NUMERO_PEDIDO'),
                int(detalle.get('CODIGO_PRODUCTO')),
                detalle.get('NOMBRE_PRODUCTO'),
                detalle.get('UNIDAD_MEDIDA'),
                int(detalle.get('CANTIDAD', 0)),
                float(detalle.get('PRECIO_UNITARIO', 0)),
                float(detalle.get('TOTAL', 0))
            ))
        
        connection.commit()
        print("✅ Detalles insertados exitosamente")
        return {"success": True, "message": "Detalles insertados correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error al insertar detalles: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al insertar detalles: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.post("/actualizar_stock")
async def actualizar_stock(productos_data: List[Dict[str, Any]]):
    """Actualizar stock de productos - NO permite stock negativo"""

    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        productos_sin_stock = []
        
        for producto in productos_data:
            codigo = producto.get('CODIGO_PRODUCTO')
            cantidad = producto.get('CANTIDAD')
            
            # Verificar stock actual antes de actualizar
            cursor.execute("""
                SELECT existencia, nombre_producto 
                FROM productos 
                WHERE codigo_producto = %s
            """, (int(codigo),))
            
            resultado = cursor.fetchone()
            
            if resultado:
                stock_actual = float(resultado[0]) if resultado[0] else 0
                nombre_producto = resultado[1]
                
                # Calcular el nuevo stock
                nuevo_stock = stock_actual - float(cantidad)
                
                # Si el nuevo stock sería negativo, ajustarlo a 0
                if nuevo_stock < 0:
                    productos_sin_stock.append({
                        'codigo': codigo,
                        'nombre': nombre_producto,
                        'stock_actual': stock_actual,
                        'cantidad_solicitada': cantidad,
                        'faltante': abs(nuevo_stock)
                    })
                    nuevo_stock = 0
                
                print(f"Actualizando producto {codigo} ({nombre_producto}): {stock_actual} - {cantidad} = {nuevo_stock}")
                
                # Actualizar con el nuevo stock (mínimo 0)
                cursor.execute("""
                    UPDATE productos 
                    SET existencia = %s
                    WHERE codigo_producto = %s
                """, (
                    nuevo_stock,
                    int(codigo)
                ))
        
        connection.commit()
        
        # Verificar si hubo productos sin stock suficiente
        if productos_sin_stock:
            mensaje_warning = "Stock actualizado pero algunos productos no tenían suficiente inventario:\n\n"
            for prod in productos_sin_stock:
                mensaje_warning += f"• {prod['nombre']} - Stock disponible: {prod['stock_actual']}, Solicitado: {prod['cantidad_solicitada']}, Faltante: {prod['faltante']}\n"
            
            print("⚠️ " + mensaje_warning)
            return {
                "success": True, 
                "message": "Stock actualizado",
                "warning": True,
                "productos_sin_stock": productos_sin_stock,
                "mensaje_warning": mensaje_warning
            }
        
        print("✅ Stock actualizado exitosamente")
        return {"success": True, "message": "Stock actualizado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error al actualizar stock: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al actualizar stock: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/detalle_pedido/{numero_pedido}")
async def get_detalle_pedido(numero_pedido: int):
    """Obtener detalles de un pedido específico"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                codigo_producto,
                nombre_producto,
                unidad_medida,
                cantidad,
                precio_unitario,
                total_linea
            FROM pedidos_det
            WHERE numero_pedido = %s
            ORDER BY numero_linea
        """, (numero_pedido,))
        
        detalles = cursor.fetchall()
        
        json_data = [{
            'CODIGO_PRODUCTO': row[0],
            'NOMBRE_PRODUCTO': row[1],
            'UNIDAD_MEDIDA': row[2],
            'CANTIDAD': row[3],
            'PRECIO_UNITARIO': float(row[4]),
            'TOTAL_LINEA': float(row[5])
        } for row in detalles]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener detalle del pedido: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener detalle del pedido")
    finally:
        cursor.close()
        connection.close()

@router.get("/obtener_pedido_completo/{numero_pedido}")
async def obtener_pedido_completo(numero_pedido: int, user: dict = Depends(require_login)):
    """Obtener pedido completo con encabezado y detalle para edición"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Obtener encabezado - SIN municipio porque no existe en la tabla
        cursor.execute("""
            SELECT numero_pedido, codigo_cliente, codigo_usuario, fecha, 
                   nombre_cliente, nit, direccion, total_documento, 
                   comentarios, estado
            FROM pedidos_enc 
            WHERE numero_pedido = %s
        """, (numero_pedido,))
        
        enc = cursor.fetchone()
        if not enc:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        encabezado = {
            'NUMERO_PEDIDO': enc[0],
            'CODIGO_CLIENTE': enc[1],
            'CODIGO_USUARIO': enc[2],
            'FECHA': enc[3].strftime('%d/%m/%Y') if enc[3] else '',
            'NOMBRE_CLIENTE': enc[4],
            'NIT': enc[5],
            'DIRECCION': enc[6],
            'TOTAL_DOCUMENTO': float(enc[7]) if enc[7] else 0,
            'COMENTARIOS': enc[8] if enc[8] else '',
            'ESTADO': enc[9],
            'NOMBRE_NEGOCIO': '',  # No está en pedidos_enc
            'MUNICIPIO': ''  # No está en pedidos_enc
        }
        
        # Obtener detalle
        cursor.execute("""
            SELECT codigo_producto, nombre_producto, unidad_medida, 
                   cantidad, precio_unitario, total_linea
            FROM pedidos_det 
            WHERE numero_pedido = %s
            ORDER BY numero_linea
        """, (numero_pedido,))
        
        detalle = []
        for row in cursor.fetchall():
            detalle.append({
                'CODIGO_PRODUCTO': row[0],
                'NOMBRE_PRODUCTO': row[1],
                'UNIDAD_MEDIDA': row[2],
                'CANTIDAD': row[3],
                'PRECIO_UNITARIO': float(row[4]),
                'TOTAL_LINEA': float(row[5])
            })
        
        return {'encabezado': encabezado, 'detalle': detalle}
        
    except Exception as e:
        print(f"Error al obtener pedido: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@router.put("/actualizar_pedido")
async def actualizar_pedido(data: dict, user: dict = Depends(require_login)):
    """Actualizar pedido completo"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        encabezado = data['encabezado']
        detalles = data['detalles']
        
        # Actualizar encabezado
        cursor.execute("""
            UPDATE pedidos_enc 
            SET nombre_cliente = %s, nit = %s, direccion = %s, 
                total_documento = %s, comentarios = %s
            WHERE numero_pedido = %s
        """, (
            encabezado['NOMBRE_CLIENTE'],
            encabezado['NIT'],
            encabezado['DIRECCION'],
            encabezado['TOTAL_PEDIDO'],
            encabezado.get('COMENTARIOS', ''),
            encabezado['NUMERO_PEDIDO']
        ))
        
        # Eliminar detalles anteriores
        cursor.execute("DELETE FROM pedidos_det WHERE numero_pedido = %s", 
                      (encabezado['NUMERO_PEDIDO'],))
        
        # Insertar nuevos detalles
        for detalle in detalles:
            cursor.execute("""
                INSERT INTO pedidos_det 
                (numero_pedido, codigo_producto, nombre_producto, unidad_medida, 
                 cantidad, precio_unitario, total_linea)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                detalle['NUMERO_PEDIDO'],
                detalle['CODIGO_PRODUCTO'],
                detalle['NOMBRE_PRODUCTO'],
                detalle['UNIDAD_MEDIDA'],
                detalle['CANTIDAD'],
                detalle['PRECIO_UNITARIO'],
                detalle['TOTAL']
            ))
        
        connection.commit()
        return {"success": True, "message": "Pedido actualizado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al actualizar pedido: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@router.get("/imprimir_pedido/{numero_pedido}")
async def imprimir_pedido(request: Request, numero_pedido: int):
    """Generar vista PDF del pedido"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                numero_pedido,
                fecha,
                nombre_cliente,
                nit,
                direccion,
                total_documento,
                estado,
                comentarios
            FROM pedidos_enc
            WHERE numero_pedido = %s
        """, (numero_pedido,))
        
        encabezado = cursor.fetchone()
        
        if not encabezado:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        cursor.execute("""
            SELECT 
                codigo_producto,
                nombre_producto,
                unidad_medida,
                cantidad,
                precio_unitario,
                total_linea
            FROM pedidos_det
            WHERE numero_pedido = %s
            ORDER BY numero_linea
        """, (numero_pedido,))
        
        detalles = cursor.fetchall()
        
        fecha_pedido = encabezado[1].strftime('%d/%m/%Y %H:%M:%S Hrs') if encabezado[1] else ''
        
        pedido_data = {
            'numero': encabezado[0],
            'fecha': fecha_pedido,
            'cliente': encabezado[2],
            'nit': encabezado[3],
            'direccion': encabezado[4],
            'total': float(encabezado[5]) if encabezado[5] else 0.0,
            'estado': encabezado[6],
            'comentarios': encabezado[7] or ''
        }
        
        detalles_lista = [{
            'codigo': row[0],
            'producto': row[1],
            'unidad': row[2],
            'cantidad': float(row[3]) if row[3] else 0,
            'precio': float(row[4]) if row[4] else 0.0,
            'total': float(row[5]) if row[5] else 0.0
        } for row in detalles]
        
        fecha_impresion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        return templates.TemplateResponse("pedido_pdf.html", {
            "request": request,
            "pedido": pedido_data,
            "detalles": detalles_lista,
            "fecha_impresion": fecha_impresion
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.get("/imprimir_pedidos_del_dia")
async def imprimir_pedidos_del_dia(request: Request, fecha: str = None):
    """
    Genera una vista HTML para imprimir todos los pedidos de un día específico
    con todos sus detalles
    """
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Si no se proporciona fecha, usar la fecha actual
        if not fecha:
            fecha = date.today().strftime('%Y-%m-%d')
        
        # Obtener todos los pedidos del día
        cursor.execute("""
            SELECT 
                numero_pedido,
                fecha,
                nombre_cliente,
                nit,
                direccion,
                total_documento,
                estado,
                comentarios
            FROM pedidos_enc
            WHERE DATE(fecha) = %s
            ORDER BY numero_pedido
        """, (fecha,))
        
        pedidos_enc = cursor.fetchall()
        
        if not pedidos_enc:
            # Si no hay pedidos, mostrar mensaje
            return templates.TemplateResponse("sin_pedidos.html", {
                "request": request,
                "fecha": fecha,
                "mensaje": "No se encontraron pedidos para la fecha seleccionada"
            })
        
        # Para cada pedido, obtener sus detalles
        pedidos_completos = []
        total_general = 0
        
        for pedido_enc in pedidos_enc:
            numero_pedido = pedido_enc[0]
            
            # Obtener detalles del pedido
            cursor.execute("""
                SELECT 
                    codigo_producto,
                    nombre_producto,
                    unidad_medida,
                    cantidad,
                    precio_unitario,
                    total_linea
                FROM pedidos_det
                WHERE numero_pedido = %s
                ORDER BY numero_linea
            """, (numero_pedido,))
            
            detalles = cursor.fetchall()
            
            # Formatear datos del pedido
            pedido_data = {
                'NUMERO_PEDIDO': pedido_enc[0],
                'FECHA': pedido_enc[1].strftime('%d/%m/%Y %H:%M:%S') if pedido_enc[1] else '',
                'NOMBRE_CLIENTE': pedido_enc[2],
                'NIT': pedido_enc[3],
                'DIRECCION': pedido_enc[4],
                'TOTAL_DOCUMENTO': float(pedido_enc[5]) if pedido_enc[5] else 0.0,
                'ESTADO': pedido_enc[6],
                'COMENTARIOS': pedido_enc[7] or '',
                'DETALLES': []
            }
            
            # Agregar detalles
            for detalle in detalles:
                pedido_data['DETALLES'].append({
                    'CODIGO_PRODUCTO': detalle[0],
                    'NOMBRE_PRODUCTO': detalle[1],
                    'UNIDAD_MEDIDA': detalle[2],
                    'CANTIDAD': float(detalle[3]) if detalle[3] else 0,
                    'PRECIO_UNITARIO': float(detalle[4]) if detalle[4] else 0.0,
                    'TOTAL_LINEA': float(detalle[5]) if detalle[5] else 0.0
                })
            
            pedidos_completos.append(pedido_data)
            total_general += pedido_data['TOTAL_DOCUMENTO']
        
        # Formatear fecha para mostrar
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
        fecha_formato = fecha_obj.strftime('%d/%m/%Y')
        
        fecha_impresion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Renderizar template
        return templates.TemplateResponse("pedidos_del_dia.html", {
            "request": request,
            "fecha": fecha_formato,
            "pedidos": pedidos_completos,
            "total_general": total_general,
            "cantidad_pedidos": len(pedidos_completos),
            "fecha_impresion": fecha_impresion
        })
        
    except Exception as e:
        print(f"Error al generar reporte de pedidos del día: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/pedidos_del_dia")
async def get_pedidos_del_dia(fecha: str = None):
    """
    API endpoint para obtener todos los pedidos del día (JSON)
    Útil para consultas desde JavaScript
    """
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Si no se proporciona fecha, usar la fecha actual
        if not fecha:
            fecha = date.today().strftime('%Y-%m-%d')
        
        # Obtener pedidos del día
        cursor.execute("""
            SELECT 
                pe.numero_pedido,
                pe.fecha,
                pe.nombre_cliente,
                pe.nit,
                pe.direccion,
                pe.total_documento,
                pe.estado,
                pe.comentarios
            FROM pedidos_enc pe
            WHERE DATE(pe.fecha) = %s
            ORDER BY pe.numero_pedido
        """, (fecha,))
        
        pedidos = cursor.fetchall()
        
        pedidos_lista = []
        
        for pedido in pedidos:
            # Obtener detalles de cada pedido
            cursor.execute("""
                SELECT 
                    codigo_producto,
                    nombre_producto,
                    unidad_medida,
                    cantidad,
                    precio_unitario,
                    total_linea
                FROM pedidos_det
                WHERE numero_pedido = %s
                ORDER BY numero_linea
            """, (pedido[0],))
            
            detalles = cursor.fetchall()
            
            pedido_data = {
                'numero_pedido': pedido[0],
                'fecha': pedido[1].strftime('%d/%m/%Y %H:%M:%S') if pedido[1] else '',
                'nombre_cliente': pedido[2],
                'nit': pedido[3],
                'direccion': pedido[4],
                'total_documento': float(pedido[5]) if pedido[5] else 0.0,
                'estado': pedido[6],
                'comentarios': pedido[7] or '',
                'detalles': [{
                    'codigo_producto': d[0],
                    'nombre_producto': d[1],
                    'unidad_medida': d[2],
                    'cantidad': float(d[3]) if d[3] else 0,
                    'precio_unitario': float(d[4]) if d[4] else 0.0,
                    'total_linea': float(d[5]) if d[5] else 0.0
                } for d in detalles]
            }
            
            pedidos_lista.append(pedido_data)
        
        return {
            'fecha': fecha,
            'total_pedidos': len(pedidos_lista),
            'pedidos': pedidos_lista
        }
        
    except Exception as e:
        print(f"Error al obtener pedidos del día: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener pedidos del día: {str(e)}")
    finally:
        cursor.close()
        connection.close()
