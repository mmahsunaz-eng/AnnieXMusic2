import asyncio
import re
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus

from AnnieXMedia.core.mongo import mongodb

# =====================
# CONFIG
# =====================
LOG_CHANNEL = -1002620223816  # GANTI JIKA PERLU

# =====================
# REGEX ANTI SENSOR
# =====================
BAD_REGEX = re.compile(
    r"v[\W_]*c[\W_]*s|vc[\W_]*sex|video[\W_]*call[\W_]*sex",
    re.IGNORECASE
)

# =====================
# HELPER (MONGO ASYNC)
# =====================
async def autoban_active(chat_id: int) -> bool:
    data = await mongodb.autoban.find_one({"chat_id": chat_id})
    return bool(data and data.get("status") == 1)


async def is_whitelist_user(user_id: int) -> bool:
    return await mongodb.whitelist_users.find_one(
        {"user_id": user_id}
    ) is not None


async def is_whitelist_word(text: str) -> bool:
    async for w in mongodb.whitelist_words.find():
        if w["word"] in text:
            return True
    return False


async def is_banned_word(text: str) -> bool:
    async for w in mongodb.banned_words.find():
        if w["word"] in text:
            return True
    return False


# =====================
# /autoban on | off | status
# =====================
@Client.on_message(filters.command("autoban") & filters.group)
async def autoban_cmd(client: Client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("❌ Admin saja.")

    if len(message.command) < 2:
        return await message.reply("`/autoban on | off | status`")

    sub = message.command[1].lower()
    chat_id = message.chat.id

    if sub in ("on", "off"):
        status = 1 if sub == "on" else 0

        await mongodb.autoban.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": status}},
            upsert=True
        )

        return await message.reply_text(
            f"🚨 **AUTO BAN SYSTEM**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Status : {'🟢 AKTIF' if status else '🔴 NONAKTIF'}\n"
            f"👤 Oleh   : {message.from_user.mention}\n"
            f"🕒 Waktu  : {datetime.now().strftime('%H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

    if sub == "status":
        wl_user = await mongodb.whitelist_users.count_documents({})
        wl_word = await mongodb.whitelist_words.count_documents({})
        bw_word = await mongodb.banned_words.count_documents({})

        return await message.reply_text(
            f"🚨 **AUTO BAN STATUS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Sistem : {'🟢 AKTIF' if await autoban_active(chat_id) else '🔴 MATI'}\n"
            f"🛡️ Mode   : Regex + Custom Word\n\n"
            f"👤 Whitelist User : {wl_user}\n"
            f"💬 Whitelist Kata : {wl_word}\n"
            f"🛑 Kata Terlarang : {bw_word}\n\n"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💠 **Official Onlyforacha X Bot**"
        )


# =====================
# WHITELIST COMMAND
# =====================
@Client.on_message(filters.command("wl") & filters.group)
async def whitelist_cmd(client: Client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if len(message.command) < 2:
        return await message.reply(
            "`/wl user (reply)`\n"
            "`/wl deluser (reply)`\n"
            "`/wl word <kata>`\n"
            "`/wl delword <kata>`\n"
            "`/wl list`"
        )

    sub = message.command[1].lower()

    if sub == "user" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        await mongodb.whitelist_users.update_one(
            {"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True
        )
        return await message.reply("✅ User di-whitelist.")

    if sub == "deluser" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        await mongodb.whitelist_users.delete_one({"user_id": uid})
        return await message.reply("❌ User dihapus.")

    if sub == "word" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        await mongodb.whitelist_words.update_one(
            {"word": word}, {"$set": {"word": word}}, upsert=True
        )
        return await message.reply("✅ Kata di-whitelist.")

    if sub == "delword" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        await mongodb.whitelist_words.delete_one({"word": word})
        return await message.reply("❌ Kata dihapus.")

    if sub == "list":
        users = [str(u["user_id"]) async for u in mongodb.whitelist_users.find()]
        words = [w["word"] async for w in mongodb.whitelist_words.find()]

        return await message.reply_text(
            f"📂 **WHITELIST**\n\n"
            f"👤 User:\n{chr(10).join(users) if users else 'Kosong'}\n\n"
            f"💬 Kata:\n{chr(10).join(words) if words else 'Kosong'}"
        )


# =====================
# BADWORD COMMAND
# =====================
@Client.on_message(filters.command("badword") & filters.group)
async def badword_cmd(client: Client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if len(message.command) < 2:
        return await message.reply("`/badword add|del|list <kata>`")

    sub = message.command[1].lower()

    if sub == "add" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        await mongodb.banned_words.update_one(
            {"word": word}, {"$set": {"word": word}}, upsert=True
        )
        return await message.reply("✅ Kata terlarang ditambahkan.")

    if sub == "del" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        await mongodb.banned_words.delete_one({"word": word})
        return await message.reply("❌ Kata terlarang dihapus.")

    if sub == "list":
        words = [w["word"] async for w in mongodb.banned_words.find()]
        return await message.reply_text(
            f"🛑 **KATA TERLARANG**\n{chr(10).join(words) if words else 'Kosong'}"
        )


# =====================
# AUTO BAN HANDLER
# =====================
@Client.on_message(filters.group & filters.text)
async def autoban_handler(client: Client, message):
    if not await autoban_active(message.chat.id):
        return

    if not message.from_user:
        return

    if await is_whitelist_user(message.from_user.id):
        return

    text = message.text.lower()

    if await is_whitelist_word(text):
        return

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if BAD_REGEX.search(text) or await is_banned_word(text):
        await message.delete()
        await client.ban_chat_member(message.chat.id, message.from_user.id)

        now = datetime.now()
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
            f"ᴏꜰꜰɪᴄɪᴀʟ 「 Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ 🌸」"
         )

        await client.send_message(
            LOG_CHANNEL,
            f"🚨 AUTO BAN LOG\n"
            f"User: {message.from_user.mention}\n"
            f"ID: `{message.from_user.id}`\n"
            f"Grup: {message.chat.title}\n"
            f"Pesan: {message.text}\n"
            f"Waktu: {now.strftime('%H:%M:%S')}"
        )

        await asyncio.sleep(10)
        await notif.delete()
