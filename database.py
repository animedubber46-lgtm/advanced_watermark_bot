from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.users = self.db.users
        self.presets = self.db.presets
        self.jobs = self.db.jobs

    async def ensure_indexes(self):
        await self.presets.create_index([("user_id", 1)])
        await self.jobs.create_index([("user_id", 1)])

    async def add_preset(self, preset: dict) -> str:
        result = await self.presets.insert_one(preset)
        return str(result.inserted_id)

    async def get_presets(self, user_id: int):
        cursor = self.presets.find({"user_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def get_preset(self, user_id: int, preset_id: str):
        from bson import ObjectId
        return await self.presets.find_one({"_id": ObjectId(preset_id), "user_id": user_id})

    async def delete_preset(self, user_id: int, preset_id: str) -> bool:
        from bson import ObjectId
        result = await self.presets.delete_one({"_id": ObjectId(preset_id), "user_id": user_id})
        return result.deleted_count > 0

db = Database()
