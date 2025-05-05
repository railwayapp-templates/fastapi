from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

class LoginRequest(BaseModel):
    username: str
    password: str
    
class UserRole(str, Enum):
    ADMIN = "admin"
    VENDEDOR = "vendedor"
    MARKETING = "marketing"
    VENTAS = "ventas"

class UserBase(BaseModel):
    """Modelo base para usuarios"""
    email: EmailStr
    name: str
    role: UserRole = UserRole.VENDEDOR  # Rol por defecto

class UserCreate(UserBase):
    """Modelo para crear un usuario"""
    password: str

class UserUpdate(BaseModel):
    """Modelo para actualizar un usuario"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

class UserInDB(UserBase):
    """Modelo para usuario almacenado en la base de datos"""
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    role: UserRole

    class Config:
        validate_by_name = True  # Cambiado de allow_population_by_field_name
        json_schema_extra = {    # Cambiado de schema_extra
            "example": {
                "id": "user123",
                "email": "usuario@example.com",
                "name": "Nombre Usuario",
                "role": "vendedor"
            }
        }

class UserResponse(BaseModel):
    """Modelo de respuesta para usuario"""
    id: str
    email: EmailStr
    name: str
    role: UserRole

    class Config:
        schema_extra = {
            "example": {
                "id": "user123",
                "email": "usuario@example.com",
                "name": "Nombre Usuario",
                "role": "vendedor"
            }
        }
        use_enum_values = True

class UserListResponse(BaseModel):
    """Modelo para respuestas de lista de usuarios paginada"""
    data: List[UserResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int

class UserSearchParams(BaseModel):
    """Parámetros de búsqueda para usuarios"""
    page: Optional[int] = 1
    pageSize: Optional[int] = 10
    search: Optional[str] = ""
    role: Optional[UserRole] = None

class Token(BaseModel):
    """Modelo para tokens de autenticación"""
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    """Datos contenidos en el token"""
    user_id: Optional[str] = None
    role: Optional[str] = None