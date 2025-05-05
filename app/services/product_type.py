import math
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.config import product_types_collection
from app.models.product_type import ProductTypeCreate, SearchParams, ProductTypeUpdate

async def get_product_types(params: SearchParams) -> Dict[str, Any]:
    """
    Obtiene una lista paginada de tipos de producto con opciones de búsqueda
    """
    # Valores por defecto
    page = params.page or 1
    page_size = params.pageSize or 10
    search = params.search or ""
    
    # Crear filtro de búsqueda
    filter_query = {}
    if search:
        filter_query["name"] = {"$regex": search, "$options": "i"}  # Búsqueda insensible a mayúsculas/minúsculas
    
    # Contar total de documentos que cumplen con el filtro
    total = await product_types_collection.count_documents(filter_query)
    
    # Calcular paginación
    skip = (page - 1) * page_size
    
    # Obtener datos paginados
    cursor = product_types_collection.find(filter_query).skip(skip).limit(page_size)
    product_types = await cursor.to_list(length=page_size)
    
    # Transformar los datos para que coincidan con la interfaz TypeScript
    transformed_data = []
    for pt in product_types:
        transformed_data.append({
            "id": pt["_id"],
            "name": pt["name"],
            "client": pt["client"],
            "createdAt": pt["created_at"],
            "updatedAt": pt["updated_at"]
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

async def get_product_type_by_id(id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un tipo de producto por su ID
    """
    product_type = await product_types_collection.find_one({"_id": id})
    
    if product_type:
        return {
            "id": product_type["_id"],
            "name": product_type["name"],
            "client": product_type["client"],
            "createdAt": product_type["created_at"],
            "updatedAt": product_type["updated_at"]
        }
    return None

async def create_product_type(product_type: ProductTypeCreate) -> Dict[str, Any]:
    """
    Crea un nuevo tipo de producto
    """
    timestamp = datetime.utcnow().isoformat()
    new_id = f"type{uuid.uuid4().hex[:8]}"
    
    new_product_type = {
        "_id": new_id,
        "name": product_type.name,
        "client": product_type.client,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    await product_types_collection.insert_one(new_product_type)
    
    return {
        "id": new_id,
        "name": product_type.name,
        "client": product_type.client,
        "createdAt": timestamp,
        "updatedAt": timestamp
    }

async def update_product_type(id: str, product_type: ProductTypeUpdate) -> Optional[Dict[str, Any]]:
    """
    Actualiza un tipo de producto existente
    """
    # Comprobar si el tipo de producto existe
    existing = await product_types_collection.find_one({"_id": id})
    if not existing:
        return None
    
    # Preparar datos de actualización
    timestamp = datetime.utcnow().isoformat()
    update_data = {"updated_at": timestamp}
    
    # Añadir solo los campos que se van a actualizar
    if product_type.name is not None:
        update_data["name"] = product_type.name
    if product_type.client is not None:
        update_data["client"] = product_type.client
    
    # Realizar la actualización
    await product_types_collection.update_one(
        {"_id": id},
        {"$set": update_data}
    )
    
    # Obtener el documento actualizado
    updated = await product_types_collection.find_one({"_id": id})
    
    return {
        "id": updated["_id"],
        "name": updated["name"],
        "client": updated["client"],
        "createdAt": updated["created_at"],
        "updatedAt": updated["updated_at"]
    }

async def delete_product_type(id: str) -> bool:
    """
    Elimina un tipo de producto por su ID
    """
    # Comprobar si el tipo de producto existe
    existing = await product_types_collection.find_one({"_id": id})
    if not existing:
        return False
    
    # Eliminar el tipo de producto
    result = await product_types_collection.delete_one({"_id": id})
    
    return result.deleted_count > 0