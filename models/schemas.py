from typing import Optional
from pydantic import BaseModel


# ================================================
# AUTENTICACIÓN
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


# ================================================
# PRODUCTOS
# ================================================

class ProductResponse(BaseModel):
    Codigo: int
    Nombre: str
    Medida: Optional[str] = None
    Marca: Optional[str] = None
    Existencia: Optional[int] = 0
    Costo: float = 0.0
    Precio: float = 0.0
    Disponible: bool = True


class DeleteProductRequest(BaseModel):
    ProductoID: int


# ================================================
# PEDIDOS
# ================================================

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
# USUARIOS
# ================================================

class UsuarioCreate(BaseModel):
    usuario: str
    clave: str
    nombre_usuario: str
    codigo_perfil: int


class UsuarioUpdate(BaseModel):
    usuario: str
    nombre_usuario: str
    codigo_perfil: int


class CambiarClaveRequest(BaseModel):
    clave: str
