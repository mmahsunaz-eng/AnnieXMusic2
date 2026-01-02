# Authored By Certified Coders © 2025
import os
import re
import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from AnnieXMedia import app
from AnnieXMedia.core.mongo import mongodb as db
from AnnieXMedia.utils.decorators import AdminRightsCheck

# =====================
# CONFIG
# =====================
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002620223816"))

# =====================
# REGEX ANTI SENSOR
# =====================
BAD_REGEX = re.compile(
    r"v[\W_]*c[\W_]*s|vc[\W_]*sex|video[\W_]*call[\W_]*sex",
    re.IGNORECASE,
)

# =====================
# HELPER (ASYNC – WAJIB)
# =====================
async def autoban_active(chat_id: int) -> bool:
    data = await db.autoban.find_one({"chat_id": chat_id})
    return bool(data and data.get("status") == 1)


async def is_whitelist_user(user_id: int) -> bool:
    return await db.whitelist_users.find_one({"user_id": user_id}) is not None


async def is_whitelist_word(text: str) -> bool:
    async for w in db.whitelist_words.find():
        if w["word"] in text:
            return True
    return False


async def is_banned_word(text: str) -> bool:
    async for w in db.banned_words.find():
        if w["word"] in text:
            return True
    return False


# =====================
# /autoban COMMAND
# =====================
@app.on_message(filters.command("autoban") & filters.group)
@AdminRightsCheck
async def autoban_cmd(app, message: Message, _):
    chat_id = message.chat.id

    if len(message.command) < 2:
        return await message.reply_text("`/autoban on | off | status`")

    sub = message.command[1].lower()

    if sub in ("on", "off"):
        status = 1 if sub == "on" else 0
        await db.autoban.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": status}},
            upsert=True,
        )

        return await message.reply_text(
            f"📢 **AUTO BAN UPDATE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Status : {'🟢 ONLINE' if status else '🔴 OFFLINE'}\n"
            f"🕒 Waktu  : {datetime.now().strftime('%H:%M:%S')}\n"
            f"👤 Oleh  : {message.from_user.mention}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

    if sub == "status":
        wl_u = await db.whitelist_users.count_documents({})
        wl_w = await db.whitelist_words.count_documents({})
        bw = await db.banned_words.count_documents({})

        return await message.reply_text(
            f"📢 **AUTO BAN STATUS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Sistem : {'🟢 ONLINE' if await autoban_active(chat_id) else '🔴 OFFLINE'}\n"
            f"👤 Whitelist User : {wl_u}\n"
            f"💬 Whitelist Kata : {wl_w}\n"
            f"🛑 Kata Terlarang : {bw}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )


# =====================
# /wl COMMAND
# =====================
@app.on_message(filters.command("wl") & filters.group)
@AdminRightsCheck
async def whitelist_cmd(app, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(
            "`/wl user|deluser (reply)`\n"
            "`/wl word|delword <kata>`\n"
            "`/wl list`"
        )

    sub = message.command[1].lower()

    if sub == "user" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        await db.whitelist_users.update_one(
            {"user_id": uid},
            {"$set": {"user_id": uid}},
            upsert=True,
        )
        return await message.reply_text("✅ User di-whitelist.")

    if sub == "deluser" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        await db.whitelist_users.delete_one({"user_id": uid})
        return await message.reply_text("❌ User dihapus.")

    if sub == "word" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        await db.whitelist_words.update_one(
            {"word": word},
            {"$set": {"word": word}},
            upsert=True,
        )
        return await message.reply_text("✅ Kata di-whitelist.")

    if sub == "delword" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        await db.whitelist_words.delete_one({"word": word})
        return await message.reply_text("❌ Kata dihapus.")

    if sub == "list":
        users = []
        async for x in db.whitelist_users.find():
            users.append(str(x["user_id"]))

        words = []
        async for x in db.whitelist_words.find():
            words.append(x["word"])

        return await message.reply_text(
            f"📂 **WHITELIST**\n\n"
            f"👤 User:\n{chr(10).join(users) if users else 'Kosong'}\n\n"
            f"💬 Kata:\n{chr(10).join(words) if words else 'Kosong'}"
        )


# =====================
# AUTO BAN HANDLER (FINAL)
# =====================
@app.on_message(
    filters.group & filters.text & ~filters.command([]),
    group=100
)
async def autoban_handler(app, message: Message):
async def autoban_handler(app, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    if not await autoban_active(chat_id):
        return

    member = await app.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        return

    if await is_whitelist_user(user_id):
        return

    if await is_whitelist_word(text):
        return

    if BAD_REGEX.search(text) or await is_banned_word(text):
        await message.delete()
        await app.ban_chat_member(chat_id, user_id)

        time_str = datetime.now().strftime("%H:%M:%S")

        notif = await message.reply_text(
            f"🚫⚠️ ** ᴀᴜᴛᴏ ʙᴀɴ ᴀᴄᴛɪᴠᴀᴛᴇ ** ⚠️🚫\n\n"
            f"👤 Bot   : Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ\n"
            f"🕒 Waktu : {time_str}\n"
            f"💬 Grup  : {message.chat.title}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User  : {message.from_user.mention}\n"
            f"💬 Pesan : `{message.text}`\n\n"
            f"⛔ **TINDAKAN**\n"
            f"• Pesan dihapus ✅\n"
            f"• User di-ban otomatis ✅\n\n"
            f"📛 **Alasan:**\n"
            f"Melanggar peraturan grup (Kalimat Terlarang)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💠 **Moderasi otomatis oleh**\n"
            f"ᴏꜰꜰɪᴄɪᴀʟ 「 Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ 」"
        )

        await app.send_message(
            LOG_CHANNEL,
            f"🚨 **AUTO BAN LOG**\n"
            f"👤 {message.from_user.mention}\n"
            f"🆔 `{user_id}`\n"
            f"💬 {message.chat.title}\n"
            f"📄 {message.text}"
        )

        await asyncio.sleep(10)
        await notif.delete()
