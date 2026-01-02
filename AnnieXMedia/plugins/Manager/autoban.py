@Client.on_message(filters.group)
async def test(client, message):
    if message.text == "/autoban":
        await message.reply("KEDETECT")
