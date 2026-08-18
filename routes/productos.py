from typing import List

from fastapi import APIRouter, HTTPException, Depends

from database.db import conexion_sql
from auth.security import require_login
from models.schemas import ProductResponse
from services.productos_service import get_productos_data

router = APIRouter(tags=["productos"])

@router.get("/api/productos", response_model=List[ProductResponse])
async def get_productos_api(user: dict = Depends(require_login)):
    """API endpoint para obtener productos (JSON)"""
    try:
        productos = await get_productos_data()
        return productos
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener productos")

@router.get("/listado_productos")
async def get_productos_listado(user: dict = Depends(require_login)):
    """API endpoint para obtener listado completo de productos"""
    try:
        productos = await get_productos_data()
        return productos
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener productos")

@router.post("/api/productos/insertar")
async def insertar_producto(producto_data: dict):
    """Insertar nuevo producto"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Obtener disponibilidad (por defecto TRUE si no se especifica)
        disponible = producto_data.get('DISPONIBLE', True)
        if isinstance(disponible, str):
            disponible = disponible.lower() in ['true', '1', 'yes', 'si']
        
        cursor.execute("""
            INSERT INTO productos (nombre_producto, unidad_medida, marca, existencia, costo, disponible)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING codigo_producto
        """, (
            producto_data.get('NOMBRE_PRODUCTO'),
            producto_data.get('UNIDAD_MEDIDA'),
            int(producto_data.get('MARCA')),
            float(producto_data.get('EXISTENCIA', 0)),
            float(producto_data.get('COSTO', 0)),
            disponible
        ))
        
        codigo_producto = cursor.fetchone()[0]
        
        # Insertar precio si se proporciona
        precio = producto_data.get('PRECIO')
        if precio and float(precio) > 0:
            cursor.execute("""
                INSERT INTO precios (nivel_precio, codigo_producto, precio)
                VALUES (1, %s, %s)
            """, (codigo_producto, float(precio)))
        
        connection.commit()
        return {"success": True, "message": "Producto insertado correctamente", "codigo": codigo_producto}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al insertar producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al insertar producto: {str(e)}")
    finally:
        cursor.close()
        connection.close()  

@router.put("/api/productos/actualizar")
async def actualizar_producto(producto_data: dict):
    """Actualizar producto existente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Actualizar producto incluyendo la marca
        cursor.execute("""
            UPDATE productos SET
                nombre_producto = %s, 
                existencia = %s, 
                unidad_medida = %s,
                marca = %s,
                costo = %s
            WHERE codigo_producto = %s
        """, (
            producto_data.get('NOMBRE_PRODUCTO'),
            float(producto_data.get('EXISTENCIA', 0)),
            producto_data.get('UNIDAD_MEDIDA'),
            int(producto_data.get('MARCA')),
            float(producto_data.get('COSTO', 0)), 
            int(producto_data.get('Codigo'))
        ))
        
        # Actualizar o insertar precio
        precio = producto_data.get('PRECIO')
        if precio:
            # Verificar si ya existe un precio
            cursor.execute("""
                SELECT COUNT(*) FROM precios 
                WHERE codigo_producto = %s AND nivel_precio = 1
            """, (int(producto_data.get('Codigo')),))
            
            existe_precio = cursor.fetchone()[0] > 0
            
            if existe_precio:
                cursor.execute("""
                    UPDATE precios SET precio = %s
                    WHERE codigo_producto = %s AND nivel_precio = 1
                """, (float(precio), int(producto_data.get('Codigo'))))
            else:
                cursor.execute("""
                    INSERT INTO precios (nivel_precio, codigo_producto, precio)
                    VALUES (1, %s, %s)
                """, (int(producto_data.get('Codigo')), float(precio)))
        
        connection.commit()
        return {"success": True, "message": "Producto actualizado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al actualizar producto: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al actualizar producto: {str(e)}")
    finally:
        cursor.close()
        connection.close()

        
@router.post("/api/productos/cambiar_disponibilidad")
async def cambiar_disponibilidad_producto(data: dict):
    """Cambiar el estado de disponibilidad de un producto"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        codigo_producto = int(data.get('codigo_producto'))
        disponible = bool(data.get('disponible'))
        
        cursor.execute("""
            UPDATE productos 
            SET disponible = %s
            WHERE codigo_producto = %s
        """, (disponible, codigo_producto))
        
        connection.commit()
        
        estado = "disponible" if disponible else "no disponible"
        
        return {
            "success": True, 
            "message": f"Producto marcado como {estado}",
            "disponible": disponible
        }
        
    except Exception as e:
        connection.rollback()
        print(f"Error al cambiar disponibilidad: {e}")
        raise HTTPException(status_code=500, detail=f"Error al cambiar disponibilidad: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.get("/listado_productos_disponibles")
async def get_productos_disponibles(user: dict = Depends(require_login)):
    """API endpoint para obtener solo productos disponibles"""
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
                COALESCE(p.existencia, 0) as existencia,
                COALESCE(pr.precio, 0) as precio
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto
                AND pr.nivel_precio = 1
            WHERE p.disponible = TRUE
            ORDER BY p.nombre_producto
        """)
        
        productos = cursor.fetchall()
        
        json_data = [{
            'Codigo': row[0],
            'Nombre': row[1],
            'Medida': row[2],
            'Marca': row[3],
            'Existencia': float(row[4]),
            'Precio': float(row[5]) if row[5] is not None else 0.0
        } for row in productos]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener productos disponibles: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener productos disponibles")
    finally:
        cursor.close()
        connection.close()


@router.delete("/api/productos/{codigo_producto}")
async def eliminar_producto(codigo_producto: int):
    """Eliminar producto"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Eliminar precios primero (foreign key)
        cursor.execute("DELETE FROM precios WHERE codigo_producto = %s", (codigo_producto,))
        
        # Eliminar producto
        cursor.execute("DELETE FROM productos WHERE codigo_producto = %s", (codigo_producto,))
        
        if cursor.rowcount > 0:
            connection.commit()
            return {"success": True, "message": "Producto eliminado correctamente"}
        else:
            return {"success": False, "error": "No se encontró el producto a eliminar"}
            
    except Exception as e:
        connection.rollback()
        print(f"Error al eliminar producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar producto: {str(e)}")
    finally:
        cursor.close()
        connection.close()