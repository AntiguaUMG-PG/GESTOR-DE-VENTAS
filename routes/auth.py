from fastapi import APIRouter

from models.schemas import LoginRequest, AuthResponse
from services.auth_services import authenticate_user

router = APIRouter(tags=["auth"])

@router.post("/api/autenticacion", response_model=AuthResponse)
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