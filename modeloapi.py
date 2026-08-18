from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from routes.frontend import router as frontend_router
from routes.auth import router as auth_router
from routes.productos import router as productos_router
from routes.clientes import router as clientes_router
from routes.pedidos import router as pedidos_router
from routes.marcas import router as marcas_router
from routes.usuarios import router as usuarios_router
from routes.reportes import router as reportes_router
from routes.catalogos import router as catalogos_router
from routes.dashboard import router as dashboard_router
from routes.health import router as health_router

app = FastAPI(title="Gestor de Pedidos", version="2.0.0")
app.add_middleware(SessionMiddleware, secret_key="Natha0908I45")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(frontend_router)
app.include_router(auth_router)
app.include_router(productos_router)
app.include_router(clientes_router)
app.include_router(pedidos_router)
app.include_router(marcas_router)
app.include_router(usuarios_router)
app.include_router(reportes_router)
app.include_router(catalogos_router)
app.include_router(dashboard_router)
app.include_router(health_router)


# ================================================
# CONFIGURACIÓN DE INICIO
# ================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)