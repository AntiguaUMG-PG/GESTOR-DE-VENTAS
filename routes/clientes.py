from fastapi import APIRouter, Depends, HTTPException

from database.db import conexion_sql
from auth.security import require_login

router = APIRouter(tags=["clientes"])


@router.get("/listado_clientes")
async def get_clientes_data(user: dict = Depends(require_login)):
    """API endpoint para obtener listado de clientes"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                c.codigo_cliente as Codigo,
                c.nombre_cliente as Nombre,
                c.nombre_negocio as Nombre_Negocio,
                c.nit,
                c.telefono as Telefono,
                c.direccion as Direccion,
                m.nombre_municipio as Municipio,
                d.nombre_departamento as Departamento,
                np.descripcion_nivel as Nivel_Precio,
                COALESCE(c.saldo, 0) as Saldo
            FROM clientes c
            LEFT JOIN municipios m ON c.municipio = m.municipio
            LEFT JOIN departamentos d ON c.departamento = d.departamento
            LEFT JOIN nivel_precio np ON c.nivel_precio = np.nivel_precio
            ORDER BY c.nombre_cliente
        """)
        clientes = cursor.fetchall()
        
        json_data = [{
            'Codigo': row[0],
            'Nombre': row[1],
            'Nombre_Negocio': row[2],
            'NIT': row[3],
            'Telefono': row[4],
            'Direccion': row[5],
            'Municipio': row[6],
            'Departamento': row[7],
            'Nivel_Precio': row[8],
            'Saldo': float(row[9]) if row[9] is not None else 0.0
        } for row in clientes]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener clientes: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener clientes")
    finally:
        cursor.close()
        connection.close()

@router.post("/insertar_cliente")
async def insertar_cliente(cliente_data: dict):
    """Insertar nuevo cliente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO clientes (
                nombre_cliente, nombre_negocio, nit, telefono, 
                direccion, municipio, departamento, nivel_precio, saldo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0.0)
        """, (
            cliente_data.get('Nombre'),
            cliente_data.get('Nombre_Negocio'),
            cliente_data.get('NIT'),
            cliente_data.get('Telefono'),
            cliente_data.get('Direccion'),
            int(cliente_data.get('Municipio')),
            int(cliente_data.get('Departamento')),
            int(cliente_data.get('Nivel_Precio'))
        ))
        
        connection.commit()
        return {"success": True, "message": "Cliente insertado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al insertar cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al insertar cliente: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.put("/actualizar_cliente")
async def actualizar_cliente(cliente_data: dict):
    """Actualización de cliente existente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE clientes SET
                nombre_cliente = %s, nombre_negocio = %s, nit = %s, telefono = %s,
                direccion = %s, municipio = %s, departamento = %s, nivel_precio = %s
            WHERE codigo_cliente = %s
        """, (
            cliente_data.get('Nombre'),
            cliente_data.get('Nombre_Negocio'),
            cliente_data.get('NIT'),
            cliente_data.get('Telefono'),
            cliente_data.get('Direccion'),
            int(cliente_data.get('Municipio')),
            int(cliente_data.get('Departamento')),
            int(cliente_data.get('Nivel_Precio')),
            int(cliente_data.get('Codigo'))
        ))
        
        connection.commit()
        return {"success": True, "message": "Cliente actualizado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al actualizar cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@router.delete("/eliminar_cliente/{codigo_cliente}")
async def eliminar_cliente(codigo_cliente: int):
    """Eliminar cliente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM clientes WHERE codigo_cliente = %s", (codigo_cliente,))
        
        if cursor.rowcount > 0:
            connection.commit()
            return {"success": True, "message": "Cliente eliminado correctamente"}
        else:
            return {"success": False, "error": "No se encontró el cliente a eliminar"}
            
    except Exception as e:
        connection.rollback()
        print(f"Error al eliminar cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
    finally:
        cursor.close()
        connection.close()