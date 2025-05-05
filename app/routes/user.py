from fastapi import APIRouter, HTTPException, Query, Body, Depends, status
from typing import Optional, List

from app.models.user import (
    UserResponse, 
    UserUpdate, 
    UserListResponse, 
    UserSearchParams,
    UserRole
)
from app.services.user import (
    get_users,
    get_user_by_id,
    update_user,
    delete_user,
    get_user_response
)
from app.security import get_current_active_user, has_role

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Usuario no encontrado"}},
)

@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    pageSize: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    search: Optional[str] = Query(None, description="Término de búsqueda por nombre o email"),
    role: Optional[UserRole] = Query(None, description="Filtrar por rol"),
    current_user: dict = Depends(has_role([UserRole.ADMIN]))
):
    """
    Obtiene una lista paginada de usuarios con opciones de búsqueda (solo para administradores)
    """
    params = UserSearchParams(page=page, pageSize=pageSize, search=search, role=role)
    return await get_users(params)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_active_user)):
    """
    Obtiene el perfil del usuario actualmente autenticado
    """
    return await get_user_response(current_user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(has_role([UserRole.ADMIN]))
):
    """
    Obtiene un usuario por su ID (solo para administradores)
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )
    return await get_user_response(user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate = Body(...),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Actualiza el perfil del usuario actualmente autenticado
    """
    # No permitir que un usuario normal cambie su propio rol
    if current_user["role"] != UserRole.ADMIN.value and user_update.role is not None:
        user_update.role = None
    
    updated_user = await update_user(current_user["_id"], user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo actualizar el usuario"
        )
    return updated_user

@router.put("/{user_id}", response_model=UserResponse)
async def modify_user(
    user_id: str,
    user_update: UserUpdate = Body(...),
    current_user: dict = Depends(has_role([UserRole.ADMIN]))
):
    """
    Actualiza un usuario existente (solo para administradores)
    """
    updated_user = await update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    user_id: str,
    current_user: dict = Depends(has_role([UserRole.ADMIN]))
):
    """
    Elimina un usuario (solo para administradores)
    """
    # Evitar que un administrador se elimine a sí mismo
    if user_id == current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )
    
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )
    return None