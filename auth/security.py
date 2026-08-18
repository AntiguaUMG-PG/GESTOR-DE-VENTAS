from typing import Optional

from fastapi import Request, HTTPException, status

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

def require_admin(request: Request) -> dict:
    """
    Dependencia de FastAPI: exige usuario logueado Y con perfil
    de administrador (codigo_perfil == 1).
    Útil para /usuarios y endpoints de gestión de usuarios.
    """
    user = require_login(request)
    if user.get("codigo_perfil") != 1:
        raise HTTPException(status_code=403, detail="No tiene permisos para esta acción")
    return user