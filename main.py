
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.product_type import router as product_type_router
from app.routes.product import router as product_router
from app.routes.category import router as category_router
from app.routes.user import router as user_router
from app.routes.auth import router as auth_router
from app.services.category import initialize_default_categories

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sales Agent API",
    description="API para gestionar productos, categorías y ventas",
    version="0.1.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, definir orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(product_type_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(user_router)
app.include_router(auth_router)

# Ruta de verificación de salud
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# Ruta raíz
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Bienvenido a la API de Sales Agent",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)