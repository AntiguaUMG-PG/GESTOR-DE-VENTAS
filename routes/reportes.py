from datetime import datetime, date

from fastapi import APIRouter, Request, HTTPException

from database.db import conexion_sql
from config.templates import templates

router = APIRouter(tags=["reportes"])

@router.get("/reporte/inventario-vs-pedidos")
async def get_reporte_inventario_pedidos(fecha: str = None):
    """
    Comparar productos vendidos en el día vs inventario disponible
    Parámetro fecha opcional en formato YYYY-MM-DD (por defecto hoy)
    """
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        if not fecha:
            fecha = date.today().strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT 
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca,
                COALESCE(p.existencia, 0) AS inventario_actual,
                v.cantidad_vendida,
                COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0) AS inventario_resultante,
                CASE 
                    WHEN (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0
                    THEN ABS(COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0))
                    ELSE 0 
                END AS faltante,
                pr.precio
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto
            INNER JOIN (
                SELECT 
                    pd.codigo_producto,
                    COALESCE(SUM(pd.cantidad), 0) AS cantidad_vendida
                FROM pedidos_det pd
                INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                WHERE DATE(pe.fecha) = %s
                GROUP BY pd.codigo_producto
            ) AS v ON p.codigo_producto = v.codigo_producto
            ORDER BY 
                CASE WHEN (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0 THEN 0 ELSE 1 END,
                p.nombre_producto
        """, (fecha,))
        
        resultados = cursor.fetchall()
        
        json_data = [{
            'codigo_producto': row[0],
            'nombre_producto': row[1],
            'unidad_medida': row[2],
            'marca': row[3],
            'inventario_actual': int(row[4]),
            'cantidad_vendida': int(row[5]),
            'inventario_resultante': int(row[6]),
            'faltante': int(row[7]),
            'precio': float(row[8]) if row[8] is not None else 0.0,
            'estado': 'INSUFICIENTE' if row[7] > 0 else 'SUFICIENTE'
        } for row in resultados]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener reporte: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener reporte: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.get("/reporte/resumen-inventario")
async def get_resumen_inventario(fecha: str = None):
    """
    Resumen estadístico del inventario vs pedidos del día
    """
    connection = conexion_sql()

    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")

    try:
        cursor = connection.cursor()

        if not fecha:
            fecha = date.today().strftime('%Y-%m-%d')

        # Total de productos vendidos en la fecha seleccionada
        cursor.execute("""
            SELECT COUNT(DISTINCT pd.codigo_producto)
            FROM pedidos_det pd
            INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
            WHERE DATE(pe.fecha) = %s
        """, (fecha,))
        total_productos_vendidos = cursor.fetchone()[0]

        # Productos con inventario insuficiente
        cursor.execute("""
            SELECT COUNT(*)
            FROM productos p
            INNER JOIN (
                SELECT 
                    pd.codigo_producto,
                    COALESCE(SUM(pd.cantidad), 0) AS cantidad_vendida
                FROM pedidos_det pd
                INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                WHERE DATE(pe.fecha) = %s
                GROUP BY pd.codigo_producto
            ) AS v ON p.codigo_producto = v.codigo_producto
            WHERE (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0
        """, (fecha,))
        productos_insuficientes = cursor.fetchone()[0]

        # Total de unidades faltantes
        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0 
                        THEN ABS(COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0))
                        ELSE 0 
                    END
                ), 0)
            FROM productos p
            INNER JOIN (
                SELECT 
                    pd.codigo_producto,
                    COALESCE(SUM(pd.cantidad), 0) AS cantidad_vendida
                FROM pedidos_det pd
                INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                WHERE DATE(pe.fecha) = %s
                GROUP BY pd.codigo_producto
            ) AS v ON p.codigo_producto = v.codigo_producto
        """, (fecha,))
        total_unidades_faltantes = cursor.fetchone()[0] or 0

        # Total de pedidos del día
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pedidos_enc 
            WHERE DATE(fecha) = %s
        """, (fecha,))
        total_pedidos = cursor.fetchone()[0]

        return {
            'fecha': fecha,
            'total_productos_vendidos': total_productos_vendidos,
            'productos_con_inventario_suficiente': total_productos_vendidos - productos_insuficientes,
            'productos_con_inventario_insuficiente': productos_insuficientes,
            'total_unidades_faltantes': int(total_unidades_faltantes),
            'total_pedidos_dia': total_pedidos,
            'porcentaje_cobertura': round(
                ((total_productos_vendidos - productos_insuficientes) / total_productos_vendidos * 100)
                if total_productos_vendidos > 0 else 100, 2
            )
        }

    except Exception as e:
        print(f"Error al obtener resumen: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/reporte/productos-criticos")
async def get_productos_criticos(limite: int = 10):
    """
    Obtener productos con inventario más bajo o crítico
    """
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca,
                COALESCE(p.existencia, 0) as existencia
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            WHERE COALESCE(p.existencia, 0) <= 10
            ORDER BY p.existencia ASC
            LIMIT %s
        """, (limite,))
        
        resultados = cursor.fetchall()
        
        return [{
            'codigo_producto': row[0],
            'nombre_producto': row[1],
            'unidad_medida': row[2],
            'marca': row[3],
            'existencia': int(row[4]),
            'nivel_alerta': 'CRITICO' if row[4] <= 5 else 'BAJO'
        } for row in resultados]
        
    except Exception as e:
        print(f"Error al obtener productos críticos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener productos críticos: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.get("/imprimir_reporte_inventario")
async def imprimir_reporte_inventario(request: Request, fecha: str = None):
    """
    Genera la vista HTML para imprimir el reporte de inventario del día seleccionado
    """

    if not fecha:
        fecha = date.today().strftime('%Y-%m-%d')
    
    connection = conexion_sql()
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()

        # Resumen de inventario
        cursor.execute("""
        WITH ProductosVendidos AS (
            SELECT
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                p.marca,
                COALESCE(p.existencia,0) AS existencia,
                COALESCE(SUM(pd.cantidad),0) AS cantidad_vendida
            FROM productos p
            LEFT JOIN pedidos_det pd ON p.codigo_producto = pd.codigo_producto
            LEFT JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                AND DATE(pe.fecha) = %s
            GROUP BY p.codigo_producto, p.nombre_producto, p.unidad_medida, p.marca, p.existencia
        )
        SELECT
            COUNT(*) AS total_productos_vendidos,
            SUM(CASE WHEN existencia - cantidad_vendida >= 0 THEN 1 ELSE 0 END) AS productos_suficientes,
            SUM(CASE WHEN existencia - cantidad_vendida < 0 THEN 1 ELSE 0 END) AS productos_insuficientes,
            SUM(CASE WHEN existencia - cantidad_vendida < 0 THEN ABS(existencia - cantidad_vendida) ELSE 0 END) AS total_unidades_faltantes
        FROM ProductosVendidos
        """, (fecha,))
        
        resumen = cursor.fetchone()
        resumen_data = {
            'total_productos_vendidos': resumen[0],
            'productos_con_inventario_suficiente': resumen[1],
            'productos_con_inventario_insuficiente': resumen[2],
            'total_unidades_faltantes': int(resumen[3])
        }

        # Detalle
        cursor.execute("""
        WITH ProductosVendidos AS (
            SELECT
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca AS marca,
                COALESCE(p.existencia,0) AS inventario_actual,
                SUM(pd.cantidad) AS cantidad_vendida
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            INNER JOIN pedidos_det pd ON p.codigo_producto = pd.codigo_producto
            INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                AND DATE(pe.fecha) = %s
            GROUP BY p.codigo_producto, p.nombre_producto, p.unidad_medida, m.nombre_marca, p.existencia
        )
        SELECT
            codigo_producto,
            nombre_producto,
            unidad_medida,
            marca,
            inventario_actual,
            cantidad_vendida,
            inventario_actual - cantidad_vendida AS inventario_resultante,
            CASE WHEN inventario_actual - cantidad_vendida < 0 THEN ABS(inventario_actual - cantidad_vendida) ELSE 0 END AS faltante
        FROM ProductosVendidos
        ORDER BY faltante DESC, nombre_producto
        """, (fecha,))

        resultados = cursor.fetchall()
        productos_lista = []
        for row in resultados:
            productos_lista.append({
                'codigo_producto': row[0],
                'nombre_producto': row[1],
                'unidad_medida': row[2],
                'marca': row[3],
                'inventario_actual': int(row[4]),
                'cantidad_vendida': int(row[5]),
                'inventario_resultante': int(row[6]),
                'faltante': int(row[7]),
                'estado': 'INSUFICIENTE' if row[7] > 0 else 'SUFICIENTE'
            })

        fecha_impresion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        return templates.TemplateResponse("reporte_inv_pdf.html", {
            "request": request,
            "fecha": fecha,
            "datos": productos_lista,
            "resumen": resumen_data,
            "fecha_impresion": fecha_impresion
        })

    except Exception as e:
        print(f"Error al generar reporte de inventario: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar reporte de inventario: {str(e)}")
    finally:
        cursor.close()
        connection.close()
