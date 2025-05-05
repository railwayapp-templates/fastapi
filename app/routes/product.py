from fastapi import APIRouter, HTTPException, Query, Body, status, Depends
from typing import Optional

from app.models.product import (
    ProductCreate, 
    ProductResponse, 
    ProductUpdate,
    PaginatedProductResponse, 
    SearchProductParams
)
from app.services.product import (
    get_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "No encontrado"}},
)

@router.get("", response_model=PaginatedProductResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Número de página"),
    pageSize: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    search: Optional[str] = Query(None, description="Término de búsqueda (nombre, descripción, categoría, tipo)"),
    startDate: Optional[str] = Query(None, description="Fecha de inicio (formato ISO)"),
    endDate: Optional[str] = Query(None, description="Fecha de fin (formato ISO)")
):
    """
    Obtiene una lista paginada de productos con opciones de búsqueda
    """
    params = SearchProductParams(
        page=page, 
        pageSize=pageSize, 
        search=search,
        startDate=startDate,
        endDate=endDate
    )
    return await get_products(params)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """
    Obtiene un producto por su ID
    """
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    return product

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def add_product(product: ProductCreate = Body(...)):
    """
    Crea un nuevo producto
    """
    return await create_product(product)

@router.put("/{product_id}", response_model=ProductResponse)
async def modify_product(product_id: str, product: ProductUpdate = Body(...)):
    """
    Actualiza un producto existente
    """
    updated_product = await update_product(product_id, product)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    return updated_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(product_id: str):
    """
    Elimina un producto
    """
    success = await delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    return None