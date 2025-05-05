from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional

from app.models.category import (
    CategoryCreate, 
    CategoryResponse, 
    CategoryUpdate,
    PaginatedCategoryResponse, 
    SearchParams
)
from app.services.category import (
    get_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category
)

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "No encontrado"}},
)

@router.get("", response_model=PaginatedCategoryResponse)
async def list_categories(
    page: int = Query(1, ge=1, description="Número de página"),
    pageSize: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    search: Optional[str] = Query(None, description="Término de búsqueda por nombre o descripción")
):
    """
    Obtiene una lista paginada de categorías con opciones de búsqueda
    """
    params = SearchParams(page=page, pageSize=pageSize, search=search)
    return await get_categories(params)

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    """
    Obtiene una categoría por su ID
    """
    category = await get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {category_id} no encontrada"
        )
    return category

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def add_category(category: CategoryCreate = Body(...)):
    """
    Crea una nueva categoría
    """
    return await create_category(category)

@router.put("/{category_id}", response_model=CategoryResponse)
async def modify_category(category_id: str, category: CategoryUpdate = Body(...)):
    """
    Actualiza una categoría existente
    """
    updated_category = await update_category(category_id, category)
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {category_id} no encontrada"
        )
    return updated_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_category(category_id: str):
    """
    Elimina una categoría
    """
    success = await delete_category(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {category_id} no encontrada"
        )
    return None