import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client["tross_challenge"]
profiles_collection = db["profiles"]

# Ensure unique index on handle or url
async def init_db():
    await profiles_collection.create_index("url", unique=True)