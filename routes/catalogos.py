from fastapi import APIRouter, Depends, HTTPException

from database.db import conexion_sql
from auth.security import require_login

router = APIRouter(tags=["catalogos"])

@router.get("/listado_municipios")
async def get_municipios(user: dict = Depends(require_login)):
    """Obtener listado de municipios con información del departamento"""
    connection = conexion_sql()
    
    if not connection:
        return [{"id": 112, "nombre": "SAN LUCAS SACATEPEQUEZ", "departamento_id": 16}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT municipio as id, nombre_municipio as nombre, departamento as departamento_id 
            FROM municipios 
            ORDER BY nombre_municipio
        """)
        municipios = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1], 'departamento_id': row[2]} for row in municipios]
        
    except Exception as e:
        print(f"Error al obtener municipios: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

@router.get("/listado_municipios_por_departamento/{departamento_id}")
async def get_municipios_por_departamento(departamento_id: int, user: dict = Depends(require_login)):
    """Obtener listado de municipios filtrados por departamento"""
    connection = conexion_sql()
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT municipio as id, nombre_municipio as nombre, departamento as departamento_id 
            FROM municipios 
            WHERE departamento = %s
            ORDER BY nombre_municipio
        """, (departamento_id,))
        
        municipios = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1], 'departamento_id': row[2]} for row in municipios]
        
    except Exception as e:
        print(f"Error al obtener municipios por departamento: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


@router.get("/listado_departamentos")
async def get_departamentos(user: dict = Depends(require_login)):
    """Obtener listado de departamentos"""
    connection = conexion_sql()
    
    if not connection:
        return [{"id": 16, "nombre": "SACATEPEQUEZ"}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT departamento as id, nombre_departamento as nombre FROM departamentos ORDER BY nombre_departamento")
        departamentos = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in departamentos]
        
    except Exception as e:
        print(f"Error al obtener departamentos: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

@router.get("/listado_niveles_precio")
async def get_niveles_precio(user: dict = Depends(require_login)):
    """Obtener listado de niveles de precio"""
    connection = conexion_sql()
    
    if not connection:
        return [{"id": 1, "nombre": "TIENDA_BARRIO"}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT nivel_precio as id, descripcion_nivel as nombre FROM nivel_precio ORDER BY nivel_precio")
        niveles = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in niveles]
        
    except Exception as e:
        print(f"Error al obtener niveles de precio: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()