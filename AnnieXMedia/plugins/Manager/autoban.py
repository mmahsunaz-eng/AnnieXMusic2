from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
import sqlite3, re
from datetime import datetime

# =====================
# CONFIG
# =====================
LOG_CHANNEL = -1002620223816  # GANTI ID CHANNEL LOG

# =====================
# DATABASE SQLITE
# =====================
db = sqlite3.connect("autoban.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS autoban (
    chat_id INTEGER PRIMARY KEY,
    status INTEGER
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS whitelist_users (
    user_id INTEGER PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS whitelist_words (
    word TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS banned_words (
    word TEXT PRIMARY KEY
)""")

db.commit()

# =====================
# REGEX ANTI SENSOR
# =====================
BAD_REGEX = re.compile(
    r"v[\W_]*c[\W_]*s|vc[\W_]*sex|video[\W_]*call[\W_]*sex",
    re.IGNORECASE
)

# =====================
# HELPER FUNCTION
# =====================
def autoban_active(chat_id):
    cur.execute("SELECT status FROM autoban WHERE chat_id=?", (chat_id,))
    r = cur.fetchone()
    return r and r[0] == 1

def is_whitelist_user(uid):
    cur.execute("SELECT 1 FROM whitelist_users WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def is_whitelist_word(text):
    cur.execute("SELECT word FROM whitelist_words")
    return any(w[0] in text for w in cur.fetchall())

def is_banned_word(text):
    cur.execute("SELECT word FROM banned_words")
    return any(w[0] in text for w in cur.fetchall())

# =====================
# /autoban on | off | status
# =====================
@Client.on_message(filters.command("autoban") & filters.group)
async def autoban_cmd(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("❌ Admin saja.")

    if len(message.command) < 2:
        return await message.reply("`/autoban on | off | status`")

    sub = message.command[1].lower()
    chat_id = message.chat.id

    if sub in ("on", "off"):
        status = 1 if sub == "on" else 0
        cur.execute("INSERT OR REPLACE INTO autoban VALUES (?,?)", (chat_id, status))
        db.commit()

        return await message.reply_text(
            f"📢 **AUTO BAN UPDATE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Status: {'🟢 ONLINE' if status else '🔴 OFFLINE'}\n"
            f"🕒 Waktu: {datetime.now().strftime('%H:%M:%S')}\n"
            f"👤 Oleh: {message.from_user.mention}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

    if sub == "status":
        cur.execute("SELECT COUNT(*) FROM whitelist_users")
        wl_u = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM whitelist_words")
        wl_w = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM banned_words")
        bw = cur.fetchone()[0]

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
# WHITELIST COMMAND
# =====================
@Client.on_message(filters.command("wl") & filters.group)
async def whitelist_cmd(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if len(message.command) < 2:
        return await message.reply("`/wl user|deluser (reply)`\n`/wl word|delword <kata>`\n`/wl list`")

    sub = message.command[1].lower()

    if sub == "user" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        cur.execute("INSERT OR IGNORE INTO whitelist_users VALUES (?)", (uid,))
        db.commit()
        return await message.reply("✅ User di-whitelist.")

    if sub == "deluser" and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        cur.execute("DELETE FROM whitelist_users WHERE user_id=?", (uid,))
        db.commit()
        return await message.reply("❌ User dihapus.")

    if sub == "word" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        cur.execute("INSERT OR IGNORE INTO whitelist_words VALUES (?)", (word,))
        db.commit()
        return await message.reply("✅ Kata di-whitelist.")

    if sub == "delword" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        cur.execute("DELETE FROM whitelist_words WHERE word=?", (word,))
        db.commit()
        return await message.reply("❌ Kata dihapus.")

    if sub == "list":
        cur.execute("SELECT user_id FROM whitelist_users")
        users = "\n".join(str(x[0]) for x in cur.fetchall()) or "Kosong"
        cur.execute("SELECT word FROM whitelist_words")
        words = "\n".join(x[0] for x in cur.fetchall()) or "Kosong"
        return await message.reply_text(f"📂 **WHITELIST**\n👤 User:\n{users}\n\n💬 Kata:\n{words}")

# =====================
# BADWORD COMMAND
# =====================
@Client.on_message(filters.command("badword") & filters.group)
async def badword_cmd(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    if len(message.command) < 2:
        return await message.reply("`/badword add|del <kata>`\n`/badword list`")

    sub = message.command[1].lower()

    if sub == "add" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        cur.execute("INSERT OR IGNORE INTO banned_words VALUES (?)", (word,))
        db.commit()
        return await message.reply("✅ Kata terlarang ditambahkan.")

    if sub == "del" and len(message.command) > 2:
        word = " ".join(message.command[2:]).lower()
        cur.execute("DELETE FROM banned_words WHERE word=?", (word,))
        db.commit()
        return await message.reply("❌ Kata terlarang dihapus.")

    if sub == "list":
        cur.execute("SELECT word FROM banned_words")
        words = "\n".join(w[0] for w in cur.fetchall()) or "Kosong"
        return await message.reply_text(f"🛑 **KATA TERLARANG**\n{words}")

# =====================
# AUTO BAN HANDLER
# =====================
@Client.on_message(filters.group & filters.text)
async def autoban_handler(client, message):
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
        f"📢 **Broadcast dimulai**\n\n"
        f"👤 Oleh: Ｏɴʟʏғᴏʀᴀᴄʜᴀ 𓆩✘𓆪 ᴀssɪsᴛᴀɴᴛ\n"
        f"🕒 Waktu: {time_str}\n"
        f"💬 Grup: {message.chat.title}\n\n"
        f"**Pesan:**\n"
        f"🚨⚠️ **P E N G U M U M A N** ⚠️🚨\n\n"
        f"📢 **PEMBERITAHUAN KEPADA MEMBER GRUP**\n\n"
        f"📅 {date_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User  : {message.from_user.mention}\n"
        f"💬 Pesan : `{message.text}`\n\n"
        f"⛔ **TINDAKAN OTOMATIS**\n"
        f"• Pesan dihapus\n"
        f"• User di-ban permanen\n\n"
        f"📛 **Alasan:**\n"
        f"Melanggar peraturan grup (Kalimat Terlarang)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💠 **Diterbitkan oleh:**\n"
        f"ᴏꜰꜰɪᴄɪᴀʟ 「 Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ 」\n\n"
        f"💎 Harap patuhi peraturan grup demi kenyamanan bersama"
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
    await notif.delete() if BAD_REGEX.search(text) or is_banned_word(text):
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
  
        
