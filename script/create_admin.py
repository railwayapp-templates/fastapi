"""
Script para crear un usuario administrador inicial
"""
import asyncio
import sys
import os

# Añadir el directorio raíz al path para poder importar desde app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import UserCreate, UserRole
from app.services.user import create_user, get_user_by_email

async def create_admin_user(email: str, name: str, password: str):
    """Crea un usuario admin si no existe"""
    
    # Verificar si ya existe
    existing_user = await get_user_by_email(email)
    if existing_user:
        print(f"Usuario con email {email} ya existe.")
        return
    
    # Crear usuario admin
    user_create = UserCreate(
        email=email,
        name=name,
        password=password,
        role=UserRole.ADMIN
    )
    
    user = await create_user(user_create)
    if user:
        print(f"Usuario administrador creado con éxito: {user['email']}")
    else:
        print("No se pudo crear el usuario administrador")

if __name__ == "__main__":
    print("Creando usuario administrador...")
    
    email = "admin@tienda.com"
    name = "admin"
    password = "admin123"
    
    asyncio.run(create_admin_user(email, name, password))