# Creating the complete gestion.py file with /gestion command

# ==========================================
# SYSTÈME DE CLONAGE - COMMANDE /GESTION
# ==========================================

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
from bot import Bot
from config import OWNER_ID
from database.database import db


# ============================================================
# VÉRIFICATION DES RÔLES
# ============================================================

async def check_role(user_id: int, bot_id: int = None) -> str:
    """
    Vérifie le rôle d'un utilisateur
    Retourne: 'owner', 'maitre', 'admin', ou None
    """
    if user_id == OWNER_ID:
        return 'owner'
    
    if bot_id:
        role = await db.get_user_bot_role(bot_id, user_id)
        if role:
            return role
    
    return None


# ============================================================
# COMMANDE /GESTION
# ============================================================

@Bot.on_message(filters.command('gestion') & filters.private)
async def gestion_command(client: Bot, message: Message):
    """
    Commande /gestion - Interface de gestion pour MAITRE et ADMIN
    Permet de personnaliser le bot cloné
    """
    user_id = message.from_user.id
    
    # Vérifier si l'utilisateur est OWNER
    if user_id == OWNER_ID:
        # Owner peut gérer tous les bots
        bots = await db.get_all_cloned_bots()
        if not bots:
            return await message.reply_text(
                "<b>❌ Aucun bot cloné</b>\n\n"
                "Il n'y a pas encore de bots clonés dans le système.",
                quote=True
            )
        
        # Afficher la liste des bots pour l'owner
        buttons = []
        for bot in bots:
            buttons.append([InlineKeyboardButton(
                f"🤖 @{bot['bot_username']}",
                callback_data=f"gestion_select_{bot['_id']}"
            )])
        
        buttons.append([InlineKeyboardButton("❌ Fermer", callback_data="close")])
        
        return await message.reply_text(
            "<b>⚙️ Gestion des Bots Clonés</b>\n\n"
            "Sélectionnez un bot à gérer:",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    
    # Vérifier si l'utilisateur est MAITRE ou ADMIN d'au moins un bot
    user_bots = []
    all_bots = await db.get_all_cloned_bots()
    
    for bot in all_bots:
        role = await db.get_user_bot_role(bot['_id'], user_id)
        if role in ['maitre', 'admin']:
            user_bots.append({**bot, 'role': role})
    
    if not user_bots:
        return await message.reply_text(
            "<b>⛔ Accès refusé</b>\n\n"
            "Vous n'êtes pas MAITRE ou ADMIN d'un bot cloné.\n"
            "Créez d'abord un bot avec <code>/clone</code>",
            quote=True
        )
    
    # Si l'utilisateur a plusieurs bots, lui faire choisir
    if len(user_bots) > 1:
        buttons = []
        for bot in user_bots:
            role_emoji = "👑" if bot['role'] == 'maitre' else "👤"
            buttons.append([InlineKeyboardButton(
                f"{role_emoji} @{bot['bot_username']}",
                callback_data=f"gestion_select_{bot['_id']}"
            )])
        
        buttons.append([InlineKeyboardButton("❌ Fermer", callback_data="close")])
        
        return await message.reply_text(
            "<b>⚙️ Sélectionnez un bot à gérer</b>\n\n"
            "👑 = Maître | 👤 = Admin",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    
    # Un seul bot, ouvrir directement le menu de gestion
    await show_gestion_menu(message, user_bots[0]['_id'], user_id)


async def show_gestion_menu(message_or_callback, bot_id: int, user_id: int):
    """Affiche le menu de gestion d'un bot"""
    bot_data = await db.get_cloned_bot(bot_id)
    if not bot_data:
        text = "<b>❌ Bot non trouvé</b>"
        if isinstance(message_or_callback, CallbackQuery):
            return await message_or_callback.message.edit_text(text)
        return await message_or_callback.reply_text(text)
    
    role = await check_role(user_id, bot_id)
    role_display = {
        'owner': '👑 Propriétaire',
        'maitre': '👑 Maître',
        'admin': '👤 Admin'
    }.get(role, '❓ Inconnu')
    
    # Récupérer les ID codes
    id_codes = await db.get_id_codes(bot_id=bot_id)
    
    settings = bot_data.get('settings', {})
    
    text = (
        f"<b>⚙️ Gestion du Bot</b>\n\n"
        f"🤖 <b>Bot:</b> @{bot_data['bot_username']}\n"
        f"{role_display}\n\n"
        f"🆔 <b>ID_PUBS:</b> <code>{id_codes['id_pubs'] if id_codes else 'N/A'}</code>\n"
        f"🔑 <b>ID_CODE:</b> <code>{id_codes['id_code'] if id_codes else 'N/A'}</code>\n\n"
        f"<b>Configuration actuelle:</b>\n"
        f"📸 Photo: {'✅' if settings.get('start_photo') else '❌'}\n"
        f"💬 Message: {'✅' if settings.get('start_message') else '❌ (défaut)'}\n"
        f"🔘 Boutons: {len(settings.get('custom_buttons', []))} ajouté(s)\n"
        f"📢 Canal DB: {'✅' if settings.get('channel_id') else '❌'}\n"
        f"📌 Force Sub: {len(settings.get('force_sub_channels', []))} canal(aux)\n\n"
        f"<i>Utilisez les boutons ci-dessous pour personnaliser</i>"
    )
    
    # Boutons de gestion
    buttons = [
        [
            InlineKeyboardButton("📸 Photo démarrage", callback_data=f"gestion_photo_{bot_id}"),
            InlineKeyboardButton("💬 Message démarrage", callback_data=f"gestion_msg_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔘 Boutons", callback_data=f"gestion_buttons_{bot_id}"),
            InlineKeyboardButton("📢 Canal DB", callback_data=f"gestion_channel_{bot_id}")
        ],
        [
            InlineKeyboardButton("📌 Force Sub", callback_data=f"gestion_fsub_{bot_id}"),
            InlineKeyboardButton("👥 Admins", callback_data=f"gestion_admins_{bot_id}")
        ]
    ]
    
    # Boutons spéciaux pour MAITRE et OWNER
    if role in ['owner', 'maitre']:
        buttons.append([
            InlineKeyboardButton("💰 Gains", callback_data=f"gestion_earnings_{bot_id}"),
            InlineKeyboardButton("📊 Stats", callback_data=f"gestion_stats_{bot_id}")
        ])
        buttons.append([
            InlineKeyboardButton("🔄 Régénérer ID_CODE", callback_data=f"gestion_regen_{bot_id}")
        ])
    
    buttons.append([InlineKeyboardButton("❌ Fermer", callback_data="close")])
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message_or_callback.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ============================================================
# CALLBACKS GESTION
# ============================================================

@Bot.on_callback_query(filters.regex(r"^gestion_select_(\d+)$"))
async def gestion_select_callback(client: Bot, callback: CallbackQuery):
    """Sélection d'un bot à gérer"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    # Vérifier les permissions
    role = await check_role(user_id, bot_id)
    if not role:
        return await callback.answer("⛔ Vous n'avez pas accès à ce bot", show_alert=True)
    
    await show_gestion_menu(callback, bot_id, user_id)
    await callback.answer()


@Bot.on_callback_query(filters.regex(r"^gestion_photo_(\d+)$"))
async def gestion_photo_callback(client: Bot, callback: CallbackQuery):
    """Gestion de la photo de démarrage"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if not role:
        return await callback.answer("⛔ Accès refusé", show_alert=True)
    
    text = (
        "<b>📸 Photo de démarrage</b>\n\n"
        "Envoyez une photo pour définir l'image de démarrage de votre bot.\n\n"
        "<b>Options:</b>\n"
        "• Envoyez une photo pour la définir\n"
        "• Envoyez <code>/supprimer</code> pour supprimer\n"
        "• Envoyez <code>/annuler</code> pour annuler\n\n"
        "<i>La photo sera affichée avec le message de démarrage</i>"
    )
    
    buttons = [[InlineKeyboardButton("‹ Retour", callback_data=f"gestion_select_{bot_id}")]]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()
    
    # Stocker l'état pour la prochaine réponse
    # Note: Dans une implémentation complète, utiliser un système de FSM ou de sessions


@Bot.on_callback_query(filters.regex(r"^gestion_msg_(\d+)$"))
async def gestion_msg_callback(client: Bot, callback: CallbackQuery):
    """Gestion du message de démarrage"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if not role:
        return await callback.answer("⛔ Accès refusé", show_alert=True)
    
    bot_data = await db.get_cloned_bot(bot_id)
    current_msg = bot_data.get('settings', {}).get('start_message', 'Non défini (utilise le message par défaut)')
    
    text = (
        f"<b>💬 Message de démarrage</b>\n\n"
        f"<b>Actuel:</b>\n{current_msg}\n\n"
        f"<b>Variables disponibles:</b>\n"
        f"• {{first}} - Prénom de l'utilisateur\n"
        f"• {{last}} - Nom de famille\n"
        f"• {{username}} - Nom d'utilisateur\n"
        f"• {{mention}} - Mention\n"
        f"• {{id}} - ID utilisateur\n\n"
        f"Envoyez le nouveau message ou <code>/annuler</code>"
    )
    
    buttons = [
        [InlineKeyboardButton("🔄 Réinitialiser", callback_data=f"gestion_resetmsg_{bot_id}")],
        [InlineKeyboardButton("‹ Retour", callback_data=f"gestion_select_{bot_id}")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()


@Bot.on_callback_query(filters.regex(r"^gestion_buttons_(\d+)$"))
async def gestion_buttons_callback(client: Bot, callback: CallbackQuery):
    """Gestion des boutons inline"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if not role:
        return await callback.answer("⛔ Accès refusé", show_alert=True)
    
    bot_data = await db.get_cloned_bot(bot_id)
    buttons_list = bot_data.get('settings', {}).get('custom_buttons', [])
    
    text = (
        f"<b>🔘 Boutons personnalisés</b>\n\n"
        f"<b>Boutons actuels ({len(buttons_list)}):</b>\n"
    )
    
    for i, btn in enumerate(buttons_list, 1):
        text += f"{i}. {btn['text']} → {btn['url']}\n"
    
    text += (
        f"\n<b>Note:</b> Le bouton '🤖 Créé Votre Propre Bot' est toujours présent.\n\n"
        f"<b>Format pour ajouter:</b>\n"
        f"<code>Titre du bouton - https://lien.com</code>"
    )
    
    buttons = [
        [InlineKeyboardButton("➕ Ajouter un bouton", callback_data=f"gestion_addbtn_{bot_id}")],
        [InlineKeyboardButton("🗑️ Supprimer un bouton", callback_data=f"gestion_delbtn_{bot_id}")],
        [InlineKeyboardButton("‹ Retour", callback_data=f"gestion_select_{bot_id}")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()


@Bot.on_callback_query(filters.regex(r"^gestion_channel_(\d+)$"))
async def gestion_channel_callback(client: Bot, callback: CallbackQuery):
    """Gestion du canal DB"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if not role:
        return await callback.answer("⛔ Accès refusé", show_alert=True)
    
    bot_data = await db.get_cloned_bot(bot_id)
    channel_id = bot_data.get('settings', {}).get('channel_id')
    
    text = (
        f"<b>📢 Canal de Base de Données (DB)</b>\n\n"
        f"<b>Actuel:</b> <code>{channel_id if channel_id else 'Non configuré'}</code>\n\n"
        f"<b>Instructions:</b>\n"
        f"1. Créez un canal privé\n"
        f"2. Ajoutez votre bot comme administrateur\n"
        f"3. Envoyez ici l'ID du canal (ex: -1001234567890)\n\n"
        f"<b>⚠️ Important:</b> Le bot doit être admin du canal!"
    )
    
    buttons = [
        [InlineKeyboardButton("🔄 Modifier", callback_data=f"gestion_setchannel_{bot_id}")],
        [InlineKeyboardButton("‹ Retour", callback_data=f"gestion_select_{bot_id}")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()


@Bot.on_callback_query(filters.regex(r"^gestion_regen_(\d+)$"))
async def gestion_regen_callback(client: Bot, callback: CallbackQuery):
    """Régénérer ID_CODE"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if role not in ['owner', 'maitre']:
        return await callback.answer("⛔ Seul le MAITRE peut faire ça", show_alert=True)
    
    new_codes = await db.regenerate_id_code(bot_id, user_id)
    
    if new_codes:
        await callback.answer("✅ ID_CODE régénéré avec succès!", show_alert=True)
        await show_gestion_menu(callback, bot_id, user_id)
    else:
        await callback.answer("❌ Erreur lors de la régénération", show_alert=True)


@Bot.on_callback_query(filters.regex(r"^gestion_earnings_(\d+)$"))
async def gestion_earnings_callback(client: Bot, callback: CallbackQuery):
    """Affiche les gains"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if role not in ['owner', 'maitre']:
        return await callback.answer("⛔ Accès refusé", show_alert=True)
    
    earnings = await db.get_bot_earnings(bot_id)
    bot_data = await db.get_cloned_bot(bot_id)
    
    if not earnings:
        return await callback.answer("❌ Données non trouvées", show_alert=True)
    
    text = (
        f"<b>💰 Gains du Bot</b>\n\n"
        f"🤖 @{bot_data['bot_username']}\n\n"
        f"💵 <b>Solde actuel:</b> ${earnings['balance']:.2f}\n"
        f"💰 <b>Total gagné:</b> ${earnings['total_earned']:.2f}\n"
        f"💸 <b>Total retiré:</b> ${earnings['total_withdrawn']:.2f}\n\n"
        f"<b>🎯 Seuil de retrait:</b> $7.00\n"
    )
    
    if earnings['balance'] >= 7.0:
        text += "\n✅ <b>Vous pouvez retirer vos gains!</b>"
        buttons = [[InlineKeyboardButton("💸 Retirer", callback_data=f"gestion_withdraw_{bot_id}")]]
    else:
        missing = 7.0 - earnings['balance']
        text += f"\n❌ Encore ${missing:.2f} nécessaires pour retirer"
        buttons = []
    
    buttons.append([InlineKeyboardButton("‹ Retour", callback_data=f"gestion_select_{bot_id}")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()


@Bot.on_callback_query(filters.regex(r"^gestion_stats_(\d+)$"))
async def gestion_stats_callback(client: Bot, callback: CallbackQuery):
    """Affiche les statistiques"""
    bot_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    role = await check_role(user_id, bot_id)
    if not role:
        return await callback.answer("⛔ Accès refusé", show_alert=True)
    
    bot_data = await db.get_cloned_bot(bot_id)
    stats = bot_data.get('stats', {})
    
    text = (
        f"<b>📊 Statistiques du Bot</b>\n\n"
        f"🤖 @{bot_data['bot_username']}\n\n"
        f"👥 <b>Utilisateurs totaux:</b> {stats.get('total_users', 0)}\n"
        f"📁 <b>Fichiers envoyés:</b> {stats.get('total_files_sent', 0)}\n"
        f"📺 <b>Pub regardées:</b> {stats.get('total_ads_watched', 0)}\n\n"
        f"📅 <b>Créé le:</b> {bot_data['created_at'][:10]}\n"
        f"{'✅ Actif' if bot_data.get('is_active') else '❌ Inactif'}"
    )
    
    buttons = [[InlineKeyboardButton("‹ Retour", callback_data=f"gestion_select_{bot_id}")]]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()
