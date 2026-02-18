# Creating the cloned bot handler (plugins/cloned/start.py) - COMPLETE VERSION
# ==========================================
# HANDLER POUR BOTS CLONÉS - START
# ==========================================

import asyncio
import base64
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from database.database import db
from config import ADSGRAM_WEBAPP_URL, FREE_SESSION_DURATION


async def get_clone_settings(bot_id: int):
    """Récupère les paramètres personnalisés du bot cloné"""
    bot_data = await db.get_cloned_bot(bot_id)
    if bot_data:
        return bot_data.get('settings', {})
    return {}


async def build_start_keyboard(bot_id: int, bot_username: str, user_id: int):
    """Construit le clavier de démarrage avec les boutons personnalisés"""
    settings = await get_clone_settings(bot_id)
    custom_buttons = settings.get('custom_buttons', [])
    
    keyboard = []
    
    # Ajouter les boutons personnalisés
    for btn in custom_buttons:
        keyboard.append([InlineKeyboardButton(btn['text'], url=btn['url'])])
    
    # Bouton pour vérifier la session
    keyboard.append([InlineKeyboardButton("📺 Ma Session", callback_data="check_session")])
    
    # Bouton obligatoire "Créer votre propre bot"
    # Le lien pointe vers le bot mère avec paramètre clone
    # Note: Le bot_username ici doit être celui du bot mère, pas du clone
    # On utilisera une variable d'environnement ou une config
    mother_bot = "YumeFlowerBot"  # À remplacer par le vrai username
    keyboard.append([InlineKeyboardButton(
        "🤖 Créé Votre Propre Bot",
        url=f"https://t.me/{mother_bot}?start=clone"
    )])
    
    return InlineKeyboardMarkup(keyboard)


async def get_start_message(bot_id: int, user):
    """Récupère le message de démarrage personnalisé ou par défaut"""
    settings = await get_clone_settings(bot_id)
    custom_msg = settings.get('start_message')
    
    if custom_msg:
        # Formater avec les variables utilisateur
        return custom_msg.format(
            first=user.first_name,
            last=user.last_name or '',
            username=user.username or '',
            mention=user.mention,
            id=user.id
        )
    
    # Message par défaut
    return (
        f"<b>👋 Bienvenue, {user.first_name} !</b>\n\n"
        f"Ce bot vous permet de récupérer des fichiers.\n\n"
        f"<b>📺 Comment ça marche ?</b>\n"
        f"1. Recevez un lien de fichier\n"
        f"2. Cliquez sur le lien\n"
        f"3. Regardez une pub pour débloquer l'accès\n\n"
        f"<i>Propulsé <a href='https://t.me/Kingceyy'>Kingcey</a></i>"
    )


async def get_start_photo(bot_id: int):
    """Récupère la photo de démarrage personnalisée ou None"""
    settings = await get_clone_settings(bot_id)
    return settings.get('start_photo')


