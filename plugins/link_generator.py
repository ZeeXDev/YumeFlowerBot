#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from asyncio import TimeoutError
from helper_func import encode, get_message_id, admin

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "Transfère-moi le premier message de la liste (avec la citation)..\n\nOu envoie-moi son lien", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Erreur\n\nCe message ne provient pas de ma chaîne de base de données.", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "Transfère-moi le dernier message de la liste (avec la citation)..\n\nOu envoie-moi son lien", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Erreur\n\nCe message ne provient pas de ma chaîne de base de données", quote = True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Partager le lien", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Voici le lien généré</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(text = "Transfère le message de la chaîne de base de données (avec citation)..\nOu envoie le lien du message de la chaîne", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Erreur\n\nCe message transféré ne provient pas de ma chaîne de base de données ou ce lien n'est pas issu de la chaîne de base de données", quote = True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Partager le lien", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Voici le lien généré</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["ARRÊTER"]], resize_keyboard=True)

    await message.reply("Envoie tous les messages que tu souhaites inclure dans le lot.\n\nAppuie sur ARRÊTER quand tu as terminé.", reply_markup=STOP_KEYBOARD)

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text="En attente de fichiers/messages...\nAppuie sur ARRÊTER pour terminer.",
                timeout=60
            )
        except asyncio.TimeoutError:
            break

        if user_msg.text and user_msg.text.strip().upper() == "ARRÊTER":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(f"❌ Échec du stockage d'un message :\n<code>{e}</code>")
            continue

    await message.reply("✅ Collecte du lot terminée.", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("❌ Aucun message n'a été ajouté au lot.")
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Partager le lien", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(f"<b>Voici le lien de votre lot personnalisé :</b>\n\n{link}", reply_markup=reply_markup)