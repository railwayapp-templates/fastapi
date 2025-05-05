import math
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.config import database
from app.models.product import ProductCreate, ProductUpdate, SearchProductParams

# Definir la colección para productos
products_collection = database.products

async def get_products(params: SearchProductParams) -> Dict[str, Any]:
    """
    Obtiene una lista paginada de productos con opciones de búsqueda
    """
    # Valores por defecto
    page = params.page or 1
    page_size = params.pageSize or 10
    search = params.search or ""
    start_date = params.startDate
    end_date = params.endDate
    
    # Crear filtro de búsqueda
    filter_query = {}
    
    # Filtro por búsqueda en diferentes campos
    if search:
        filter_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"category": {"$regex": search, "$options": "i"}},
            {"productType": {"$regex": search, "$options": "i"}}
        ]
    
    # Filtro por rango de fechas
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        
        if date_filter:
            filter_query["createdAt"] = date_filter
    
    # Contar total de documentos que cumplen con el filtro
    total = await products_collection.count_documents(filter_query)
    
    # Calcular paginación
    skip = (page - 1) * page_size
    
    # Obtener datos paginados
    cursor = products_collection.find(filter_query).skip(skip).limit(page_size)
    products = await cursor.to_list(length=page_size)
    
    # Transformar los datos para la respuesta
    transformed_data = []
    for product in products:
        # Transformar _id a productId para mantener la estructura de la interfaz
        product["productId"] = product.pop("_id")
        transformed_data.append(product)
    
    # Calcular total de páginas
    total_pages = math.ceil(total / page_size)
    
    return {
        "data": transformed_data,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages
    }

async def get_product_by_id(id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un producto por su ID
    """
    product = await products_collection.find_one({"_id": id})
    
    if product:
        # Transformar _id a productId para mantener la estructura de la interfaz
        product["productId"] = product.pop("_id")
        return product
    
    return None

async def create_product(product: ProductCreate) -> Dict[str, Any]:
    """
    Crea un nuevo producto
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Generar un productId con formato similar al mock
    new_id = f"P{str(uuid.uuid4().int)[:4].zfill(4)}"
    
    # Preparar documento para la base de datos
    product_dict = product.dict()
    
    new_product = {
        "_id": new_id,
        **product_dict,
        "createdAt": timestamp,
        "updatedAt": timestamp
    }
    
    # Insertar en la base de datos
    await products_collection.insert_one(new_product)
    
    # Transformar _id a productId para mantener la estructura de la interfaz
    new_product["productId"] = new_product.pop("_id")
    
    return new_product

async def update_product(id: str, product_update: ProductUpdate) -> Optional[Dict[str, Any]]:
    """
    Actualiza un producto existente
    """
    # Comprobar si el producto existe
    existing = await products_collection.find_one({"_id": id})
    if not existing:
        return None
    
    # Preparar datos de actualización
    timestamp = datetime.utcnow().isoformat()
    update_data = {"updatedAt": timestamp}
    
    # Añadir solo los campos que se van a actualizar
    product_dict = product_update.dict(exclude_unset=True)
    if product_dict:
        update_data.update(product_dict)
    
    # Realizar la actualización
    await products_collection.update_one(
        {"_id": id},
        {"$set": update_data}
    )
    
    # Obtener el documento actualizado
    updated = await products_collection.find_one({"_id": id})
    
    # Transformar _id a productId para mantener la estructura de la interfaz
    updated["productId"] = updated.pop("_id")
    
    return updated

async def delete_product(id: str) -> bool:
    """
    Elimina un producto por su ID
    """
    # Comprobar si el producto existe
    existing = await products_collection.find_one({"_id": id})
    if not existing:
        return False
    
    # Eliminar el producto
    result = await products_collection.delete_one({"_id": id})
    
    return result.deleted_count > 0