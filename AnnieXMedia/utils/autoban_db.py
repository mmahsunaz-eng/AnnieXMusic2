import os
from motor.motor_asyncio import AsyncIOMotorClient

mongo = AsyncIOMotorClient(os.getenv("MONGO_DB_URI"))
db = Annie
col = db.autoban_words

async def get_chat(chat_id: int):
    data = await col.find_one({"chat_id": chat_id})
    if not data:
        data = {
            "chat_id": chat_id,
            "enabled": True,
            "words": [],
            "whitelist": []
        }
        await col.insert_one(data)
    return data

async def add_word(chat_id: int, word: str):
    await col.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"words": word}},
        upsert=True
    )

async def remove_word(chat_id: int, word: str):
    await col.update_one(
        {"chat_id": chat_id},
        {"$pull": {"words": word}}
    )

async def set_status(chat_id: int, status: bool):
    await col.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )

async def add_whitelist(chat_id: int, user_id: int):
    await col.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"whitelist": user_id}},
        upsert=True
    )

async def remove_whitelist(chat_id: int, user_id: int):
    await col.update_one(
        {"chat_id": chat_id},
        {"$pull": {"whitelist": user_id}}
    )
