from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProductTypeBase(BaseModel):
    """Modelo base para tipos de producto"""
    name: str
    client: str

class ProductTypeCreate(ProductTypeBase):
    """Modelo para crear un tipo de producto"""
    pass

class ProductTypeUpdate(ProductTypeBase):
    """Modelo para actualizar un tipo de producto"""
    name: Optional[str] = None
    client: Optional[str] = None

class ProductTypeInDB(ProductTypeBase):
    """Modelo para tipo de producto almacenado en la base de datos"""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "type123",
                "name": "Producto Premium",
                "client": "Cliente A",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }

class ProductTypeResponse(BaseModel):
    """Modelo de respuesta para tipo de producto"""
    id: str
    name: str
    client: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "type123",
                "name": "Producto Premium",
                "client": "Cliente A",
                "createdAt": "2023-01-01T12:00:00Z",
                "updatedAt": "2023-01-01T12:00:00Z"
            }
        }

class PaginatedResponse(BaseModel):
    """Modelo para respuestas paginadas"""
    data: List[ProductTypeResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int

class SearchParams(BaseModel):
    """Parámetros de búsqueda para tipos de producto"""
    page: Optional[int] = 1
    pageSize: Optional[int] = 10
    search: Optional[str] = ""