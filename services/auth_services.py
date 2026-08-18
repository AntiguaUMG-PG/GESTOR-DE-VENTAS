from database.db import conexion_sql

async def authenticate_user(usuario: str, clave: str) -> dict:
    """Función auxiliar para autenticar usuario"""
    print(f"Autenticando usuario: {usuario}")
    
    conn = conexion_sql()
    
    if not conn:
        print("❌ No se pudo establecer conexión a la base de datos")
        return {
            'authenticated': False,
            'message': 'Error de conexión a la base de datos. Verifique la configuración.'
        }
    
    print("✅ Conexión a base de datos establecida")
    
    try:
        cursor = conn.cursor()
        consulta_sql = """
        SELECT codigo_usuario, nombre_usuario, codigo_perfil
        FROM usuarios
        WHERE usuario = %s AND clave = %s
        """
        
        print(f"-- Ejecutando consulta para usuario: {usuario}")
        cursor.execute(consulta_sql, (usuario, clave))
        result = cursor.fetchone()
        
        print(f"-- Resultado de consulta: {result}")
        
        if result:
            user_data = {
                'authenticated': True,
                'user_id': result[0],
                'nombre_usuario': result[1],
                'codigo_perfil': result[2]
            }
            print(f"✅ Usuario autenticado: {user_data}")
            return user_data
        else:
            print("-- Usuario no encontrado o credenciales incorrectas")
            
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (usuario,))
            user_exists = cursor.fetchone()[0]
            
            if user_exists > 0:
                print("-- El usuario existe, contraseña incorrecta")
                return {
                    'authenticated': False,
                    'message': 'Contraseña incorrecta'
                }
            else:
                print("-- El usuario no existe")
                return {
                    'authenticated': False,
                    'message': 'Usuario no encontrado'
                }
            
    except Exception as e:
        print(f"-- Error en consulta de autenticación: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'authenticated': False,
            'message': f'Error en la consulta: {str(e)}'
        }
    finally:
        cursor.close()
        conn.close()