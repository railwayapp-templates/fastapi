from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional

from app.models.product_type import (
    ProductTypeCreate, 
    ProductTypeResponse, 
    ProductTypeUpdate,
    PaginatedResponse, 
    SearchParams
)
from app.services.product_type import (
    get_product_types,
    get_product_type_by_id,
    create_product_type,
    update_product_type,
    delete_product_type
)

router = APIRouter(
    prefix="/product-types",
    tags=["product-types"],
    responses={404: {"description": "No encontrado"}},
)

@router.get("", response_model=PaginatedResponse)
async def list_product_types(
    page: int = Query(1, ge=1, description="Número de página"),
    pageSize: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    search: Optional[str] = Query(None, description="Término de búsqueda por nombre")
):
    """
    Obtiene una lista paginada de tipos de producto con opciones de búsqueda
    """
    params = SearchParams(page=page, pageSize=pageSize, search=search)
    return await get_product_types(params)

@router.get("/{product_type_id}", response_model=ProductTypeResponse)
async def get_product_type(product_type_id: str):
    """
    Obtiene un tipo de producto por su ID
    """
    product_type = await get_product_type_by_id(product_type_id)
    if not product_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de producto con ID {product_type_id} no encontrado"
        )
    return product_type

@router.post("", response_model=ProductTypeResponse, status_code=status.HTTP_201_CREATED)
async def add_product_type(product_type: ProductTypeCreate = Body(...)):
    """
    Crea un nuevo tipo de producto
    """
    return await create_product_type(product_type)

@router.put("/{product_type_id}", response_model=ProductTypeResponse)
async def modify_product_type(product_type_id: str, product_type: ProductTypeUpdate = Body(...)):
    """
    Actualiza un tipo de producto existente
    """
    updated_product_type = await update_product_type(product_type_id, product_type)
    if not updated_product_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de producto con ID {product_type_id} no encontrado"
        )
    return updated_product_type

@router.delete("/{product_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_type(product_type_id: str):
    """
    Elimina un tipo de producto
    """
    success = await delete_product_type(product_type_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de producto con ID {product_type_id} no encontrado"
        )
    return None