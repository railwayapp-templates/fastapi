import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

# Cargar variables de entorno
load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "productdb")

# Cliente de MongoDB
client = AsyncIOMotorClient(MONGO_URI)
database = client[MONGO_DB_NAME]

# Colecciones
categories_collection = database.categories
product_types_collection = database.product_types
products_collection = database.products
users_collection = database.users
# No necesitamos definir una variable para categories aquí ya que 
# la definimos directamente en el servicio de categoría