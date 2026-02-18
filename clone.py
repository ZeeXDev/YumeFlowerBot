# Creating the complete clone.py file with /clone command

# ==========================================
# SYSTÈME DE CLONAGE - COMMANDE /CLONE
# ==========================================

import asyncio
import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import AccessTokenInvalid, FloodWait
from bot import Bot
from config import OWNER_ID, APP_ID, API_HASH
from helper_func import admin
from database.database import db

# Stockage des clients clonés en mémoire
cloned_clients = {}


async def get_bot_info(token: str):
    """Récupère les informations d'un bot à partir de son token"""
    temp_client = Client(
        name="temp_bot",
        api_id=APP_ID,
        api_hash=API_HASH,
        bot_token=token,
        no_updates=True
    )
    
    try:
        await temp_client.start()
        me = await temp_client.get_me()
        await temp_client.stop()
        return {
            'success': True,
            'id': me.id,
            'username': me.username,
            'first_name': me.first_name
        }
    except AccessTokenInvalid:
        return {'success': False, 'error': 'Token invalide'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@Bot.on_message(filters.command('clone') & filters.private)
async def clone_bot_command(client: Bot, message: Message):
    """
    Commande /clone - Permet de cloner le bot
    Usage: /clone {BOT_TOKEN}
    Exemple: /clone 89171999:HKqjakakxxxxxxxxxxxxx
    """
    user_id = message.from_user.id
    
    # Vérifier les arguments
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Format incorrect</b>\n\n"
            "<b>Usage:</b> <code>/clone {BOT_TOKEN}</code>\n\n"
            "<b>Exemple:</b>\n"
            "<code>/clone 89171999:HKqjakakxxxxxxxxxxxxx</code>\n\n"
            "<i>Obtenez votre token depuis @BotFather</i>",
            quote=True
        )
    
    bot_token = message.command[1].strip()
    
    # Vérifier si le token est déjà utilisé
    existing_bot = await db.get_cloned_bot_by_token(bot_token)
    if existing_bot:
        return await message.reply_text(
            "<b>❌ Ce bot est déjà cloné!</b>\n\n"
            f"Le bot @{existing_bot['bot_username']} existe déjà dans le système.",
            quote=True
        )
    
    # Message de traitement
    processing_msg = await message.reply_text(
        "<b>🔄 Vérification du token...</b>\n"
        "<i>Veuillez patienter</i>",
        quote=True
    )
    
    # Vérifier le token et récupérer les infos
    bot_info = await get_bot_info(bot_token)
    
    if not bot_info['success']:
        return await processing_msg.edit_text(
            f"<b>❌ Erreur lors de la vérification</b>\n\n"
            f"<code>{bot_info['error']}</code>\n\n"
            "<i>Vérifiez que le token est correct et que le bot n'est pas déjà utilisé ailleurs.</i>"
        )
    
    await processing_msg.edit_text(
        "<b>✅ Token valide!</b>\n"
        f"<b>Bot:</b> @{bot_info['username']}\n"
        "<i>Création du clone...</i>"
    )
    
    try:
        # Créer l'entrée dans la base de données
        clone_data = await db.create_cloned_bot(
            bot_token=bot_token,
            master_id=user_id,
            bot_username=bot_info['username'],
            bot_id=bot_info['id'],
            api_id=APP_ID,
            api_hash=API_HASH
        )
        
        # Démarrer le bot cloné
        success = await start_cloned_bot(bot_info['id'])
        
        if success:
            await processing_msg.edit_text(
                f"<b>🎉 Bot cloné avec succès!</b>\n\n"
                f"<b>🤖 Bot:</b> @{bot_info['username']}\n"
                f"<b>👤 Maître:</b> <code>{user_id}</code>\n"
                f"<b>🆔 ID_PUBS:</b> <code>{clone_data['id_pubs']}</code>\n"
                f"<b>🔑 ID_CODE:</b> <code>{clone_data['id_code']}</code>\n\n"
                f"<b>⚠️ IMPORTANT:</b>\n"
                f"• Conservez votre <code>ID_CODE</code> précieusement\n"
                f"• Il permet d'accéder à la page Maître\n"
                f"• Ne le partagez avec personne\n\n"
                f"<b>📝 Prochaines étapes:</b>\n"
                f"1. Utilisez <code>/gestion</code> pour personnaliser\n"
                f"2. Configurez votre canal DB\n"
                f"3. Partagez votre <code>ID_PUBS</code> aux utilisateurs",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚙️ Gérer mon bot", callback_data=f"gestion_{bot_info['id']}")]
                ])
            )
        else:
            await processing_msg.edit_text(
                f"<b>⚠️ Bot créé mais non démarré</b>\n\n"
                f"Le bot @{bot_info['username']} a été enregistré mais n'a pas pu démarrer.\n"
                f"Contactez l'administrateur."
            )
            
    except Exception as e:
        await processing_msg.edit_text(
            f"<b>❌ Erreur lors du clonage</b>\n\n"
            f"<code>{str(e)}</code>"
        )


async def start_cloned_bot(bot_id: int) -> bool:
    """Démarre un bot cloné"""
    try:
        bot_data = await db.get_cloned_bot(bot_id)
        if not bot_data:
            return False
        
        # Créer le client
        client = Client(
            name=f"cloned_bot_{bot_id}",
            api_id=APP_ID,
            api_hash=API_HASH,
            bot_token=bot_data['bot_token'],
            plugins={"root": "plugins/cloned"}  # Plugins spéciaux pour bots clonés
        )
        
        await client.start()
        cloned_clients[bot_id] = client
        
        print(f"[CLONE] Bot @{bot_data['bot_username']} démarré (ID: {bot_id})")
        return True
        
    except Exception as e:
        print(f"[CLONE ERROR] Impossible de démarrer le bot {bot_id}: {e}")
        return False


async def stop_cloned_bot(bot_id: int) -> bool:
    """Arrête un bot cloné"""
    try:
        if bot_id in cloned_clients:
            await cloned_clients[bot_id].stop()
            del cloned_clients[bot_id]
            print(f"[CLONE] Bot {bot_id} arrêté")
        return True
    except Exception as e:
        print(f"[CLONE ERROR] Erreur arrêt bot {bot_id}: {e}")
        return False


async def restart_all_cloned_bots():
    """Redémarre tous les bots clonés au démarrage du bot mère"""
    print("[CLONE] Redémarrage des bots clonés...")
    bots = await db.get_all_cloned_bots()
    
    started = 0
    failed = 0
    
    for bot_data in bots:
        if bot_data.get('is_active', True):
            success = await start_cloned_bot(bot_data['_id'])
            if success:
                started += 1
            else:
                failed += 1
            await asyncio.sleep(1)  # Éviter le flood
    
    print(f"[CLONE] {started} bots démarrés, {failed} échecs")
    return started, failed


# Démarrer tous les bots clonés au lancement
async def init_cloned_bots():
    """Initialise tous les bots clonés au démarrage"""
    await restart_all_cloned_bots()
