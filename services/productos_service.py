from typing import List
from database.db import conexion_sql

async def get_productos_data() -> List[dict]:
    """Función auxiliar para obtener datos de productos"""
    """Obtener datos de productos con disponibilidad"""
    connection = conexion_sql()
    
    if not connection:
        raise Exception("No se pudo conectar a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca,
                COALESCE(p.existencia, 0) as existencia,
                COALESCE(p.costo, 0) as costo,    
                COALESCE(pr.precio, 0) as precio,
                COALESCE(p.disponible, TRUE) as disponible
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto
                AND pr.nivel_precio = 1
            ORDER BY p.nombre_producto
        """)
        
        contenido_producto = cursor.fetchall()
        
        json_data = [{
            'Codigo': row[0],
            'Nombre': row[1],
            'Medida': row[2],
            'Marca': row[3],
            'Existencia': float(row[4]),
            'Costo': float(row[5]) if row[5] is not None else 0.0,  
            'Precio': float(row[6]) if row[6] is not None else 0.0,
            'Disponible': row[7] 
        } for row in contenido_producto]
        
        return json_data
        
    except Exception as e:
        print(f"Error en consulta de productos: {e}")
        raise Exception("Error al consultar productos")
    finally:
        cursor.close()
        connection.close()