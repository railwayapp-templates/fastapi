from pydantic import BaseModel, Field
from typing import Optional, List

class CategoryBase(BaseModel):
    """Modelo base para categorías"""
    name: str
    description: str
    image: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Modelo para crear una categoría"""
    pass

class CategoryUpdate(CategoryBase):
    """Modelo para actualizar una categoría"""
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

class CategoryInDB(CategoryBase):
    """Modelo para categoría almacenada en la base de datos"""
    id: str = Field(alias="_id")

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "cat1",
                "name": "Hombre",
                "description": "Ropa para hombres",
                "image": "https://example.com/image.jpg"
            }
        }

class CategoryResponse(BaseModel):
    """Modelo de respuesta para categoría"""
    id: str
    name: str
    description: str
    image: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "cat1",
                "name": "Hombre",
                "description": "Ropa para hombres",
                "image": "https://example.com/image.jpg"
            }
        }

class PaginatedCategoryResponse(BaseModel):
    """Modelo para respuestas paginadas de categorías"""
    data: List[CategoryResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int

class SearchParams(BaseModel):
    """Parámetros de búsqueda para categorías"""
    page: Optional[int] = 1
    pageSize: Optional[int] = 10
    search: Optional[str] = ""