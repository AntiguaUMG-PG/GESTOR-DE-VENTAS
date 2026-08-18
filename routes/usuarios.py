
from fastapi import APIRouter, Depends, HTTPException

from database.db import conexion_sql
from auth.security import require_login
from models.schemas import UsuarioCreate, UsuarioUpdate, CambiarClaveRequest

router = APIRouter(tags=["usuarios"])


@router.get("/api/usuarios")
async def get_usuarios(user: dict = Depends(require_login)):
    """Obtener listado de usuarios"""
    
    # Verificar permisos de administrador
    if user.get("codigo_perfil") != 1:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver usuarios")
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                u.codigo_usuario,
                u.usuario,
                u.nombre_usuario,
                u.fecha_registro,
                u.codigo_perfil,
                p.descripcion as perfil_descripcion
            FROM usuarios u
            INNER JOIN perfil p ON u.codigo_perfil = p.codigo_perfil
            ORDER BY u.codigo_usuario DESC
        """)
        
        usuarios = cursor.fetchall()
        
        return [{
            'codigo_usuario': row[0],
            'usuario': row[1],
            'nombre_usuario': row[2],
            'fecha_registro': row[3].isoformat() if row[3] else None,
            'codigo_perfil': row[4],
            'perfil_descripcion': row[5]
        } for row in usuarios]
        
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener usuarios")
    finally:
        cursor.close()
        connection.close()


@router.get("/api/perfiles")
async def get_perfiles(user: dict = Depends(require_login)):
    """Obtener listado de perfiles"""
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT codigo_perfil, descripcion
            FROM perfil
            ORDER BY codigo_perfil
        """)
        
        perfiles = cursor.fetchall()
        
        return [{
            'codigo_perfil': row[0],
            'descripcion': row[1]
        } for row in perfiles]
        
    except Exception as e:
        print(f"Error al obtener perfiles: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener perfiles")
    finally:
        cursor.close()
        connection.close()


@router.post("/api/usuarios")
async def crear_usuario(usuario_data: UsuarioCreate, user: dict = Depends(require_login)):
    """Crear nuevo usuario - SIN BCRYPT (contraseña en texto plano)"""
    
    # Verificar permisos de administrador
    if user.get("codigo_perfil") != 1:
        raise HTTPException(status_code=403, detail="No tiene permisos para crear usuarios")
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (usuario_data.usuario,))
        existe = cursor.fetchone()[0]
        
        if existe > 0:
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        
        # Insertar usuario CON CONTRASEÑA EN TEXTO PLANO
        cursor.execute("""
            INSERT INTO usuarios (usuario, clave, nombre_usuario, fecha_registro, codigo_perfil)
            VALUES (%s, %s, %s, NOW(), %s)
            RETURNING codigo_usuario
        """, (
            usuario_data.usuario,
            usuario_data.clave,  # ← Contraseña en texto plano
            usuario_data.nombre_usuario,
            usuario_data.codigo_perfil
        ))
        
        codigo_usuario = cursor.fetchone()[0]
        connection.commit()
        
        return {
            "success": True,
            "message": "Usuario creado correctamente",
            "codigo_usuario": codigo_usuario
        }
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        print(f"Error al crear usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.put("/api/usuarios/{codigo_usuario}")
async def actualizar_usuario(
    codigo_usuario: int, 
    usuario_data: UsuarioUpdate, 
    user: dict = Depends(require_login)
):
    """Actualizar usuario existente"""
    
    # Verificar permisos de administrador
    if user.get("codigo_perfil") != 1:
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar usuarios")
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Verificar si el usuario existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE codigo_usuario = %s", (codigo_usuario,))
        existe = cursor.fetchone()[0]
        
        if existe == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar si el nuevo nombre de usuario ya existe (excepto el actual)
        cursor.execute("""
            SELECT COUNT(*) FROM usuarios 
            WHERE usuario = %s AND codigo_usuario != %s
        """, (usuario_data.usuario, codigo_usuario))
        
        existe_otro = cursor.fetchone()[0]
        
        if existe_otro > 0:
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        
        # Actualizar usuario
        cursor.execute("""
            UPDATE usuarios
            SET usuario = %s,
                nombre_usuario = %s,
                codigo_perfil = %s
            WHERE codigo_usuario = %s
        """, (
            usuario_data.usuario,
            usuario_data.nombre_usuario,
            usuario_data.codigo_perfil,
            codigo_usuario
        ))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Usuario actualizado correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        print(f"Error al actualizar usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.delete("/api/usuarios/{codigo_usuario}")
async def eliminar_usuario(codigo_usuario: int, user: dict = Depends(require_login)):
    """Eliminar usuario"""
    
    # Verificar permisos de administrador
    if user.get("codigo_perfil") != 1:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar usuarios")
    
    # No permitir eliminar el propio usuario
    if user.get("user_id") == codigo_usuario:
        raise HTTPException(status_code=400, detail="No puede eliminar su propio usuario")
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Verificar si el usuario existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE codigo_usuario = %s", (codigo_usuario,))
        existe = cursor.fetchone()[0]
        
        if existe == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar si el usuario tiene pedidos asociados
        cursor.execute("SELECT COUNT(*) FROM pedidos_enc WHERE codigo_usuario = %s", (codigo_usuario,))
        tiene_pedidos = cursor.fetchone()[0]
        
        if tiene_pedidos > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar el usuario porque tiene {tiene_pedidos} pedido(s) asociado(s)"
            )
        
        # Eliminar usuario
        cursor.execute("DELETE FROM usuarios WHERE codigo_usuario = %s", (codigo_usuario,))
        connection.commit()
        
        return {
            "success": True,
            "message": "Usuario eliminado correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        print(f"Error al eliminar usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.post("/api/usuarios/{codigo_usuario}/cambiar-clave")
async def cambiar_clave(
    codigo_usuario: int, 
    clave_data: CambiarClaveRequest, 
    user: dict = Depends(require_login)
):
    """Cambiar contraseña de un usuario - SIN BCRYPT (contraseña en texto plano)"""
    
    # Verificar permisos: administrador o el propio usuario
    if user.get("codigo_perfil") != 1 and user.get("user_id") != codigo_usuario:
        raise HTTPException(status_code=403, detail="No tiene permisos para cambiar esta contraseña")
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Verificar si el usuario existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE codigo_usuario = %s", (codigo_usuario,))
        existe = cursor.fetchone()[0]
        
        if existe == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Actualizar contraseña EN TEXTO PLANO
        cursor.execute("""
            UPDATE usuarios
            SET clave = %s
            WHERE codigo_usuario = %s
        """, (clave_data.clave, codigo_usuario))  # ← Contraseña en texto plano
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Contraseña actualizada correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        print(f"Error al cambiar contraseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al cambiar contraseña: {str(e)}")
    finally:
        cursor.close()
        connection.close()
