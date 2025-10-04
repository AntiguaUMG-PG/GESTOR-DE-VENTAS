from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

import pyodbc
import os
from datetime import datetime, date

app = FastAPI(title="Gestor de Pedidos", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key="Natha0908I45")


# Configuración de plantillas y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuración de seguridad
def get_current_user(request: Request) -> Optional[dict]:
    """Obtiene el usuario actual de la sesión"""
    return request.session.get("user")

def require_login(request: Request):
    """Verifica que el usuario esté autenticado"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/"}
        )
    return user

# ================================================
# MODELOS DE DATOS
# ================================================

class LoginRequest(BaseModel):
    usuario: str
    clave: str

class AuthResponse(BaseModel):
    authenticated: bool
    user_id: Optional[int] = None
    nombre_usuario: Optional[str] = None
    codigo_perfil: Optional[int] = None
    message: Optional[str] = None

class ProductResponse(BaseModel):
    Codigo: int
    Nombre: str
    Medida: Optional[str] = None
    Marca: Optional[str] = None
    Existencia: Optional[int] = 0
    Precio: float = 0.0

class DeleteProductRequest(BaseModel):
    ProductoID: int

class PedidoEncabezado(BaseModel):
    FECHA_PEDIDO: str
    CODIGO_USUARIO: int
    CODIGO_CLIENTE: int
    NOMBRE_CLIENTE: str
    NIT: str
    DIRECCION: str
    TOTAL_PEDIDO: float
    COMENTARIOS: Optional[str] = None

class PedidoDetalle(BaseModel):
    NUMERO_PEDIDO: int
    CODIGO_PRODUCTO: int
    NOMBRE_PRODUCTO: str
    UNIDAD_MEDIDA: str
    CANTIDAD: int
    PRECIO_UNITARIO: float
    TOTAL: float

# ================================================
# CONEXIÓN A BASE DE DATOS
# ================================================

def conexion_sql():
    """funcion para la configuracion de la conexión a la base de datos"""
    try:
        drivers = [
            'ODBC Driver 17 for SQL Server',
            'ODBC Driver 13 for SQL Server', 
            'SQL Server Native Client 11.0',
            'SQL Server'
        ]
        
        connection_string = None
        for driver in drivers:
            try:
                connection_string = (
                    f'DRIVER={{{driver}}};'
                    'SERVER=LENOVONATHA;'
                    'DATABASE=Gestor_Pedidos;'
                    'UID=manage;'
                    'PWD=natha91275;'
                    'Trusted_Connection=no;'
                    'Encrypt=no;'
                    'TrustServerCertificate=yes;'
                )
                print(f"Intentando conexión con driver: {driver}")
                sql_conexion = pyodbc.connect(connection_string, timeout=10)
                print(f"✅ Conexión exitosa con driver: {driver}")
                return sql_conexion
            except pyodbc.Error as e:
                print(f"❌ Falló con driver {driver}: {str(e)}")
                continue
        
        # Si llegamos aquí, ningún driver funcionó
        raise Exception("No se pudo conectar con ningún driver disponible")
        
    except Exception as error:
        print(f"❌ Error general de conexión: {str(error)}")
        print("🔍 Drivers ODBC disponibles:")
        try:
            available_drivers = pyodbc.drivers()
            for driver in available_drivers:
                print(f"   - {driver}")
        except:
            print("   No se pudieron listar los drivers")
        return None

# ================================================
# RUTAS DE FRONTEND (HTML)
# ================================================

@app.get("/")
async def get_login(request: Request):
    """Página de inicio de sesión"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/index", status_code=302)
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/index")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página Principal"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
        })

@app.get("/clientes")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página Principal"""
    return templates.TemplateResponse("clientes.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
        })

@app.get("/pedidos")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página Principal"""
    return templates.TemplateResponse("pedidos.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
        })

@app.get("/productos")
async def get_productos_page(request: Request, user: dict = Depends(require_login)):
    """Página de productos"""
    try:
        # Obtener productos directamente desde la base de datos
        productos = await get_productos_data()
        return templates.TemplateResponse("Productos.html", {
            "request": request, 
            "contenido_producto": productos,
            "usuario": user.get("nombre_usuario"),
            "perfil": user.get("codigo_perfil")
        })
    except Exception as e:
        print(f"Error al cargar productos: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request, 
            "error": "Error al cargar los productos"
        })
    
