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
# HELPER FUNCTIONS
# =====================
def autoban_active(chat_id):
    data = db.autoban.find_one({"chat_id": chat_id})
    return bool(data and data.get("status") == 1)


def is_whitelist_user(uid):
    return db.whitelist_users.find_one({"user_id": uid}) is not None


def is_whitelist_word(text):
    return any(w["word"] in text for w in db.whitelist_words.find())


def is_banned_word(text):
    return any(w["word"] in text for w in db.banned_words.find())


# =====================
# /autoban COMMAND
# =====================
@app.on_message(filters.command("autoban") & filters.group)
@AdminRightsCheck
async def autoban_cmd(client, message: Message, _):
    chat_id = message.chat.id

    if len(message.command) < 2:
        return await message.reply("`/autoban on | off | status`")

    sub = message.command[1].lower()

    if sub in ("on", "off"):
        status = 1 if sub == "on" else 0
        db.autoban.update_one(
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
        wl_u = db.whitelist_users.count_documents({})
        wl_w = db.whitelist_words.count_documents({})
        bw = db.banned_words.count_documents({})

        return await message.reply_text(
            f"📢 **AUTO BAN STATUS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Sistem : {'🟢 ONLINE' if autoban_active(chat_id) else '🔴 OFFLINE'}\n"
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
async def whitelist_cmd(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply(
            "`/wl user|deluser (reply)`\n"
            "`/wl word|delword <kata>`\n"
            "`/wl list`"
        )

    sub = message.command[1].lower()

    if sub == "user" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        db.whitelist_users.update_one(
            {"user_id": uid},
            {"$set": {"user_id": uid}},
            upsert=True,
        )
        return await message.reply("✅ User di-whitelist.")

    if sub == "deluser" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        db.whitelist_users.delete_one({"user_id": uid})
        return await message.reply("❌ User dihapus.")

    if sub == "word" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.whitelist_words.update_one(
            {"word": word},
            {"$set": {"word": word}},
            upsert=True,
        )
        return await message.reply("✅ Kata di-whitelist.")

    if sub == "delword" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.whitelist_words.delete_one({"word": word})
        return await message.reply("❌ Kata dihapus.")

    if sub == "list":
        users = "\n".join(str(x["user_id"]) for x in db.whitelist_users.find()) or "Kosong"
        words = "\n".join(x["word"] for x in db.whitelist_words.find()) or "Kosong"
        return await message.reply_text(
            f"📂 **WHITELIST**\n\n👤 User:\n{users}\n\n💬 Kata:\n{words}"
        )


# =====================
# /badword COMMAND
# =====================
@app.on_message(filters.command("badword") & filters.group)
@AdminRightsCheck
async def badword_cmd(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply("`/badword add|del <kata>`\n`/badword list`")

    sub = message.command[1].lower()

    if sub == "add" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.banned_words.update_one(
            {"word": word},
            {"$set": {"word": word}},
            upsert=True,
        )
        return await message.reply("✅ Kata terlarang ditambahkan.")

    if sub == "del" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.banned_words.delete_one({"word": word})
        return await message.reply("❌ Kata terlarang dihapus.")

    if sub == "list":
        words = "\n".join(x["word"] for x in db.banned_words.find()) or "Kosong"
        return await message.reply_text(f"🛑 **KATA TERLARANG**\n{words}")


# =====================
# AUTO BAN HANDLER
# =====================
@app.on_message(filters.group & filters.text, group=2)
async def autoban_handler(client, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    if not autoban_active(chat_id):
        return
    if is_whitelist_user(user_id):
        return
    if is_whitelist_word(text):
        return

    if BAD_REGEX.search(text) or is_banned_word(text):
        await message.delete()
        await client.ban_chat_member(chat_id, user_id)

        time_str = datetime.now().strftime("%H:%M:%S")

        notif = await message.reply(
            f"🚫⚠️ **ᴀᴜᴛᴏ ʙᴀɴ ᴀᴄᴛɪᴠᴀᴛᴇ** ⚠️🚫\n\n"
            f"👤 User  : {message.from_user.mention}\n"
            f"💬 Pesan : `{message.text}`\n"
            f"🕒 Waktu : {time_str}\n\n"
            f"⛔ Pesan dihapus & user di-ban otomatis"
        )

        await client.send_message(
            LOG_CHANNEL,
            f"🚨 **AUTO BAN LOG**\n"
            f"👤 {message.from_user.mention}\n"
            f"🆔 `{user_id}`\n"
            f"💬 {message.chat.title}\n"
            f"📄 {message.text}"
        )

        await asyncio.sleep(10)
        await notif.delete()
