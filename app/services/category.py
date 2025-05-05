import math
from typing import Optional, Dict, List, Any
import uuid

from app.config import database
from app.models.category import CategoryCreate, CategoryUpdate, SearchParams

# Definir la colección de categorías
category_collection = database.categories

async def get_categories(params: SearchParams) -> Dict[str, Any]:
    """
    Obtiene una lista paginada de categorías con opciones de búsqueda
    """
    # Valores por defecto
    page = params.page or 1
    page_size = params.pageSize or 10
    search = params.search or ""
    
    # Crear filtro de búsqueda
    filter_query = {}
    if search:
        # Búsqueda en nombre o descripción
        filter_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Contar total de documentos que cumplen con el filtro
    total = await category_collection.count_documents(filter_query)
    
    # Calcular paginación
    skip = (page - 1) * page_size
    
    # Obtener datos paginados
    cursor = category_collection.find(filter_query).skip(skip).limit(page_size)
    categories = await cursor.to_list(length=page_size)
    
    # Transformar los datos para que coincidan con la interfaz TypeScript
    transformed_data = []
    for cat in categories:
        transformed_data.append({
            "id": cat["_id"],
            "name": cat["name"],
            "description": cat["description"],
            "image": cat.get("image")
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

async def get_category_by_id(id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una categoría por su ID
    """
    category = await category_collection.find_one({"_id": id})
    
    if category:
        return {
            "id": category["_id"],
            "name": category["name"],
            "description": category["description"],
            "image": category.get("image")
        }
    return None

async def create_category(category: CategoryCreate) -> Dict[str, Any]:
    """
    Crea una nueva categoría
    """
    new_id = f"cat{uuid.uuid4().hex[:8]}"
    
    new_category = {
        "_id": new_id,
        "name": category.name,
        "description": category.description,
        "image": category.image
    }
    
    await category_collection.insert_one(new_category)
    
    return {
        "id": new_id,
        "name": category.name,
        "description": category.description,
        "image": category.image
    }

async def update_category(id: str, category: CategoryUpdate) -> Optional[Dict[str, Any]]:
    """
    Actualiza una categoría existente
    """
    # Comprobar si la categoría existe
    existing = await category_collection.find_one({"_id": id})
    if not existing:
        return None
    
    # Preparar datos de actualización
    update_data = {}
    
    # Añadir solo los campos que se van a actualizar
    if category.name is not None:
        update_data["name"] = category.name
    if category.description is not None:
        update_data["description"] = category.description
    if category.image is not None:
        update_data["image"] = category.image
    
    # No actualizar si no hay cambios
    if not update_data:
        # Devolver categoría existente sin cambios
        return {
            "id": existing["_id"],
            "name": existing["name"],
            "description": existing["description"],
            "image": existing.get("image")
        }
    
    # Realizar la actualización
    await category_collection.update_one(
        {"_id": id},
        {"$set": update_data}
    )
    
    # Obtener el documento actualizado
    updated = await category_collection.find_one({"_id": id})
    
    return {
        "id": updated["_id"],
        "name": updated["name"],
        "description": updated["description"],
        "image": updated.get("image")
    }

async def delete_category(id: str) -> bool:
    """
    Elimina una categoría por su ID
    """
    # Comprobar si la categoría existe
    existing = await category_collection.find_one({"_id": id})
    if not existing:
        return False
    
    # Eliminar la categoría
    result = await category_collection.delete_one({"_id": id})
    
    return result.deleted_count > 0

async def initialize_default_categories():
    """
    Inicializa categorías por defecto si la colección está vacía
    """
    count = await category_collection.count_documents({})
    
    if count == 0:
        default_categories = [
            {
                "_id": "cat1",
                "name": "Hombre",
                "description": "Ropa para hombres",
                "image": "https://images.unsplash.com/photo-1516826957135-700dedea698c?q=80&w=400&auto=format&fit=crop"
            },
            {
                "_id": "cat2",
                "name": "Mujer",
                "description": "Ropa para mujeres",
                "image": "https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?q=80&w=400&auto=format&fit=crop"
            },
            {
                "_id": "cat3",
                "name": "Niños",
                "description": "Ropa para niños",
                "image": "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?q=80&w=400&auto=format&fit=crop"
            },
            {
                "_id": "cat4",
                "name": "Accesorios",
                "description": "Complementos y accesorios de moda",
                "image": "https://images.unsplash.com/photo-1556656793-08538906a9f8?q=80&w=400&auto=format&fit=crop"
            }
        ]
        
        await category_collection.insert_many(default_categories)