@app.get("/reporte_inventario")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página Principal"""
    return templates.TemplateResponse("reporte_inventario.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
        })

# ================================================
# RUTAS DE AUTENTICACIÓN
# ================================================

@app.post("/login_datos")
async def post_login_frontend(request: Request, nombre: str = Form(...), contrasena: str = Form(...)):
    """Procesar login desde formulario HTML"""
    print(f"-- Intento de login HTML - Usuario: '{nombre}', Contraseña length: {len(contrasena)}")
    
    try:
        # Limpiar espacios en blanco
        nombre = nombre.strip()
        contrasena = contrasena.strip()
        
        # Validar que los campos no estén vacíos
        if not nombre or not contrasena:
            print("❌ Campos vacíos después de limpiar")
            error_msg = "Por favor complete todos los campos"
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": error_msg
            })
        
        # Autenticar usuario
        print("Iniciando autenticación...")
        auth_result = await authenticate_user(nombre, contrasena)
        print(f"Resultado autenticación HTML: {auth_result}")
        
        if auth_result["authenticated"]:
            request.session["user"] = {
                "user_id": auth_result.get("user_id"),
                "nombre_usuario": auth_result.get("nombre_usuario"),
                "codigo_perfil": auth_result.get("codigo_perfil"),
                "usuario": nombre
            }
            
            # Redirigir al dashboard
            return RedirectResponse(url="/index", status_code=302)
        else:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": auth_result.get("message", "Credenciales incorrectas")
            })
            
    except Exception as e:
        print(f" Error crítico en login HTML: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Error interno del servidor. Revise los logs en la consola."
        })
    # Cerrar la sesion de usuario
@app.get("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@app.post("/api/autenticacion", response_model=AuthResponse)
async def authenticate_api(login_data: LoginRequest):
    try:
        result = await authenticate_user(login_data.usuario, login_data.clave)
        return AuthResponse(**result)
    except Exception as e:
        print(f"Error en autenticación API: {e}")
        return AuthResponse(
            authenticated=False,
            message="Error interno del servidor"
        )

async def authenticate_user(usuario: str, clave: str) -> dict:
    """Función auxiliar para autenticar usuario"""
    print(f"Autenticando usuario: {usuario}")
    
    # Probar conexión primero
    conn = conexion_sql()
    
    if not conn:
        print(" No se pudo establecer conexión a la base de datos")
        return {
            'authenticated': False,
            'message': 'Error de conexión a la base de datos. Verifique la configuración.'
        }
    
    print("✅ Conexión a base de datos establecida")
    
    try:
        cursor = conn.cursor()
        consulta_sql = """
        SELECT CODIGO_USUARIO, NOMBRE_USUARIO, CODIGO_PERFIL
        FROM USUARIOS
        WHERE USUARIO = ? AND CLAVE = ?
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
            
            # Verificar si el usuario existe
            cursor.execute("SELECT COUNT(*) FROM USUARIOS WHERE USUARIO = ?", (usuario,))
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
@app.post("/debug-login-json")
async def debug_login_json(login_data: LoginRequest):
    """Endpoint de debug para login usando JSON (para Postman/API calls)"""
    usuario = login_data.usuario
    clave = login_data.clave
    
    debug_info = {
        "input_data": {
            "usuario": usuario,
            "clave_length": len(clave),
            "usuario_length": len(usuario)
        },
        "steps": []
    }
    
    conn = conexion_sql()
    if not conn:
        debug_info["error"] = "No connection to database"
        return JSONResponse(content=debug_info)
    
    try:
        cursor = conn.cursor()
        debug_info["steps"].append("✅ Conexión establecida")
        
        # Paso 1: Verificar si el usuario existe (sin importar la clave)
        cursor.execute("SELECT CODIGO_USUARIO, USUARIO, NOMBRE_USUARIO, CODIGO_PERFIL FROM USUARIOS WHERE USUARIO = ?", (usuario,))
        user_data = cursor.fetchone()
        
        if user_data:
            debug_info["steps"].append("✅ Usuario encontrado en base de datos")
            debug_info["user_found"] = {
                "codigo_usuario": user_data[0],
                "usuario": user_data[1],
                "nombre_usuario": user_data[2],
                "codigo_perfil": user_data[3]
            }
            
            # Paso 2: Verificar con usuario y clave
            cursor.execute("""
                SELECT CODIGO_USUARIO, USUARIO, NOMBRE_USUARIO, CODIGO_PERFIL, CLAVE
                FROM USUARIOS 
                WHERE USUARIO = ? AND CLAVE = ?
            """, (usuario, clave))
            auth_result = cursor.fetchone()
            
            if auth_result:
                debug_info["steps"].append("✅ Autenticación exitosa")
                debug_info["auth_success"] = True
                debug_info["final_result"] = {
                    "codigo_usuario": auth_result[0],
                    "usuario": auth_result[1],
                    "nombre_usuario": auth_result[2],
                    "codigo_perfil": auth_result[3]
                }
            else:
                debug_info["steps"].append("❌ Credenciales incorrectas")
                debug_info["auth_success"] = False
                
                # Verificar la clave almacenada (solo longitud por seguridad)
                cursor.execute("SELECT CLAVE FROM USUARIOS WHERE USUARIO = ?", (usuario,))
                stored_password = cursor.fetchone()[0]
                debug_info["password_comparison"] = {
                    "input_length": len(clave),
                    "stored_length": len(stored_password),
                    "match": clave == stored_password,
                    "input_preview": clave[:3] + "..." if len(clave) > 3 else clave,
                    "stored_preview": stored_password[:3] + "..." if len(stored_password) > 3 else stored_password
                }
        else:
            debug_info["steps"].append("❌ Usuario no encontrado")
            debug_info["auth_success"] = False
            
    except Exception as e:
        debug_info["error"] = str(e)
        debug_info["steps"].append(f"💥 Error: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()
    
    return JSONResponse(content=debug_info)

@app.post("/debug-login")
async def debug_login(usuario: str = Form(...), clave: str = Form(...)):
    """Endpoint de debug para el login - con información detallada"""
    debug_info = {
        "input_data": {
            "usuario": usuario,
            "clave_length": len(clave),
            "usuario_length": len(usuario)
        },
        "steps": []
    }
    
    conn = conexion_sql()
    if not conn:
        debug_info["error"] = "No connection to database"
        return JSONResponse(content=debug_info)
    
    try:
        cursor = conn.cursor()
        debug_info["steps"].append("✅ Conexión establecida")
        
        # Paso 1: Verificar si el usuario existe (sin importar la clave)
        cursor.execute("SELECT CODIGO_USUARIO, USUARIO, NOMBRE_USUARIO, CODIGO_PERFIL FROM USUARIOS WHERE USUARIO = ?", (usuario,))
        user_data = cursor.fetchone()
        
        if user_data:
            debug_info["steps"].append("✅ Usuario encontrado en base de datos")
            debug_info["user_found"] = {
                "codigo_usuario": user_data[0],
                "usuario": user_data[1],
                "nombre_usuario": user_data[2],
                "codigo_perfil": user_data[3]
            }
            
            # Paso 2: Verificar con usuario y clave
            cursor.execute("""
                SELECT CODIGO_USUARIO, USUARIO, NOMBRE_USUARIO, CODIGO_PERFIL, CLAVE
                FROM USUARIOS 
                WHERE USUARIO = ? AND CLAVE = ?
            """, (usuario, clave))
            auth_result = cursor.fetchone()
            
            if auth_result:
                debug_info["steps"].append("✅ Autenticación exitosa")
                debug_info["auth_success"] = True
                debug_info["final_result"] = {
                    "codigo_usuario": auth_result[0],
                    "usuario": auth_result[1],
                    "nombre_usuario": auth_result[2],
                    "codigo_perfil": auth_result[3]
                }
            else:
                debug_info["steps"].append("❌ Credenciales incorrectas")
                debug_info["auth_success"] = False
                
                # Verificar la clave almacenada (solo longitud por seguridad)
                cursor.execute("SELECT CLAVE FROM USUARIOS WHERE USUARIO = ?", (usuario,))
                stored_password = cursor.fetchone()[0]
                debug_info["password_comparison"] = {
                    "input_length": len(clave),
                    "stored_length": len(stored_password),
                    "match": clave == stored_password
                }
        else:
            debug_info["steps"].append("❌ Usuario no encontrado")
            debug_info["auth_success"] = False
            
    except Exception as e:
        debug_info["error"] = str(e)
        debug_info["steps"].append(f"💥 Error: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()
    
    return JSONResponse(content=debug_info)

# ================================================
# RUTAS DE CLIENTES
# ================================================

@app.get("/listado_clientes")
async def get_clientes_data(user: dict = Depends(require_login)):
    """API endpoint para obtener listado de clientes"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                C.CODIGO_CLIENTE as Codigo,
                C.NOMBRE_CLIENTE as Nombre,
                C.NOMBRE_NEGOCIO as Nombre_Negocio,
                C.NIT,
                C.TELEFONO as Telefono,
                C.DIRECCION as Direccion,
                M.NOMBRE_MUNICIPIO as Municipio,
                D.NOMBRE_DEPARTAMENTO as Departamento,
                NP.DESCRIPCION_NIVEL as Nivel_Precio,
                ISNULL(C.SALDO, 0) as Saldo
            FROM CLIENTES C
            LEFT JOIN MUNICIPIOS M ON C.MUNICIPIO = M.MUNICIPIO
            LEFT JOIN DEPARTAMENTOS D ON C.DEPARTAMENTO = D.DEPARTAMENTO
            LEFT JOIN NIVEL_PRECIO NP ON C.NIVEL_PRECIO = NP.NIVEL_PRECIO
            ORDER BY C.NOMBRE_CLIENTE
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

@app.post("/insertar_cliente")
async def insertar_cliente(cliente_data: dict):
    """Insertar nuevo cliente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO CLIENTES (
                NOMBRE_CLIENTE, NOMBRE_NEGOCIO, NIT, TELEFONO, 
                DIRECCION, MUNICIPIO, DEPARTAMENTO, NIVEL_PRECIO, SALDO
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0)
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

@app.put("/actualizar_cliente")
async def actualizar_cliente(cliente_data: dict):
    """Actualizacion de cliente existente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE CLIENTES SET
                NOMBRE_CLIENTE = ?, NOMBRE_NEGOCIO = ?, NIT = ?, TELEFONO = ?,
                DIRECCION = ?, MUNICIPIO = ?, DEPARTAMENTO = ?, NIVEL_PRECIO = ?
            WHERE CODIGO_CLIENTE = ?
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

@app.delete("/eliminar_cliente/{codigo_cliente}")
async def eliminar_cliente(codigo_cliente: int):
    """Eliminar cliente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM CLIENTES WHERE CODIGO_CLIENTE = ?", (codigo_cliente,))
        
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

# ================================================
# RUTAS PARA PEDIDOS
# ================================================

@app.get("/listado_pedidos")
async def get_pedidos_data(user: dict = Depends(require_login)):
    """API endpoint para obtener listado de pedidos"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                P.NUMERO_PEDIDO,
                P.FECHA,
                P.NOMBRE_CLIENTE,
                P.NIT,
                P.DIRECCION,
                ISNULL(P.TOTAL_DOCUMENTO, 0) as TOTAL_DOCUMENTO,
                P.ESTADO
            FROM PEDIDOS_ENC P
            ORDER BY P.NUMERO_PEDIDO DESC
        """)
        pedidos = cursor.fetchall()
        
        json_data = [{
            'NUMERO_PEDIDO': row[0],
            'FECHA': row[1].strftime('%d/%m/%Y %H:%M:%S') if row[1] else '',
            'NOMBRE_CLIENTE': row[2],
            'NIT': row[3],
            'DIRECCION': row[4],
            'TOTAL_DOCUMENTO': float(row[5]) if row[5] is not None else 0.0,
            'ESTADO': row[6]
        } for row in pedidos]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener pedidos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener pedidos")
    finally:
        cursor.close()
        connection.close()

@app.get("/numero_pedido")
async def get_numero_pedido(user: dict = Depends(require_login)):
    connection = conexion_sql()
    
    if not connection:
        return {"ultimo_numero_pedido": 1}
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT ISNULL(MAX(NUMERO_PEDIDO), 0) + 1 FROM PEDIDOS_ENC")
        siguiente_numero = cursor.fetchone()[0]
        
        return {"ultimo_numero_pedido": siguiente_numero}
        
    except Exception as e:
        print(f"Error al obtener número de pedido: {e}")
        return {"ultimo_numero_pedido": 1}
    finally:
        cursor.close()
        connection.close()

@app.get("/buscar_productos")
async def buscar_productos(term: str):
    connection = conexion_sql()
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT TOP 20
                P.CODIGO_PRODUCTO as Codigo,
                P.NOMBRE_PRODUCTO as Descripcion_producto,
                P.UNIDAD_MEDIDA as Presentacion,
                ISNULL(PR.PRECIO, 0) as Precio,
                ISNULL(P.EXISTENCIA, 0) as EXISTENCIA
            FROM PRODUCTOS P
            LEFT JOIN PRECIOS PR ON P.CODIGO_PRODUCTO = PR.CODIGO_PRODUCTO AND PR.NIVEL_PRECIO = 1
            WHERE P.NOMBRE_PRODUCTO LIKE ?
            ORDER BY P.NOMBRE_PRODUCTO
        """, (f"%{term}%",))
        
        productos = cursor.fetchall()
        
        json_data = [{
            'Codigo': row[0],
            'Descripcion_producto': row[1],
            'Presentacion': row[2],
            'Precio': float(row[3]) if row[3] is not None else 0.0,
            'EXISTENCIA': int(row[4]) if row[4] is not None else 0
        } for row in productos]
        
        return json_data
        
    except Exception as e:
        print(f"Error al buscar productos: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

@app.post("/verificar_stock")
async def verificar_stock(stock_data: dict):
    connection = conexion_sql()
    
    if not connection:
        return {"success": False, "message": "Error de conexión"}
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT EXISTENCIA 
            FROM PRODUCTOS 
            WHERE CODIGO_PRODUCTO = ?
        """, (stock_data.get('codigo_producto'),))
        
        result = cursor.fetchone()
        
        if result:
            existencia = int(result[0]) if result[0] else 0
            cantidad_solicitada = int(stock_data.get('cantidad', 0))
            
            if cantidad_solicitada > existencia:
                return {
                    "success": False,
                    "message": f"Stock insuficiente. Disponible: {existencia}"
                }
            else:
                return {"success": True, "existencia": existencia}
        else:
            return {"success": False, "message": "Producto no encontrado"}
            
    except Exception as e:
        print(f"Error al verificar stock: {e}")
        return {"success": False, "message": "Error al verificar stock"}
    finally:
        cursor.close()
        connection.close()

