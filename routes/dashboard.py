from fastapi import APIRouter, Depends

from database.db import conexion_sql
from auth.security import require_login

router = APIRouter(tags=["dashboard"])

@router.get("/api/dashboard/totales")
async def get_dashboard_totales(user: dict = Depends(require_login)):
    """Obtener totales para el dashboard"""
    connection = conexion_sql()
    
    if not connection:
        return {"clientes": 0, "pedidos": 0, "productos": 0}
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pedidos_enc")
        total_pedidos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM productos")
        total_productos = cursor.fetchone()[0]
        
        return {
            "clientes": total_clientes,
            "pedidos": total_pedidos,
            "productos": total_productos
        }
        
    except Exception as e:
        print(f"Error al obtener totales: {e}")
        return {"clientes": 0, "pedidos": 0, "productos": 0}
    finally:
        cursor.close()
        connection.close()

@router.get("/api/dashboard/clientes-por-departamento")
async def get_clientes_por_departamento(user: dict = Depends(require_login)):
    """Obtener distribución de clientes por departamento"""
    connection = conexion_sql()
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT d.nombre_departamento as departamento, COUNT(*) as total
            FROM clientes c
            INNER JOIN departamentos d ON c.departamento = d.departamento
            GROUP BY d.nombre_departamento
            ORDER BY COUNT(*) DESC
        """)
        
        resultados = cursor.fetchall()
        return [{"departamento": row[0], "total": row[1]} for row in resultados]
        
    except Exception as e:
        print(f"Error al obtener clientes por departamento: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

@router.get("/api/dashboard/productos-por-marca")
async def get_productos_por_marca(user: dict = Depends(require_login)):
    """Obtener distribución de productos por marca"""
    connection = conexion_sql()
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT m.nombre_marca as marca, COUNT(*) as total
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            GROUP BY m.nombre_marca
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        resultados = cursor.fetchall()
        return [{"marca": row[0], "total": row[1]} for row in resultados]
        
    except Exception as e:
        print(f"Error al obtener productos por marca: {e}")
        return []
    finally:
        cursor.close()
        connection.close()