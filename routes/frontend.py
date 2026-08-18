from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from auth.security import get_current_user, require_login
from services.productos_service import get_productos_data
from services.auth_services import authenticate_user 

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ================================================
# LOGIN / LOGOUT
# ================================================

@router.get("/")
async def get_login(request: Request):
    """Página de inicio de sesión"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/index", status_code=302)
    
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login_datos")
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

@router.get("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

# ================================================
# PÁGINAS PRINCIPALES (requieren login)
# ================================================

@router.get("/index")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página Principal"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })

@router.get("/clientes")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página de Clientes"""
    return templates.TemplateResponse("clientes.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })

@router.get("/pedidos")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página de Pedidos"""
    return templates.TemplateResponse("pedidos.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })

@router.get("/productos")
async def get_productos_page(request: Request, user: dict = Depends(require_login)):
    """Página de productos"""
    try:
        productos = await get_productos_data()
        return templates.TemplateResponse("productos.html", {
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
    
@router.get("/reporte_inventario")
async def get_login(request: Request, user: dict = Depends(require_login)):
    """Página de Reporte de Inventario"""
    return templates.TemplateResponse("reporte_inventario.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })


@router.get("/usuarios")
async def get_usuarios_page(request: Request, user: dict = Depends(require_login)):
    """Página de gestión de usuarios"""
    
    # Verificar que el usuario sea administrador
    if user.get("codigo_perfil") != 1:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "No tiene permisos para acceder a esta sección"
        })
    
    return templates.TemplateResponse("usuarios.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })

@router.get("/marcas")
async def get_marcas_page(request: Request, user: dict = Depends(require_login)):
    """Página de gestión de marcas"""
    return templates.TemplateResponse("marcas.html", {
        "request": request,
        "usuario": user.get("nombre_usuario"),
        "perfil": user.get("codigo_perfil")
    })