@app.post("/insertar_pedido_enc")
async def insertar_pedido_enc(pedido_data: dict):
    """Insertar el encabezado de pedido"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Convertir fecha de DD/MM/YYYY a formato datetime
        fecha_str = pedido_data.get('FECHA_PEDIDO')
        if fecha_str and '/' in fecha_str:
            fecha_pedido = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
        else:
            fecha_pedido = datetime.now() 
        
        cursor.execute("""
            INSERT INTO PEDIDOS_ENC (
                FECHA, CODIGO_USUARIO, CODIGO_CLIENTE, NOMBRE_CLIENTE,
                NIT, DIRECCION, TOTAL_DOCUMENTO, ESTADO, COMENTARIOS
            )
            OUTPUT INSERTED.NUMERO_PEDIDO
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ABIERTO', ?)
        """, (
            fecha_pedido,
            pedido_data.get('CODIGO_USUARIO'),
            pedido_data.get('CODIGO_CLIENTE'),
            pedido_data.get('NOMBRE_CLIENTE'),
            pedido_data.get('NIT'),
            pedido_data.get('DIRECCION'),
            pedido_data.get('TOTAL_PEDIDO'),
            pedido_data.get('COMENTARIOS')
        ))
        
        numero_pedido = cursor.fetchone()[0]
        connection.commit()
        
        return {"success": True, "numero_pedido": numero_pedido}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al insertar pedido: {e}")
        raise HTTPException(status_code=500, detail=f"Error al insertar pedido: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.post("/insertar_pedido_det")
async def insertar_pedido_det(detalles_data: List[Dict[str, Any]]):
    """Insertar los detalles de pedido"""
    
    
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        for i, detalle in enumerate(detalles_data):
            print(f"Insertando detalle {i+1}: {detalle}")
            
            cursor.execute("""
                INSERT INTO PEDIDOS_DET (
                    NUMERO_PEDIDO, CODIGO_PRODUCTO, NOMBRE_PRODUCTO,
                    UNIDAD_MEDIDA, CANTIDAD, PRECIO_UNITARIO, TOTAL_LINEA
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                detalle.get('NUMERO_PEDIDO'),
                str(detalle.get('CODIGO_PRODUCTO')),  # Convertir a string
                detalle.get('NOMBRE_PRODUCTO'),
                detalle.get('UNIDAD_MEDIDA'),
                int(detalle.get('CANTIDAD', 0)),
                float(detalle.get('PRECIO_UNITARIO', 0)),
                float(detalle.get('TOTAL', 0))
            ))
        
        connection.commit()
        print("✅ Detalles insertados exitosamente")
        return {"success": True, "message": "Detalles insertados correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error al insertar detalles: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al insertar detalles: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.post("/actualizar_stock")
async def actualizar_stock(productos_data: List[Dict[str, Any]]):
    """Actualizar stock de productos"""

    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        for producto in productos_data:
            codigo = producto.get('CODIGO_PRODUCTO')
            cantidad = producto.get('CANTIDAD')
            
            print(f"Actualizando producto {codigo}: restando {cantidad} unidades")
            
            cursor.execute("""
                UPDATE PRODUCTOS 
                SET EXISTENCIA = EXISTENCIA - ?
                WHERE CODIGO_PRODUCTO = ?
            """, (
                float(cantidad),
                int(codigo)
            ))
            
            # Verificar el stock actualizado
            cursor.execute("SELECT EXISTENCIA FROM PRODUCTOS WHERE CODIGO_PRODUCTO = ?", (int(codigo),))
            nuevo_stock = cursor.fetchone()
            print(f"Nuevo stock del producto {codigo}: {nuevo_stock[0] if nuevo_stock else 'N/A'}")
        
        connection.commit()
        print("✅ Stock actualizado exitosamente")
        return {"success": True, "message": "Stock actualizado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error al actualizar stock: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al actualizar stock: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.get("/detalle_pedido/{numero_pedido}")
async def get_detalle_pedido(numero_pedido: int):
    """Obtener detalles de un pedido específico"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                CODIGO_PRODUCTO,
                NOMBRE_PRODUCTO,
                UNIDAD_MEDIDA,
                CANTIDAD,
                PRECIO_UNITARIO,
                TOTAL_LINEA
            FROM PEDIDOS_DET
            WHERE NUMERO_PEDIDO = ?
            ORDER BY NUMERO_LINEA
        """, (numero_pedido,))
        
        detalles = cursor.fetchall()
        
        json_data = [{
            'CODIGO_PRODUCTO': row[0],
            'NOMBRE_PRODUCTO': row[1],
            'UNIDAD_MEDIDA': row[2],
            'CANTIDAD': row[3],
            'PRECIO_UNITARIO': float(row[4]),
            'TOTAL_LINEA': float(row[5])
        } for row in detalles]
        
        return json_data
        
    except Exception as e:
        print(f"Error al obtener detalle del pedido: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener detalle del pedido")
    finally:
        cursor.close()
        connection.close()


@app.get("/imprimir_pedido/{numero_pedido}")
async def imprimir_pedido(request: Request, numero_pedido: int):
    """Generar vista PDF del pedido"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Obtener encabezado del pedido
        cursor.execute("""
            SELECT 
                NUMERO_PEDIDO,
                FECHA,
                NOMBRE_CLIENTE,
                NIT,
                DIRECCION,
                TOTAL_DOCUMENTO,
                ESTADO,
                COMENTARIOS
            FROM PEDIDOS_ENC
            WHERE NUMERO_PEDIDO = ?
        """, (numero_pedido,))
        
        encabezado = cursor.fetchone()
        
        if not encabezado:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Obtener detalles del pedido
        cursor.execute("""
            SELECT 
                CODIGO_PRODUCTO,
                NOMBRE_PRODUCTO,
                UNIDAD_MEDIDA,
                CANTIDAD,
                PRECIO_UNITARIO,
                TOTAL_LINEA
            FROM PEDIDOS_DET
            WHERE NUMERO_PEDIDO = ?
            ORDER BY NUMERO_LINEA
        """, (numero_pedido,))
        
        detalles = cursor.fetchall()
        
        # Formatear fecha
        fecha_pedido = encabezado[1].strftime('%d/%m/%Y %H:%M:%S Hrs') if encabezado[1] else ''
        
        # Prepara datos JSON para la plantilla
        pedido_data = {
            'numero': encabezado[0],
            'fecha': fecha_pedido,
            'cliente': encabezado[2],
            'nit': encabezado[3],
            'direccion': encabezado[4],
            'total': float(encabezado[5]) if encabezado[5] else 0.0,
            'estado': encabezado[6],
            'comentarios': encabezado[7] or ''
        }
        
        # Formatear detalles
        detalles_lista = [{
            'codigo': row[0],
            'producto': row[1],
            'unidad': row[2],
            'cantidad': float(row[3]) if row[3] else 0,
            'precio': float(row[4]) if row[4] else 0.0,
            'total': float(row[5]) if row[5] else 0.0
        } for row in detalles]
        
        # Obtener fecha y hora actual para impresión
        from datetime import datetime
        fecha_impresion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        return templates.TemplateResponse("pedido_pdf.html", {
            "request": request,
            "pedido": pedido_data,
            "detalles": detalles_lista,
            "fecha_impresion": fecha_impresion
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")
    finally:
        cursor.close()
        connection.close()

# ================================================
# RUTAS PARA REPORTE DE INVENTARIO Y PEDIDOS
# ================================================

@app.get("/reporte/inventario-vs-pedidos")
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
        
        # Si no se proporciona fecha, usar la fecha actual
        if not fecha:
            from datetime import date
            fecha = date.today().strftime('%Y-%m-%d')
        
        # Consulta para obtener productos vendidos en el día y comparar con inventario
        cursor.execute("""
            SELECT 
                P.CODIGO_PRODUCTO,
                P.NOMBRE_PRODUCTO,
                P.UNIDAD_MEDIDA,
                M.NOMBRE_MARCA,
                ISNULL(P.EXISTENCIA, 0) AS INVENTARIO_ACTUAL,
                V.CANTIDAD_VENDIDA,
                ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0) AS INVENTARIO_RESULTANTE,
                CASE 
                    WHEN (ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0)) < 0
                    THEN ABS(ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0))
                    ELSE 0 
                END AS FALTANTE,
                PR.PRECIO
            FROM PRODUCTOS P
            INNER JOIN MARCAS M ON P.MARCA = M.CODIGO_MARCA
            LEFT JOIN PRECIOS PR ON P.CODIGO_PRODUCTO = PR.CODIGO_PRODUCTO
            -- tabla derivada con ventas agregadas SOLO para la fecha dada
            INNER JOIN (
                SELECT 
                    PD.CODIGO_PRODUCTO,
                    ISNULL(SUM(PD.CANTIDAD), 0) AS CANTIDAD_VENDIDA
                FROM PEDIDOS_DET PD
                INNER JOIN PEDIDOS_ENC PE ON PD.NUMERO_PEDIDO = PE.NUMERO_PEDIDO
                WHERE CONVERT(DATE, PE.FECHA) = ?
                GROUP BY PD.CODIGO_PRODUCTO
            ) AS V ON P.CODIGO_PRODUCTO = V.CODIGO_PRODUCTO
            ORDER BY 
                CASE WHEN (ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0)) < 0 THEN 0 ELSE 1 END,
                P.NOMBRE_PRODUCTO
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

