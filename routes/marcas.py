from fastapi import APIRouter, Depends, HTTPException

from database.db import conexion_sql
from auth.security import require_login

router = APIRouter(tags=["marcas"])


@router.get("/api/marcas")
async def get_marcas(user: dict = Depends(require_login)):
    """Obtener listado de marcas para formularios"""
    connection = conexion_sql()
    
    if not connection:
        return [
            {"id": 1, "nombre": "ADAMS"},
            {"id": 2, "nombre": "BEST"},
            {"id": 3, "nombre": "MONDELEZ"}
        ]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT codigo_marca as id, nombre_marca as nombre FROM marcas ORDER BY nombre_marca")
        marcas = cursor.fetchall()
        
        return [{
            'id': row[0],
            'nombre': row[1]
        } for row in marcas]
        
    except Exception as e:
        print(f"Error al obtener marcas: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


@router.get("/api/marcas/listado")
async def get_marcas_listado(user: dict = Depends(require_login)):
    """Obtener listado completo de marcas con conteo de productos"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                m.codigo_marca as id,
                m.nombre_marca as nombre,
                COUNT(p.codigo_producto) as productos_count
            FROM marcas m
            LEFT JOIN productos p ON m.codigo_marca = p.marca
            GROUP BY m.codigo_marca, m.nombre_marca
            ORDER BY m.nombre_marca
        """)
        
        marcas = cursor.fetchall()
        
        return [{
            'id': row[0],
            'nombre': row[1],
            'productos_count': row[2]
        } for row in marcas]
        
    except Exception as e:
        print(f"Error al obtener marcas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener marcas")
    finally:
        cursor.close()
        connection.close()

@router.post("/api/marcas/insertar")
async def insertar_marca(marca_data: dict, user: dict = Depends(require_login)):
    """Insertar nueva marca"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        nombre_marca = marca_data.get('NOMBRE_MARCA', '').strip().upper()
        
        if not nombre_marca:
            raise HTTPException(status_code=400, detail="El nombre de la marca es requerido")
        
        # Verificar si ya existe
        cursor.execute("SELECT COUNT(*) FROM marcas WHERE UPPER(nombre_marca) = %s", (nombre_marca,))
        existe = cursor.fetchone()[0] > 0
        
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe una marca con ese nombre")
        
        cursor.execute("""
            INSERT INTO marcas (nombre_marca)
            VALUES (%s)
            RETURNING codigo_marca
        """, (nombre_marca,))
        
        codigo_marca = cursor.fetchone()[0]
        connection.commit()
        
        print(f"✅ Marca insertada: {nombre_marca} (código: {codigo_marca})")
        
        return {"success": True, "message": "Marca insertada correctamente", "id": codigo_marca}
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        print(f"Error al insertar marca: {e}")
        raise HTTPException(status_code=500, detail=f"Error al insertar marca: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.put("/api/marcas/actualizar")
async def actualizar_marca(marca_data: dict, user: dict = Depends(require_login)):
    """Actualizar marca existente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        codigo_marca = marca_data.get('id')
        nombre_marca = marca_data.get('NOMBRE_MARCA', '').strip().upper()
        
        if not nombre_marca:
            raise HTTPException(status_code=400, detail="El nombre de la marca es requerido")
        
        # Verificar si ya existe otro con ese nombre
        cursor.execute("""
            SELECT COUNT(*) FROM marcas 
            WHERE UPPER(nombre_marca) = %s AND codigo_marca != %s
        """, (nombre_marca, codigo_marca))
        existe = cursor.fetchone()[0] > 0
        
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe otra marca con ese nombre")
        
        cursor.execute("""
            UPDATE marcas 
            SET nombre_marca = %s
            WHERE codigo_marca = %s
        """, (nombre_marca, codigo_marca))
        
        connection.commit()
        
        print(f"✅ Marca actualizada: {nombre_marca}")
        
        return {"success": True, "message": "Marca actualizada correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        print(f"Error al actualizar marca: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar marca: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.delete("/api/marcas/eliminar/{codigo_marca}")
async def eliminar_marca(codigo_marca: int, user: dict = Depends(require_login)):
    """Eliminar marca (solo si no tiene productos asociados)"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Verificar si tiene productos asociados
        cursor.execute("SELECT COUNT(*) FROM productos WHERE marca = %s", (codigo_marca,))
        productos_count = cursor.fetchone()[0]
        
        if productos_count > 0:
            return {
                "success": False, 
                "error": f"No se puede eliminar la marca porque tiene {productos_count} producto(s) asociado(s)"
            }
        
        cursor.execute("DELETE FROM marcas WHERE codigo_marca = %s", (codigo_marca,))
        
        if cursor.rowcount > 0:
            connection.commit()
            print(f"✅ Marca eliminada: {codigo_marca}")
            return {"success": True, "message": "Marca eliminada correctamente"}
        else:
            return {"success": False, "error": "No se encontró la marca"}
            
    except Exception as e:
        connection.rollback()
        print(f"Error al eliminar marca: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar marca: {str(e)}")
    finally:
        cursor.close()
        connection.close()
