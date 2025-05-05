from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.user import LoginRequest, Token, UserCreate, UserResponse
from app.security import (
    authenticate_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.services.user import create_user, get_user_response

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

@router.post("/token", response_model=Token)
async def login_for_access_token(credentials: LoginRequest):
    """
    Obtiene un token de acceso JWT para el usuario autenticado
    """

    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear datos del token
    token_data = {
        "sub": user["_id"],
        "role": user["role"]
    }
    
    # Crear token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    
    # Preparar respuesta de usuario
    user_response = await get_user_response(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """
    Registra un nuevo usuario
    """
    user_created = await create_user(user)
    if not user_created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )
    return user_created