@app.get("/reporte/resumen-inventario")
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
            from datetime import date
            fecha = date.today().strftime('%Y-%m-%d')

        # Subconsulta: total vendido por producto x fecha indicada
        ventas_query = """
            SELECT 
                PD.CODIGO_PRODUCTO,
                ISNULL(SUM(PD.CANTIDAD), 0) AS CANTIDAD_VENDIDA
            FROM PEDIDOS_DET PD
            INNER JOIN PEDIDOS_ENC PE ON PD.NUMERO_PEDIDO = PE.NUMERO_PEDIDO
            WHERE CONVERT(DATE, PE.FECHA) = ?
            GROUP BY PD.CODIGO_PRODUCTO
        """

        # Total de productos vendidos en la fecha seleccionada
        cursor.execute(f"SELECT COUNT(*) FROM ({ventas_query}) AS V", (fecha,))
        total_productos_vendidos = cursor.fetchone()[0]

        # Productos con inventario insuficiente
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM PRODUCTOS P
            INNER JOIN ({ventas_query}) AS V ON P.CODIGO_PRODUCTO = V.CODIGO_PRODUCTO
            WHERE (ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0)) < 0
        """, (fecha,))
        productos_insuficientes = cursor.fetchone()[0]

        # Total de unidades faltantes
        cursor.execute(f"""
            SELECT 
                ISNULL(SUM(
                    CASE 
                        WHEN (ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0)) < 0 
                        THEN ABS(ISNULL(P.EXISTENCIA, 0) - ISNULL(V.CANTIDAD_VENDIDA, 0))
                        ELSE 0 
                    END
                ), 0)
            FROM PRODUCTOS P
            INNER JOIN ({ventas_query}) AS V ON P.CODIGO_PRODUCTO = V.CODIGO_PRODUCTO
        """, (fecha,))
        total_unidades_faltantes = cursor.fetchone()[0] or 0

        # Total de pedidos del día
        cursor.execute("""
            SELECT COUNT(*) 
            FROM PEDIDOS_ENC 
            WHERE CONVERT(DATE, FECHA) = ?
        """, (fecha,))
        total_pedidos = cursor.fetchone()[0]

        # Armar respuesta
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


@app.get("/reporte/productos-criticos")
async def get_productos_criticos(limite: int = 10):
    """
    Obtener productos con inventario más bajo o crítico
    """
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        cursor.execute(f"""
            SELECT TOP {limite}
                P.CODIGO_PRODUCTO,
                P.NOMBRE_PRODUCTO,
                P.UNIDAD_MEDIDA,
                M.NOMBRE_MARCA,
                ISNULL(P.EXISTENCIA, 0) as EXISTENCIA
            FROM PRODUCTOS P
            INNER JOIN MARCAS M ON P.MARCA = M.CODIGO_MARCA
            WHERE ISNULL(P.EXISTENCIA, 0) <= 10
            ORDER BY P.EXISTENCIA ASC
        """)
        
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

@app.get("/imprimir_reporte_inventario")
async def imprimir_reporte_inventario(request: Request, fecha: str = None):
    """
    Genera la vista HTML para imprimir el reporte de inventario del día seleccionado
    """

    # Usar fecha actual si no se proporciona
    if not fecha:
        fecha = date.today().strftime('%Y-%m-%d')
    
    connection = conexion_sql()
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()

        # ------------------- Resumen de inventario
        cursor.execute("""
        WITH ProductosVendidos AS (
            SELECT
                P.CODIGO_PRODUCTO,
                P.NOMBRE_PRODUCTO,
                P.UNIDAD_MEDIDA,
                P.MARCA,
                ISNULL(P.EXISTENCIA,0) AS EXISTENCIA,
                ISNULL(SUM(PD.CANTIDAD),0) AS CANTIDAD_VENDIDA
            FROM PRODUCTOS P
            LEFT JOIN PEDIDOS_DET PD ON P.CODIGO_PRODUCTO = PD.CODIGO_PRODUCTO
            LEFT JOIN PEDIDOS_ENC PE ON PD.NUMERO_PEDIDO = PE.NUMERO_PEDIDO
                AND CONVERT(DATE, PE.FECHA) = ?
            GROUP BY P.CODIGO_PRODUCTO, P.NOMBRE_PRODUCTO, P.UNIDAD_MEDIDA, P.MARCA, P.EXISTENCIA
        )
        SELECT
            COUNT(*) AS total_productos_vendidos,
            SUM(CASE WHEN EXISTENCIA - CANTIDAD_VENDIDA >= 0 THEN 1 ELSE 0 END) AS productos_suficientes,
            SUM(CASE WHEN EXISTENCIA - CANTIDAD_VENDIDA < 0 THEN 1 ELSE 0 END) AS productos_insuficientes,
            SUM(CASE WHEN EXISTENCIA - CANTIDAD_VENDIDA < 0 THEN ABS(EXISTENCIA - CANTIDAD_VENDIDA) ELSE 0 END) AS total_unidades_faltantes
        FROM ProductosVendidos
        """, (fecha,))
        
        resumen = cursor.fetchone()
        resumen_data = {
            'total_productos_vendidos': resumen[0],
            'productos_con_inventario_suficiente': resumen[1],
            'productos_con_inventario_insuficiente': resumen[2],
            'total_unidades_faltantes': int(resumen[3])
        }

        # ------------------- Detalle
        cursor.execute("""
        WITH ProductosVendidos AS (
            SELECT
                P.CODIGO_PRODUCTO,
                P.NOMBRE_PRODUCTO,
                P.UNIDAD_MEDIDA,
                M.NOMBRE_MARCA AS MARCA,
                ISNULL(P.EXISTENCIA,0) AS INVENTARIO_ACTUAL,
                SUM(PD.CANTIDAD) AS CANTIDAD_VENDIDA
            FROM PRODUCTOS P
            INNER JOIN MARCAS M ON P.MARCA = M.CODIGO_MARCA
            INNER JOIN PEDIDOS_DET PD ON P.CODIGO_PRODUCTO = PD.CODIGO_PRODUCTO
            INNER JOIN PEDIDOS_ENC PE ON PD.NUMERO_PEDIDO = PE.NUMERO_PEDIDO
                AND CONVERT(DATE, PE.FECHA) = ?
            GROUP BY P.CODIGO_PRODUCTO, P.NOMBRE_PRODUCTO, P.UNIDAD_MEDIDA, M.NOMBRE_MARCA, P.EXISTENCIA
        )
        SELECT
            CODIGO_PRODUCTO,
            NOMBRE_PRODUCTO,
            UNIDAD_MEDIDA,
            MARCA,
            INVENTARIO_ACTUAL,
            CANTIDAD_VENDIDA,
            INVENTARIO_ACTUAL - CANTIDAD_VENDIDA AS INVENTARIO_RESULTANTE,
            CASE WHEN INVENTARIO_ACTUAL - CANTIDAD_VENDIDA < 0 THEN ABS(INVENTARIO_ACTUAL - CANTIDAD_VENDIDA) ELSE 0 END AS FALTANTE
        FROM ProductosVendidos
        ORDER BY FALTANTE DESC, NOMBRE_PRODUCTO
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


        # Renderizar template del reporte
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
# ================================================
# RUTAS DE PRODUCTOS
# ================================================

@app.get("/api/productos", response_model=List[ProductResponse])
async def get_productos_api(user: dict = Depends(require_login)):
    """API endpoint para obtener productos (JSON)"""
    try:
        productos = await get_productos_data()
        return productos
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener productos")

@app.get("/ProductsAndPrices")
async def get_productos_frontend(request: Request):
    """Endpoint para obtener productos desde el frontend"""
    try:
        productos = await get_productos_data()
        return templates.TemplateResponse("Products.html", {
            "request": request, 
            "contenido_producto": productos
        })
    except Exception as e:
        print(f"Error al cargar productos: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Error al cargar los productos"
        })

@app.post("/Producto_datos_actualizados")
async def post_productos_actualizados(request: Request):
    """Endpoint POST para actualizar vista de productos"""
    try:
        productos = await get_productos_data()
        return templates.TemplateResponse("Products.html", {
            "request": request, 
            "contenido_producto": productos
        })
    except Exception as e:
        print(f"Error al actualizar productos: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Error al actualizar los productos"
        })

# ================================================
# RUTAS DE PRODUCTOS
# ================================================




@app.get("/listado_productos")
async def get_productos_listado(user: dict = Depends(require_login)):
    """API endpoint para obtener listado completo de productos (alias)"""
    try:
        productos = await get_productos_data()
        return productos
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener productos")

@app.post("/api/productos/insertar")
async def insertar_producto(producto_data: dict):
    """Insertar nuevo producto"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO PRODUCTOS (NOMBRE_PRODUCTO, UNIDAD_MEDIDA, MARCA, EXISTENCIA)
            OUTPUT INSERTED.CODIGO_PRODUCTO
            VALUES (?, ?, ?, ?)
        """, (
            producto_data.get('NOMBRE_PRODUCTO'),
            producto_data.get('UNIDAD_MEDIDA'),
            int(producto_data.get('MARCA')),
            float(producto_data.get('EXISTENCIA', 0))
        ))
        
        codigo_producto = cursor.fetchone()[0]
        
        # Insertar precio si se proporcionó
        precio = producto_data.get('PRECIO')
        if precio and float(precio) > 0:
            cursor.execute("""
                INSERT INTO PRECIOS (NIVEL_PRECIO, CODIGO_PRODUCTO, PRECIO)
                VALUES (1, ?, ?)
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

@app.put("/api/productos/actualizar")
async def actualizar_producto(producto_data: dict):
    """Actualizar producto existente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Actualizar producto
        cursor.execute("""
            UPDATE PRODUCTOS SET
                NOMBRE_PRODUCTO = ?, EXISTENCIA = ?, UNIDAD_MEDIDA = ?
            WHERE CODIGO_PRODUCTO = ?
        """, (
            producto_data.get('NOMBRE_PRODUCTO'),
            float(producto_data.get('EXISTENCIA', 0)),
            producto_data.get('UNIDAD_MEDIDA'),
            int(producto_data.get('Codigo'))
        ))
        
        # Actualizar precio
        precio = producto_data.get('PRECIO')
        if precio:
            cursor.execute("""
                UPDATE PRECIOS SET PRECIO = ?
                WHERE CODIGO_PRODUCTO = ? AND NIVEL_PRECIO = 1
            """, (float(precio), int(producto_data.get('Codigo'))))
        
        connection.commit()
        return {"success": True, "message": "Producto actualizado correctamente"}
        
    except Exception as e:
        connection.rollback()
        print(f"Error al actualizar producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar producto: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.delete("/api/productos/{codigo_producto}")
async def eliminar_producto(codigo_producto: int):
    """Eliminar producto"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        # Eliminar precios primero (foreign key)
        cursor.execute("DELETE FROM PRECIOS WHERE CODIGO_PRODUCTO = ?", (codigo_producto,))
        
        # Eliminar producto
        cursor.execute("DELETE FROM PRODUCTOS WHERE CODIGO_PRODUCTO = ?", (codigo_producto,))
        
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

@app.get("/api/marcas")
async def get_marcas(user: dict = Depends(require_login)):
    """Obtener listado de marcas para formularios"""
    connection = conexion_sql()
    
    if not connection:
        # Datos ficticios como fallback basados en tu base de datos
        return [
            {"id": 1, "nombre": "ADAMS"},
            {"id": 2, "nombre": "BEST"},
            {"id": 3, "nombre": "MONDELEZ"},
            {"id": 4, "nombre": "MARINELA"},
            {"id": 5, "nombre": "BIMBO"},
            {"id": 6, "nombre": "COLOMBINA"},
            {"id": 59, "nombre": "SIN MARCA"}
        ]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT CODIGO_MARCA as id, NOMBRE_MARCA as nombre FROM MARCAS ORDER BY NOMBRE_MARCA")
        marcas = cursor.fetchall()
        
        return [{
            'id': row[0],
            'nombre': row[1]
        } for row in marcas]
        
    except Exception as e:
        print(f"Error al obtener marcas: {e}")
        return [
            {"id": 1, "nombre": "ADAMS"},
            {"id": 2, "nombre": "BEST"},
            {"id": 3, "nombre": "MONDELEZ"},
            {"id": 4, "nombre": "MARINELA"},
            {"id": 5, "nombre": "BIMBO"},
            {"id": 6, "nombre": "COLOMBINA"},
            {"id": 59, "nombre": "SIN MARCA"}
        ]
    finally:
        cursor.close()
        connection.close()

@app.get("/ProductsAndPrices")
async def get_productos_frontend(request: Request):
    """Endpoint para obtener productos desde el frontend (HTML)"""
    try:
        productos = await get_productos_data()
        return templates.TemplateResponse("Products.html", {
            "request": request, 
            "contenido_producto": productos
        })
    except Exception as e:
        print(f"Error al cargar productos: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Error al cargar los productos"
        })

async def get_productos_data() -> List[dict]:
    """Función auxiliar para obtener datos de productos"""
    connection = conexion_sql()
    
    if not connection:
        raise Exception("No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                P.CODIGO_PRODUCTO, 
                P.NOMBRE_PRODUCTO, 
                P.UNIDAD_MEDIDA, 
                M.NOMBRE_MARCA, 
                P.EXISTENCIA,
                PR.PRECIO
            FROM 
                PRODUCTOS P
                INNER JOIN MARCAS M ON P.MARCA = M.CODIGO_MARCA
                LEFT JOIN PRECIOS PR ON P.CODIGO_PRODUCTO = PR.CODIGO_PRODUCTO
                LEFT JOIN NIVEL_PRECIO NP ON PR.NIVEL_PRECIO = NP.NIVEL_PRECIO
        """)
        contenido_producto = cursor.fetchall()
        
        # Convertir a formato JSON
        json_data = [{
            'Codigo': row[0],
            'Nombre': row[1],
            'Medida': row[2],
            'Marca': row[3],
            'Existencia': row[4],
            'Precio': row[5] if row[5] is not None else 0.0
        } for row in contenido_producto]
        
        return json_data
        
    except Exception as e:
        print(f"Error en consulta de productos: {e}")
        raise Exception("Error al consultar productos")
    finally:
        cursor.close()
        connection.close()

# ================================================
# RUTAS DE ELIMINACIÓN
# ================================================

@app.post("/api/producto/eliminar")
async def eliminar_producto(delete_request: DeleteProductRequest):
    """API endpoint para eliminar producto"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        # Corregir la consulta SQL para SQL Server (no Oracle)
        cursor.execute("DELETE FROM PRODUCTOS WHERE CODIGO_PRODUCTO = ?", (delete_request.ProductoID,))
        
        if cursor.rowcount > 0:
            connection.commit()
            return {"success": True, "message": "Producto eliminado correctamente"}
        else:
            connection.rollback()
            return {"success": False, "error": "No se encontró el producto a eliminar"}
            
    except Exception as e:
        connection.rollback()
        print(f"Error al eliminar el producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar el producto: {str(e)}")
    finally:
        cursor.close()
        connection.close()

# ================================================
# RUTAS DE CATÁLOGOS
# ================================================

@app.get("/listado_municipios")
async def get_municipios(user: dict = Depends(require_login)):
    """Obtener listado de municipios"""
    connection = conexion_sql()
    
    if not connection:
        return [{"id": 112, "nombre": "SAN LUCAS SACATEPEQUEZ"}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT MUNICIPIO as id, NOMBRE_MUNICIPIO as nombre FROM MUNICIPIOS ORDER BY NOMBRE_MUNICIPIO")
        municipios = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in municipios]
        
    except Exception as e:
        print(f"Error al obtener municipios: {e}")
        return [{"id": 112, "nombre": "SAN LUCAS SACATEPEQUEZ"}]
    finally:
        cursor.close()
        connection.close()

@app.get("/listado_departamentos")
async def get_departamentos(user: dict = Depends(require_login)):
    """Obtener listado de departamentos"""
    connection = conexion_sql()
    
    if not connection:
        return [{"id": 16, "nombre": "SACATEPEQUEZ"}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DEPARTAMENTO as id, NOMBRE_DEPARTAMENTO as nombre FROM DEPARTAMENTOS ORDER BY NOMBRE_DEPARTAMENTO")
        departamentos = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in departamentos]
        
    except Exception as e:
        print(f"Error al obtener departamentos: {e}")
        return [{"id": 16, "nombre": "SACATEPEQUEZ"}]
    finally:
        cursor.close()
        connection.close()

@app.get("/listado_niveles_precio")
async def get_niveles_precio(user: dict = Depends(require_login)):
    """Obtener listado de niveles de precio"""
    connection = conexion_sql()
    
    if not connection:
        return [{"id": 1, "nombre": "TIENDA_BARRIO"}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT NIVEL_PRECIO as id, DESCRIPCION_NIVEL as nombre FROM NIVEL_PRECIO ORDER BY NIVEL_PRECIO")
        niveles = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in niveles]
        
    except Exception as e:
        print(f"Error al obtener niveles de precio: {e}")
        return [{"id": 1, "nombre": "TIENDA_BARRIO"}]
    finally:
        if connection:
            cursor.close()
            connection.close()

# ================================================
# RUTAS PARA RESUMENES DEL DASHBOARD
# ================================================

@app.get("/api/dashboard/totales")
async def get_dashboard_totales(user: dict = Depends(require_login)):
    """Obtener totales para el dashboard"""
    connection = conexion_sql()
    
    if not connection:
        return {"clientes": 85, "pedidos": 0, "productos": 272}
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM CLIENTES")
        total_clientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM PEDIDOS_ENC")
        total_pedidos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM PRODUCTOS")
        total_productos = cursor.fetchone()[0]
        
        return {
            "clientes": total_clientes,
            "pedidos": total_pedidos,
            "productos": total_productos
        }
        
    except Exception as e:
        print(f"Error al obtener totales: {e}")
        return {"clientes": 85, "pedidos": 0, "productos": 272}
    finally:
        cursor.close()
        connection.close()

@app.get("/api/dashboard/clientes-por-departamento")
async def get_clientes_por_departamento(user: dict = Depends(require_login)):
    """Obtener distribución de clientes por departamento"""
    connection = conexion_sql()
    
    if not connection:
        return [{"departamento": "SACATEPEQUEZ", "total": 85}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT D.NOMBRE_DEPARTAMENTO as departamento, COUNT(*) as total
            FROM CLIENTES C
            INNER JOIN DEPARTAMENTOS D ON C.DEPARTAMENTO = D.DEPARTAMENTO
            GROUP BY D.NOMBRE_DEPARTAMENTO
            ORDER BY COUNT(*) DESC
        """)
        
        resultados = cursor.fetchall()
        return [{"departamento": row[0], "total": row[1]} for row in resultados]
        
    except Exception as e:
        print(f"Error al obtener clientes por departamento: {e}")
        return [{"departamento": "SACATEPEQUEZ", "total": 85}]
    finally:
        cursor.close()
        connection.close()

@app.get("/api/dashboard/productos-por-marca")
async def get_productos_por_marca(user: dict = Depends(require_login)):
    """Obtener distribución de productos por marca"""
    connection = conexion_sql()
    
    if not connection:
        return [{"marca": "ADAMS", "total": 25}]
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT TOP 10 M.NOMBRE_MARCA as marca, COUNT(*) as total
            FROM PRODUCTOS P
            INNER JOIN MARCAS M ON P.MARCA = M.CODIGO_MARCA
            GROUP BY M.NOMBRE_MARCA
            ORDER BY COUNT(*) DESC
        """)
        
        resultados = cursor.fetchall()
        return [{"marca": row[0], "total": row[1]} for row in resultados]
        
    except Exception as e:
        print(f"Error al obtener productos por marca: {e}")
        return [{"marca": "ADAMS", "total": 25}]
    finally:
        cursor.close()
        connection.close()

# ================================================
# RUTAS DE SALUD Y INFORMACIÓN
# ================================================

@app.get("/debug-usuarios")
async def debug_usuarios():
    """Endpoint para debug - mostrar estructura de usuarios (solo para desarrollo)"""
    conn = conexion_sql()
    if not conn:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "No se pudo conectar a la base de datos"}
        )
    
    try:
        cursor = conn.cursor()
        
        # Obtener estructura de la tabla
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'USUARIOS'
            ORDER BY ORDINAL_POSITION
        """)
        columnas = cursor.fetchall()
        
        # Obtener algunos usuarios (sin mostrar contraseñas)
        cursor.execute("""
            SELECT TOP 5 CODIGO_USUARIO, USUARIO, NOMBRE_USUARIO, CODIGO_PERFIL
            FROM USUARIOS
        """)
        usuarios = cursor.fetchall()
        
        return {
            "status": "success",
            "estructura_tabla": [
                {
                    "columna": col[0],
                    "tipo": col[1],
                    "nullable": col[2],
                    "longitud_max": col[3]
                }
                for col in columnas
            ],
            "usuarios_ejemplo": [
                {
                    "codigo_usuario": usr[0],
                    "usuario": usr[1],
                    "nombre_usuario": usr[2],
                    "codigo_perfil": usr[3]
                }
                for usr in usuarios
            ]
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error: {str(e)}"}
        )
    finally:
        cursor.close()
        conn.close()


@app.get("/api/info")
async def api_info():
    """Información de la API"""
    return {
        "name": "Gestor de Pedidos API",
        "version": "1.0.0",
        "description": "API unificada para gestión de pedidos",
        "endpoints": {
            "authentication": "/api/autenticacion",
            "products": "/api/productos",
            "health": "/health"
        }
    }

# ================================================
# CONFIGURACIÓN DE INICIO
# ================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Asume que el archivo se llama main.py
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )