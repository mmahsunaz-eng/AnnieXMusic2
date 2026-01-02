from AnnieXMedia.core.mongo import mongodb

autoban = mongodb.autoban


async def get_chat(chat_id: int):
    return await autoban.find_one({"chat_id": chat_id})


async def set_status(chat_id: int, status: bool):
    await autoban.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )


async def add_word(chat_id: int, word: str):
    await autoban.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"words": word}},
        upsert=True
    )


async def remove_word(chat_id: int, word: str):
    await autoban.update_one(
        {"chat_id": chat_id},
        {"$pull": {"words": word}}
    )


async def add_whitelist(chat_id: int, user_id: int):
    await autoban.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"whitelist": user_id}},
        upsert=True
    )


async def remove_whitelist(chat_id: int, user_id: int):
    await autoban.update_one(
        {"chat_id": chat_id},
        {"$pull": {"whitelist": user_id}}
)
