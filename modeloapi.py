from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
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
# CONEXIÓN A BASE DE DATOS POSTGRESQL
# ================================================

def conexion_sql():
    """Función para la configuración de la conexión a PostgreSQL"""
    try:
        # Configuración de conexión a PostgreSQL
        connection = psycopg2.connect(
            host="localhost",  # o tu host
            port=5432,
            database="gestor_pedidos",
            user="manage",
            password="natha91275"
        )
        print("✅ Conexión exitosa a PostgreSQL")
        return connection
        
    except Exception as error:
        print(f"❌ Error de conexión a PostgreSQL: {str(error)}")
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
    """Página de Clientes"""
    return templates.TemplateResponse("clientes.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })

@app.get("/pedidos")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página de Pedidos"""
    return templates.TemplateResponse("pedidos.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })

@app.get("/productos")
async def get_productos_page(request: Request, user: dict = Depends(require_login)):
    """Página de productos"""
    try:
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
    """Página de Reporte de Inventario"""
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
        nombre = nombre.strip()
        contrasena = contrasena.strip()
        
        if not nombre or not contrasena:
            print("❌ Campos vacíos después de limpiar")
            error_msg = "Por favor complete todos los campos"
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": error_msg
            })
        
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
            
            return RedirectResponse(url="/index", status_code=302)
        else:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": auth_result.get("message", "Credenciales incorrectas")
            })
            
    except Exception as e:
        print(f"❌ Error crítico en login HTML: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Error interno del servidor. Revise los logs en la consola."
        })

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

@app.post("/insertar_cliente")
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

@app.put("/actualizar_cliente")
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

@app.delete("/eliminar_cliente/{codigo_cliente}")
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
                p.numero_pedido,
                p.fecha,
                p.nombre_cliente,
                p.nit,
                p.direccion,
                COALESCE(p.total_documento, 0) as total_documento,
                p.estado
            FROM pedidos_enc p
            ORDER BY p.numero_pedido DESC
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
        cursor.execute("SELECT COALESCE(MAX(numero_pedido), 0) + 1 FROM pedidos_enc")
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
            SELECT 
                p.codigo_producto as Codigo,
                p.nombre_producto as Descripcion_producto,
                p.unidad_medida as Presentacion,
                COALESCE(pr.precio, 0) as Precio,
                COALESCE(p.existencia, 0) as EXISTENCIA
            FROM productos p
            LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto AND pr.nivel_precio = 1
            WHERE p.nombre_producto ILIKE %s
            ORDER BY p.nombre_producto
            LIMIT 20
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
            SELECT existencia 
            FROM productos 
            WHERE codigo_producto = %s
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
        
        fecha_str = pedido_data.get('FECHA_PEDIDO')
        if fecha_str and '/' in fecha_str:
            fecha_pedido = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
        else:
            fecha_pedido = datetime.now() 
        
        cursor.execute("""
            INSERT INTO pedidos_enc (
                fecha, codigo_usuario, codigo_cliente, nombre_cliente,
                nit, direccion, total_documento, estado, comentarios
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'ABIERTO', %s)
            RETURNING numero_pedido
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
                INSERT INTO pedidos_det (
                    numero_pedido, codigo_producto, nombre_producto,
                    unidad_medida, cantidad, precio_unitario, total_linea
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                detalle.get('NUMERO_PEDIDO'),
                int(detalle.get('CODIGO_PRODUCTO')),
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
                UPDATE productos 
                SET existencia = existencia - %s
                WHERE codigo_producto = %s
            """, (
                float(cantidad),
                int(codigo)
            ))
            
            cursor.execute("SELECT existencia FROM productos WHERE codigo_producto = %s", (int(codigo),))
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
                codigo_producto,
                nombre_producto,
                unidad_medida,
                cantidad,
                precio_unitario,
                total_linea
            FROM pedidos_det
            WHERE numero_pedido = %s
            ORDER BY numero_linea
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
        
        cursor.execute("""
            SELECT 
                numero_pedido,
                fecha,
                nombre_cliente,
                nit,
                direccion,
                total_documento,
                estado,
                comentarios
            FROM pedidos_enc
            WHERE numero_pedido = %s
        """, (numero_pedido,))
        
        encabezado = cursor.fetchone()
        
        if not encabezado:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        cursor.execute("""
            SELECT 
                codigo_producto,
                nombre_producto,
                unidad_medida,
                cantidad,
                precio_unitario,
                total_linea
            FROM pedidos_det
            WHERE numero_pedido = %s
            ORDER BY numero_linea
        """, (numero_pedido,))
        
        detalles = cursor.fetchall()
        
        fecha_pedido = encabezado[1].strftime('%d/%m/%Y %H:%M:%S Hrs') if encabezado[1] else ''
        
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
        
        detalles_lista = [{
            'codigo': row[0],
            'producto': row[1],
            'unidad': row[2],
            'cantidad': float(row[3]) if row[3] else 0,
            'precio': float(row[4]) if row[4] else 0.0,
            'total': float(row[5]) if row[5] else 0.0
        } for row in detalles]
        
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
        
        if not fecha:
            fecha = date.today().strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT 
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca,
                COALESCE(p.existencia, 0) AS inventario_actual,
                v.cantidad_vendida,
                COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0) AS inventario_resultante,
                CASE 
                    WHEN (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0
                    THEN ABS(COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0))
                    ELSE 0 
                END AS faltante,
                pr.precio
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto
            INNER JOIN (
                SELECT 
                    pd.codigo_producto,
                    COALESCE(SUM(pd.cantidad), 0) AS cantidad_vendida
                FROM pedidos_det pd
                INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                WHERE DATE(pe.fecha) = %s
                GROUP BY pd.codigo_producto
            ) AS v ON p.codigo_producto = v.codigo_producto
            ORDER BY 
                CASE WHEN (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0 THEN 0 ELSE 1 END,
                p.nombre_producto
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
            fecha = date.today().strftime('%Y-%m-%d')

        # Total de productos vendidos en la fecha seleccionada
        cursor.execute("""
            SELECT COUNT(DISTINCT pd.codigo_producto)
            FROM pedidos_det pd
            INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
            WHERE DATE(pe.fecha) = %s
        """, (fecha,))
        total_productos_vendidos = cursor.fetchone()[0]

        # Productos con inventario insuficiente
        cursor.execute("""
            SELECT COUNT(*)
            FROM productos p
            INNER JOIN (
                SELECT 
                    pd.codigo_producto,
                    COALESCE(SUM(pd.cantidad), 0) AS cantidad_vendida
                FROM pedidos_det pd
                INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                WHERE DATE(pe.fecha) = %s
                GROUP BY pd.codigo_producto
            ) AS v ON p.codigo_producto = v.codigo_producto
            WHERE (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0
        """, (fecha,))
        productos_insuficientes = cursor.fetchone()[0]

        # Total de unidades faltantes
        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN (COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0)) < 0 
                        THEN ABS(COALESCE(p.existencia, 0) - COALESCE(v.cantidad_vendida, 0))
                        ELSE 0 
                    END
                ), 0)
            FROM productos p
            INNER JOIN (
                SELECT 
                    pd.codigo_producto,
                    COALESCE(SUM(pd.cantidad), 0) AS cantidad_vendida
                FROM pedidos_det pd
                INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                WHERE DATE(pe.fecha) = %s
                GROUP BY pd.codigo_producto
            ) AS v ON p.codigo_producto = v.codigo_producto
        """, (fecha,))
        total_unidades_faltantes = cursor.fetchone()[0] or 0

        # Total de pedidos del día
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pedidos_enc 
            WHERE DATE(fecha) = %s
        """, (fecha,))
        total_pedidos = cursor.fetchone()[0]

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
        
        cursor.execute("""
            SELECT 
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca,
                COALESCE(p.existencia, 0) as existencia
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            WHERE COALESCE(p.existencia, 0) <= 10
            ORDER BY p.existencia ASC
            LIMIT %s
        """, (limite,))
        
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

    if not fecha:
        fecha = date.today().strftime('%Y-%m-%d')
    
    connection = conexion_sql()
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()

        # Resumen de inventario
        cursor.execute("""
        WITH ProductosVendidos AS (
            SELECT
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                p.marca,
                COALESCE(p.existencia,0) AS existencia,
                COALESCE(SUM(pd.cantidad),0) AS cantidad_vendida
            FROM productos p
            LEFT JOIN pedidos_det pd ON p.codigo_producto = pd.codigo_producto
            LEFT JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                AND DATE(pe.fecha) = %s
            GROUP BY p.codigo_producto, p.nombre_producto, p.unidad_medida, p.marca, p.existencia
        )
        SELECT
            COUNT(*) AS total_productos_vendidos,
            SUM(CASE WHEN existencia - cantidad_vendida >= 0 THEN 1 ELSE 0 END) AS productos_suficientes,
            SUM(CASE WHEN existencia - cantidad_vendida < 0 THEN 1 ELSE 0 END) AS productos_insuficientes,
            SUM(CASE WHEN existencia - cantidad_vendida < 0 THEN ABS(existencia - cantidad_vendida) ELSE 0 END) AS total_unidades_faltantes
        FROM ProductosVendidos
        """, (fecha,))
        
        resumen = cursor.fetchone()
        resumen_data = {
            'total_productos_vendidos': resumen[0],
            'productos_con_inventario_suficiente': resumen[1],
            'productos_con_inventario_insuficiente': resumen[2],
            'total_unidades_faltantes': int(resumen[3])
        }

        # Detalle
        cursor.execute("""
        WITH ProductosVendidos AS (
            SELECT
                p.codigo_producto,
                p.nombre_producto,
                p.unidad_medida,
                m.nombre_marca AS marca,
                COALESCE(p.existencia,0) AS inventario_actual,
                SUM(pd.cantidad) AS cantidad_vendida
            FROM productos p
            INNER JOIN marcas m ON p.marca = m.codigo_marca
            INNER JOIN pedidos_det pd ON p.codigo_producto = pd.codigo_producto
            INNER JOIN pedidos_enc pe ON pd.numero_pedido = pe.numero_pedido
                AND DATE(pe.fecha) = %s
            GROUP BY p.codigo_producto, p.nombre_producto, p.unidad_medida, m.nombre_marca, p.existencia
        )
        SELECT
            codigo_producto,
            nombre_producto,
            unidad_medida,
            marca,
            inventario_actual,
            cantidad_vendida,
            inventario_actual - cantidad_vendida AS inventario_resultante,
            CASE WHEN inventario_actual - cantidad_vendida < 0 THEN ABS(inventario_actual - cantidad_vendida) ELSE 0 END AS faltante
        FROM ProductosVendidos
        ORDER BY faltante DESC, nombre_producto
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

@app.get("/listado_productos")
async def get_productos_listado(user: dict = Depends(require_login)):
    """API endpoint para obtener listado completo de productos"""
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
            INSERT INTO productos (nombre_producto, unidad_medida, marca, existencia)
            VALUES (%s, %s, %s, %s)
            RETURNING codigo_producto
        """, (
            producto_data.get('NOMBRE_PRODUCTO'),
            producto_data.get('UNIDAD_MEDIDA'),
            int(producto_data.get('MARCA')),
            float(producto_data.get('EXISTENCIA', 0))
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

@app.put("/api/productos/actualizar")
async def actualizar_producto(producto_data: dict):
    """Actualizar producto existente"""
    connection = conexion_sql()
    
    if not connection:
        raise HTTPException(status_code=500, detail="No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE productos SET
                nombre_producto = %s, existencia = %s, unidad_medida = %s
            WHERE codigo_producto = %s
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
                UPDATE precios SET precio = %s
                WHERE codigo_producto = %s AND nivel_precio = 1
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

@app.get("/api/marcas")
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

async def get_productos_data() -> List[dict]:
    """Función auxiliar para obtener datos de productos"""
    connection = conexion_sql()
    
    if not connection:
        raise Exception("No se pudo establecer conexión a la base de datos")
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                p.codigo_producto, 
                p.nombre_producto, 
                p.unidad_medida, 
                m.nombre_marca, 
                p.existencia,
                pr.precio
            FROM 
                productos p
                INNER JOIN marcas m ON p.marca = m.codigo_marca
                LEFT JOIN precios pr ON p.codigo_producto = pr.codigo_producto
                LEFT JOIN nivel_precio np ON pr.nivel_precio = np.nivel_precio
        """)
        contenido_producto = cursor.fetchall()
        
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
        cursor.execute("SELECT municipio as id, nombre_municipio as nombre FROM municipios ORDER BY nombre_municipio")
        municipios = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in municipios]
        
    except Exception as e:
        print(f"Error al obtener municipios: {e}")
        return []
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
        cursor.execute("SELECT departamento as id, nombre_departamento as nombre FROM departamentos ORDER BY nombre_departamento")
        departamentos = cursor.fetchall()
        
        return [{'id': row[0], 'nombre': row[1]} for row in departamentos]
        
    except Exception as e:
        print(f"Error al obtener departamentos: {e}")
        return []
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

# ================================================
# RUTAS PARA RESUMENES DEL DASHBOARD
# ================================================

@app.get("/api/dashboard/totales")
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

@app.get("/api/dashboard/clientes-por-departamento")
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

@app.get("/api/dashboard/productos-por-marca")
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

# ================================================
# RUTAS DE SALUD Y INFORMACIÓN
# ================================================

@app.get("/api/info")
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

@app.get("/health")
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

# ================================================
# CONFIGURACIÓN DE INICIO
# ================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)