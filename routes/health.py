from fastapi import APIRouter

from database.db import conexion_sql

router = APIRouter(tags=["health"])


@router.get("/api/info")
async def api_info():
    """Información de la API"""
    return {
        "name": "Gestor de Pedidos API",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "description": "API para gestión de pedidos con PostgreSQL",
        "endpoints": {
            "authentication": "/api/autenticacion",
            "products": "/api/productos",
            "health": "/health"
        }
    }

@router.get("/health")
async def health_check():
    """Verificar estado de la API y conexión a base de datos"""
    connection = conexion_sql()
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            
            return {
                "status": "healthy",
                "database": "connected",
                "db_version": db_version
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "error",
                "error": str(e)
            }
    else:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }
