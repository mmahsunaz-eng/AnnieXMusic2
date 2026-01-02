import asyncio
import re
import os
from datetime import datetime
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from AnnieXMedia import app
from AnnieXMedia.utils.autoban_db import (
    get_chat, add_word, remove_word,
    set_status, add_whitelist, remove_whitelist
)

LOG_CHAT = int(os.getenv("AUTOBAN_LOG_CHAT", 0))


def is_admin(member):
    return member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    )


def build_regex(word: str):
    # sex -> s[\W_]*e[\W_]*x
    return "".join([f"{c}[\\W_]*" for c in word])


# ================= AUTO BAN =================
@app.on_message(
    filters.group & (filters.text | filters.caption),
    group=0  # dijalankan paling awal
)
async def autoban_handler(client, message):
    # debug check
    print(f"AUTOBAN HANDLER TRIGGERED: {message.text or message.caption}")

    if not message.from_user:
        return

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if is_admin(member):
        return

    data = await get_chat(message.chat.id)
    if not data["enabled"]:
        return

    if message.from_user.id in data["whitelist"]:
        return

    text = (message.text or message.caption).lower()

    for word in data["words"]:
        if re.search(build_regex(word), text):
            try:
                time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

                # hapus pesan kotor
                await message.delete()

                # ban user
                await client.ban_chat_member(message.chat.id, message.from_user.id)

                log_text = (
                    f"🚫⚠️ ** ᴀᴜᴛᴏ ʙᴀɴ ᴀᴄᴛɪᴠᴀᴛᴇ ** ⚠️🚫\n\n"
                    f"👤 Bot   : Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ\n"
                    f"🕒 Waktu : {time_str}\n"
                    f"💬 Grup  : {message.chat.title}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 User  : {message.from_user.mention}\n"
                    f"💬 Pesan : `{text}`\n\n"
                    f"⛔ **TINDAKAN**\n"
                    f"• Pesan dihapus✅\n"
                    f"• User di-ban otomatis✅\n\n"
                    f"📛 **Alasan:**\n"
                    f"Melanggar peraturan grup (Kalimat Terlarang)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💠 **Moderasi otomatis oleh**\n"
                    f"ᴏꜰꜰɪᴄɪᴀʟ 「 Oɴʟʏғᴏʀᴀᴄʜᴀ ✘ ʙᴏᴛ 」"
                )

                # kirim notifikasi ke grup
                notice = await client.send_message(message.chat.id, log_text)

                # auto delete 5 detik
                await asyncio.sleep(5)
                await notice.delete()

                # kirim log permanen
                if LOG_CHAT:
                    await client.send_message(LOG_CHAT, log_text)

            except Exception as e:
                print("AUTOBAN ERROR:", e)
            break

# ================= COMMAND =================

@app.on_message(filters.command("addbadword") & filters.group)
async def add_bw(_, m):
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not is_admin(member):
        return await m.reply("❌ Hanya admin.")

    if len(m.command) < 2:
        return await m.reply("Gunakan: `/addbadword kata`")

    await add_word(m.chat.id, m.command[1].lower())
    await m.reply("✅ Kata ditambahkan.")


@app.on_message(filters.command("delbadword") & filters.group)
async def del_bw(_, m):
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not is_admin(member):
        return await m.reply("❌ Hanya admin.")

    await remove_word(m.chat.id, m.command[1].lower())
    await m.reply("🗑️ Kata dihapus.")


@app.on_message(filters.command("badwords") & filters.group)
async def list_bw(_, m):
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not is_admin(member):
        return await m.reply("❌ Hanya admin.")

    data = await get_chat(m.chat.id)
    if not data["words"]:
        return await m.reply("📭 Kosong.")

    text = "📛 **Daftar Kata Terlarang**\n\n"
    for i, w in enumerate(data["words"], 1):
        text += f"{i}. `{w}`\n"
    await m.reply(text)


@app.on_message(filters.command("autoban") & filters.group)
async def toggle_ab(_, m):
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not is_admin(member):
        return await m.reply("❌ Hanya admin.")

    if len(m.command) < 2:
        return await m.reply("Gunakan: `/autoban on | off | status`")

    if m.command[1] == "on":
        await set_status(m.chat.id, True)
        await m.reply("✅ AutoBan AKTIF")
    elif m.command[1] == "off":
        await set_status(m.chat.id, False)
        await m.reply("❌ AutoBan NONAKTIF")
    elif m.command[1] == "status":
        data = await get_chat(m.chat.id)
        await m.reply(
            f"📊 **AutoBan Status**\n\n"
            f"• Status : {'ON' if data['enabled'] else 'OFF'}\n"
            f"• Badwords : {len(data['words'])}\n"
            f"• Whitelist : {len(data['whitelist'])}"
        )


@app.on_message(filters.command("wl") & filters.group)
async def add_wl(_, m):
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not is_admin(member):
        return await m.reply("❌ Hanya admin.")

    if not m.reply_to_message:
        return await m.reply("Balas pesan user.")

    uid = m.reply_to_message.from_user.id
    await add_whitelist(m.chat.id, uid)
    await m.reply("🛡️ User di-whitelist.")


@app.on_message(filters.command("unwl") & filters.group)
async def del_wl(_, m):
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not is_admin(member):
        return await m.reply("❌ Hanya admin.")

    if not m.reply_to_message:
        return await m.reply("Balas pesan user.")

    uid = m.reply_to_message.from_user.id
    await remove_whitelist(m.chat.id, uid)
    await m.reply("🗑️ User dihapus dari whitelist.")