@Client.on_message(filters.command('start') & filters.private)
async def cloned_start_handler(client, message: Message):
    """Handler /start pour bots clonés"""
    bot_id = client.me.id
    bot_username = client.me.username
    user_id = message.from_user.id
    
    # Vérifier si c'est un lien de fichier
    if len(message.text) > 7 and ' ' in message.text:
        # Traitement du lien de fichier
        await handle_file_link(client, message)
        return
    
    # Message de démarrage normal
    start_msg = await get_start_message(bot_id, message.from_user)
    start_photo = await get_start_photo(bot_id)
    keyboard = await build_start_keyboard(bot_id, bot_username, user_id)
    
    try:
        if start_photo:
            await message.reply_photo(
                photo=start_photo,
                caption=start_msg,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                start_msg,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        print(f"[CLONE {bot_id}] Error in start: {e}")
        await message.reply_text(
            "<b>👋 Bienvenue !</b>\n\nUtilisez les boutons ci-dessous.",
            reply_markup=keyboard
        )


async def handle_file_link(client, message: Message):
    """Gère les liens de fichiers pour les bots clonés"""
    bot_id = client.me.id
    bot_username = client.me.username
    user_id = message.from_user.id
    
    # Extraire le base64 du lien
    try:
        base64_string = message.text.split(" ", 1)[1]
    except IndexError:
        return
    
    # Vérifier si l'utilisateur a une session active pour CE bot
    has_access = await db.has_active_session(user_id, bot_id)
    
    if not has_access:
        # Récupérer l'ID_PUBS du bot
        id_codes = await db.get_id_codes(bot_id=bot_id)
        id_pubs = id_codes['id_pubs'] if id_codes else 'N/A'
        
        # Rediriger vers la Mini App avec l'ID_PUBS
        web_app_url = ADSGRAM_WEBAPP_URL or f"https://{bot_username}.onrender.com"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📺 Débloquer (Regarder Pub)",
                web_app=WebAppInfo(url=f"{web_app_url}/index.html?id_pubs={id_pubs}")
            )],
            [InlineKeyboardButton(
                "⭐ Devenir Premium",
                web_app=WebAppInfo(url=f"{web_app_url}/prime.html?id_pubs={id_pubs}")
            )]
        ])
        
        await message.reply_text(
            f"<b>🔒 ACCÈS BLOQUÉ</b>\n\n"
            f"Vous n'avez pas de session active pour ce bot.\n\n"
            f"<b>🆔 ID_PUBS:</b> <code>{id_pubs}</code>\n\n"
            f"<b>1️⃣ Version Gratuite 🆓</b>\n"
            f"   • Regardez une pub pour débloquer\n"
            f"   • ⏱️ Accès gratuit pendant {await db.get_free_session_duration()} minutes\n\n"
            f"<b>2️⃣ Version Premium ⭐</b>\n"
            f"   • 🔓 Accès immédiat sans publicité\n"
            f"   • ⏳ Durée illimitée\n\n"
            f"<i>👇 Cliquez ci-dessous :</i>",
            reply_markup=keyboard
        )
        return
    
    # L'utilisateur a accès, récupérer le fichier
    try:
        string = await decode(base64_string)
        argument = string.split("-")
        
        # Récupérer le canal DB du bot cloné
        settings = await get_clone_settings(bot_id)
        channel_id = settings.get('channel_id')
        
        if not channel_id:
            await message.reply_text("<b>❌ Erreur:</b> Canal DB non configuré.")
            return
        
        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(channel_id))
                end = int(int(argument[2]) / abs(channel_id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(channel_id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return
        
        # Récupérer et envoyer les messages
        messages = await get_messages(client, channel_id, ids)
        
        for msg in messages:
            try:
                await msg.copy(chat_id=user_id)
                await db.increment_bot_stat(bot_id, 'total_files_sent')
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(chat_id=user_id)
            except Exception as e:
                print(f"Error sending message: {e}")
        
        # Afficher le temps restant
        time_left = await db.get_session_time_left(user_id, bot_id)
        if time_left > 0:
            minutes = time_left // 60
            seconds = time_left % 60
            await message.reply_text(
                f"<b>✅ Fichiers envoyés!</b>\n\n"
                f"⏱️ Temps restant: {minutes}m {seconds}s"
            )
            
    except Exception as e:
        print(f"Error handling file link: {e}")
        await message.reply_text("<b>❌ Erreur lors de la récupération des fichiers.</b>")


async def decode(base64_string):
    """Décode une chaîne base64"""
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    return string_bytes.decode("ascii")


async def get_messages(client, channel_id, message_ids):
    """Récupère plusieurs messages d'un canal"""
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temp_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(chat_id=channel_id, message_ids=temp_ids)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(chat_id=channel_id, message_ids=temp_ids)
        except Exception as e:
            print(f"Error getting messages: {e}")
            break
        total_messages += len(temp_ids)
        messages.extend(msgs)
    return messages


@Client.on_callback_query(filters.regex("^check_session$"))
async def check_session_callback(client, callback_query):
    """Vérifie la session de l'utilisateur"""
    bot_id = client.me.id
    user_id = callback_query.from_user.id
    
    has_session = await db.has_active_session(user_id, bot_id)
    
    if has_session:
        time_left = await db.get_session_time_left(user_id, bot_id)
        minutes = time_left // 60
        seconds = time_left % 60
        
        await callback_query.message.edit_text(
            f"<b>📺 Session Active</b>\n\n"
            f"⏱️ Temps restant: {minutes}m {seconds}s\n\n"
            f"<i>Vous pouvez récupérer des fichiers.</i>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Rafraîchir", callback_data="check_session")],
                [InlineKeyboardButton("❌ Fermer", callback_data="close")]
            ])
        )
    else:
        id_codes = await db.get_id_codes(bot_id=bot_id)
        id_pubs = id_codes['id_pubs'] if id_codes else 'N/A'
        web_app_url = ADSGRAM_WEBAPP_URL or f"https://{client.me.username}.onrender.com"
        
        await callback_query.message.edit_text(
            f"<b>🔒 Aucune Session Active</b>\n\n"
            f"🆔 ID_PUBS: <code>{id_pubs}</code>\n\n"
            f"Regardez une pub pour débloquer l'accès.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "📺 Débloquer",
                    web_app=WebAppInfo(url=f"{web_app_url}/index.html?id_pubs={id_pubs}")
                )],
                [InlineKeyboardButton("❌ Fermer", callback_data="close")]
            ])
        )
    
    await callback_query.answer()


@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client, callback_query):
    """Ferme le message"""
    await callback_query.message.delete()
    await callback_query.answer()
