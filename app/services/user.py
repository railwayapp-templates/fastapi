import math
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.config import database
from app.models.user import UserCreate, UserUpdate, UserSearchParams, UserRole
from app.security import get_password_hash

# Colección de usuarios
users_collection = database.users

async def get_users(params: UserSearchParams) -> Dict[str, Any]:
    """
    Obtiene una lista paginada de usuarios con opciones de búsqueda
    """
    # Valores por defecto
    page = params.page or 1
    page_size = params.pageSize or 10
    search = params.search or ""
    role = params.role
    
    # Crear filtro de búsqueda
    filter_query = {}
    if search:
        # Búsqueda por nombre o email
        filter_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    if role:
        filter_query["role"] = role.value
    
    # Contar total de documentos que cumplen con el filtro
    total = await users_collection.count_documents(filter_query)
    
    # Calcular paginación
    skip = (page - 1) * page_size
    
    # Obtener datos paginados
    cursor = users_collection.find(filter_query).skip(skip).limit(page_size)
    users = await cursor.to_list(length=page_size)
    
    # Transformar los datos para que coincidan con la interfaz (sin incluir contraseñas)
    transformed_data = []
    for user in users:
        transformed_data.append({
            "id": user["_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        })
    
    # Calcular total de páginas
    total_pages = math.ceil(total / page_size)
    
    return {
        "data": transformed_data,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages
    }

async def get_user_by_id(id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su ID
    """
    user = await users_collection.find_one({"_id": id})
    return user if user else None

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su email
    """
    user = await users_collection.find_one({"email": email})
    return user if user else None

async def create_user(user: UserCreate) -> Dict[str, Any]:
    """
    Crea un nuevo usuario
    """
    # Verificar si ya existe un usuario con el mismo email
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        return None
    
    timestamp = datetime.utcnow().isoformat()
    new_id = f"user{uuid.uuid4().hex[:8]}"
    
    # Crear documento de usuario
    new_user = {
        "_id": new_id,
        "email": user.email,
        "name": user.name,
        "hashed_password": get_password_hash(user.password),
        "role": user.role.value,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # Insertar en la base de datos
    await users_collection.insert_one(new_user)
    
    # Retornar datos sin la contraseña
    return {
        "id": new_id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value
    }

async def update_user(id: str, user_update: UserUpdate) -> Optional[Dict[str, Any]]:
    """
    Actualiza un usuario existente
    """
    # Comprobar si el usuario existe
    existing = await get_user_by_id(id)
    if not existing:
        return None
    
    # Verificar si se está actualizando el email y si ya existe otro usuario con ese email
    if user_update.email and user_update.email != existing["email"]:
        user_with_same_email = await get_user_by_email(user_update.email)
        if user_with_same_email:
            return None
    
    # Preparar datos de actualización
    timestamp = datetime.utcnow().isoformat()
    update_data = {"updated_at": timestamp}
    
    # Añadir solo los campos que se van a actualizar
    if user_update.name is not None:
        update_data["name"] = user_update.name
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.password is not None:
        update_data["hashed_password"] = get_password_hash(user_update.password)
    if user_update.role is not None:
        update_data["role"] = user_update.role.value
    
    # Realizar la actualización
    await users_collection.update_one(
        {"_id": id},
        {"$set": update_data}
    )
    
    # Obtener el documento actualizado
    updated = await get_user_by_id(id)
    
    # Retornar datos sin la contraseña
    return {
        "id": updated["_id"],
        "email": updated["email"],
        "name": updated["name"],
        "role": updated["role"]
    }

async def delete_user(id: str) -> bool:
    """
    Elimina un usuario por su ID
    """
    # Comprobar si el usuario existe
    existing = await get_user_by_id(id)
    if not existing:
        return False
    
    # Eliminar el usuario
    result = await users_collection.delete_one({"_id": id})
    
    return result.deleted_count > 0

async def get_user_response(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte un documento de usuario de la base de datos al formato de respuesta
    """
    return {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"]
    }