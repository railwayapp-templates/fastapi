from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InventoryItem(BaseModel):
    """Modelo para elementos de inventario"""
    id: str
    color: str
    size: str
    quantity: int

class ProductBase(BaseModel):
    """Modelo base para productos"""
    client: str  # Referencia al ID del usuario
    productType: str
    name: str
    description: str
    category: str
    price: float
    sku: str
    url: str
    imageUrl: str
    availability: bool
    inventory: List[InventoryItem]

class ProductCreate(ProductBase):
    """Modelo para crear un producto"""
    pass

class ProductUpdate(BaseModel):
    """Modelo para actualizar un producto"""
    client: Optional[str] = None
    productType: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    sku: Optional[str] = None
    url: Optional[str] = None
    imageUrl: Optional[str] = None
    availability: Optional[bool] = None
    inventory: Optional[List[InventoryItem]] = None

class ProductInDB(ProductBase):
    """Modelo para producto almacenado en la base de datos"""
    id: str = Field(alias="productId")
    createdAt: datetime
    updatedAt: datetime

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "productId": "P001",
                "client": "user123",
                "productType": "buzo",
                "name": "Buzo con capucha",
                "description": "Buzo de algodón con forro polar interior.",
                "category": "Hombre",
                "price": 1200.5,
                "sku": "BUZ-001-GR",
                "url": "https://tienda.uy/productos/P001",
                "imageUrl": "https://example.com/image.jpg",
                "availability": True,
                "inventory": [
                    {"id": "1", "color": "gris", "size": "M", "quantity": 5},
                    {"id": "2", "color": "gris", "size": "L", "quantity": 3}
                ],
                "createdAt": "2023-01-01T12:00:00Z",
                "updatedAt": "2023-01-01T12:00:00Z"
            }
        }

class ProductResponse(BaseModel):
    """Modelo de respuesta para producto"""
    productId: str
    client: str
    productType: str
    name: str
    description: str
    category: str
    price: float
    sku: str
    url: str
    imageUrl: str
    availability: bool
    inventory: List[InventoryItem]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        schema_extra = {
            "example": {
                "productId": "P001",
                "client": "user123",
                "productType": "buzo",
                "name": "Buzo con capucha",
                "description": "Buzo de algodón con forro polar interior.",
                "category": "Hombre",
                "price": 1200.5,
                "sku": "BUZ-001-GR",
                "url": "https://tienda.uy/productos/P001",
                "imageUrl": "https://example.com/image.jpg",
                "availability": True,
                "inventory": [
                    {"id": "1", "color": "gris", "size": "M", "quantity": 5},
                    {"id": "2", "color": "gris", "size": "L", "quantity": 3}
                ],
                "createdAt": "2023-01-01T12:00:00Z",
                "updatedAt": "2023-01-01T12:00:00Z"
            }
        }

class PaginatedProductResponse(BaseModel):
    """Modelo para respuestas paginadas de productos"""
    data: List[ProductResponse]
    total: int
    page: int
    pageSize: int
    totalPages: int

class SearchProductParams(BaseModel):
    """Parámetros de búsqueda para productos"""
    page: Optional[int] = 1
    pageSize: Optional[int] = 10
    search: Optional[str] = ""
    startDate: Optional[str] = None
    endDate: Optional[str] = None