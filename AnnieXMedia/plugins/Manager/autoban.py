# Authored By Certified Coders © 2025
import os
import re
import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

from AnnieXMedia.core.bot import Client
from AnnieXMedia.core.mongo import as db

# =====================
# CONFIG
# =====================
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -1002620223816))

# =====================
# REGEX ANTI SENSOR
# =====================
BAD_REGEX = re.compile(
    r"v[\W_]*c[\W_]*s|vc[\W_]*sex|video[\W_]*call[\W_]*sex",
    re.IGNORECASE
)

# =====================
# HELPER FUNCTIONS
# =====================
def autoban_active(chat_id):
    r = db.autoban.find_one({"chat_id": chat_id})
    return r and r.get("status", 0) == 1

def is_whitelist_user(uid):
    return db.whitelist_users.find_one({"user_id": uid}) is not None

def is_whitelist_word(text):
    return any(w["word"] in text for w in db.whitelist_words.find())

def is_banned_word(text):
    return any(w["word"] in text for w in db.banned_words.find())

# =====================
# /autoban COMMAND
# =====================
@client.on_message(filters.command("autoban") & filters.group)
async def autoban_cmd(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("❌ Admin saja.")

    if len(message.command) < 2:
        return await message.reply("`/autoban on | off | status`")

    sub = message.command[1].lower()
    chat_id = message.chat.id

    if sub in ("on", "off"):
        status = 1 if sub == "on" else 0
        db.autoban.update_one({"chat_id": chat_id}, {"$set": {"status": status}}, upsert=True)

        return await message.reply_text(
            f"📢 **AUTO BAN UPDATE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Status: {'🟢 ONLINE' if status else '🔴 OFFLINE'}\n"
            f"🕒 Waktu: {datetime.now().strftime('%H:%M:%S')}\n"
            f"👤 Oleh: {message.from_user.mention}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

    if sub == "status":
        wl_u = db.whitelist_users.count_documents({})
        wl_w = db.whitelist_words.count_documents({})
        bw = db.banned_words.count_documents({})

        return await message.reply_text(
            f"📢 **P E M B E R I T A H U A N**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚨⚠️ **AUTO BAN STATUS BOT** ⚠️🚨\n\n"
            f"⚙️ Status Sistem : {'🟢 ONLINE' if autoban_active(chat_id) else '🔴 OFFLINE'}\n"
            f"🛡️ Mode Proteksi : Regex + Custom Word\n"
            f"👤 Whitelist User : {wl_u}\n"
            f"💬 Whitelist Kata : {wl_w}\n"
            f"🛑 Kata Terlarang : {bw}\n\n"
            f"🕒 Waktu : {datetime.now().strftime('%H:%M:%S')}\n"
            f"📅 Tanggal : {datetime.now().strftime('%d %B %Y')}\n"
            f"👤 Diperbarui oleh : {message.from_user.mention}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💠 **ᴏꜰꜰɪᴄɪᴀʟ 「 Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ 」**"
        )

# =====================
# /wl COMMAND
# =====================
@client.on_message(filters.command("wl") & filters.group)
async def whitelist_cmd(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if len(message.command) < 2:
        return await message.reply("`/wl user|deluser (reply)`\n`/wl word|delword <kata>`\n`/wl list`")

    sub = message.command[1].lower()

    if sub == "user" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        db.whitelist_users.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
        return await message.reply("✅ User di-whitelist.")

    if sub == "deluser" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        db.whitelist_users.delete_one({"user_id": uid})
        return await message.reply("❌ User dihapus.")

    if sub == "word" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.whitelist_words.update_one({"word": word}, {"$set": {"word": word}}, upsert=True)
        return await message.reply("✅ Kata di-whitelist.")

    if sub == "delword" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.whitelist_words.delete_one({"word": word})
        return await message.reply("❌ Kata dihapus.")

    if sub == "list":
        users = "\n".join(str(x["user_id"]) for x in db.whitelist_users.find()) or "Kosong"
        words = "\n".join(x["word"] for x in db.whitelist_words.find()) or "Kosong"
        return await message.reply_text(f"📂 **WHITELIST**\n👤 User:\n{users}\n\n💬 Kata:\n{words}")

# =====================
# /badword COMMAND
# =====================
@client.on_message(filters.command("badword") & filters.group)
async def badword_cmd(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if len(message.command) < 2:
        return await message.reply("`/badword add|del <kata>`\n`/badword list`")

    sub = message.command[1].lower()

    if sub == "add" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        db.banned_words.update_one({"word": word}, {"$set": {"word": word}}, upsert=True)
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
@client.on_message(filters.group & filters.text)
async def autoban_handler(client, message: Message):
    if not autoban_active(message.chat.id):
        return
    if not message.from_user:
        return
    if is_whitelist_user(message.from_user.id):
        return

    text = message.text.lower()
    if is_whitelist_word(text):
        return

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if BAD_REGEX.search(text) or is_banned_word(text):
        await message.delete()
        await client.ban_chat_member(message.chat.id, message.from_user.id)

        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d %B %Y")

        notif = await message.reply(
            f"🚫⚠️ ** ᴀᴜᴛᴏ ʙᴀɴ ᴀᴄᴛɪᴠᴀᴛᴇ ** ⚠️🚫\n\n"
            f"👤 Bot   : Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ\n"
            f"🕒 Waktu : {time_str}\n"
            f"💬 Grup  : {message.chat.title}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User  : {message.from_user.mention}\n"
            f"💬 Pesan : `{message.text}`\n\n"
            f"⛔ **TINDAKAN**\n"
            f"• Pesan dihapus✅\n"
            f"• User di-ban otomatis✅\n\n"
            f"📛 **Alasan:**\n"
            f"Melanggar peraturan grup (Kalimat Terlarang)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💠 **Moderasi otomatis oleh**\n"
            f"ᴏꜰꜰɪᴄɪᴀʟ 「 Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ 」"
        )

        await client.send_message(
            LOG_CHANNEL,
            f"🚨 **AUTO BAN LOG**\n"
            f"👤 {message.from_user.mention}\n"
            f"🆔 `{message.from_user.id}`\n"
            f"💬 {message.chat.title}\n"
            f"💬 Pesan: {message.text}\n"
            f"🕒 {time_str}"
        )

        await asyncio.sleep(10)
        await notif.delete()
