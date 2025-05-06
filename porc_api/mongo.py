from motor.motor_asyncio import AsyncIOMotorClient
from porc_common.config import get_env

MONGO_URI = get_env("MONGO_URI", required=True)

client = AsyncIOMotorClient(MONGO_URI)
db = client.get_default_database()
runs = db["runs"]