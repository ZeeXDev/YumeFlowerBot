import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import *
from database.database import db

BAN_SUPPORT = f"{BAN_SUPPORT}"

# ============================================================
# FONCTION DE VÉRIFICATION D'ACCÈS (CORRIGÉE)
# ============================================================

async def get_bot_id(client: Client) -> int:
    """
    Retourne l'ID du bot courant pour le système de sessions.
    Bot mère = 0 (YUMEFLOWER), bot cloné = son ID Telegram.
    """
    try:
        me = await client.get_me()
        bot_real_id = me.id
        cloned = await db.get_cloned_bot(bot_real_id)
        if cloned:
            return bot_real_id  # Bot cloné
        return 0  # Bot mère YUMEFLOWER
    except Exception as e:
        print(f"[get_bot_id] Erreur: {e}")
        return 0


async def get_id_pubs_for_client(client: Client) -> str:
    """Retourne l'ID_PUBS du bot courant pour la Mini App URL."""
    try:
        me = await client.get_me()
        bot_id = me.id
        
        # Vérifier si c'est un bot cloné
        cloned = await db.get_cloned_bot(bot_id)
        if cloned:
            id_data = await db.get_id_codes(bot_id=bot_id)
            if id_data:
                return id_data["id_pubs"]
            else:
                # Bot cloné mais pas d'ID_CODES → erreur grave
                print(f"[get_id_pubs] ERREUR: Bot cloné {bot_id} sans ID_CODES !")
                return None
        
        # C'est le bot mère
        return "YUMEFLOWER"
        
    except Exception as e:
        print(f"[get_id_pubs] Erreur: {e}")
        return None


async def check_user_access(client: Client, user_id: int, message: Message) -> tuple:
    """
    Vérifie si l'utilisateur a accès aux fichiers POUR CE BOT SPÉCIFIQUE.
    Chaque bot a sa propre session par utilisateur.
    Retourne: (has_access: bool, status_message: str or None)
    """
    # Récupérer l'ID du bot courant (0 = bot mère, sinon ID Telegram du cloné)
    bot_id = await get_bot_id(client)
    
    print(f"[DEBUG] ===== check_user_access =====")
    print(f"[DEBUG] user_id: {user_id}")
    print(f"[DEBUG] bot_id from get_bot_id: {bot_id}")
    
    # Vérifier si ce bot_id existe dans cloned_bots
    if bot_id != 0:
        cloned_check = await db.get_cloned_bot(bot_id)
        print(f"[DEBUG] Is cloned bot in DB: {cloned_check is not None}")
        if not cloned_check:
            print(f"[DEBUG] ATTENTION: Bot {bot_id} n'est pas trouvé dans cloned_bots !")

    has_session = await db.has_active_session(user_id, bot_id)
    print(f"[DEBUG] has_active_session({user_id}, {bot_id}) = {has_session}")
    
    if has_session:
        time_left = await db.get_session_time_left(user_id, bot_id)
        
        # Vérifier qu'il reste du temps !
        if time_left > 0:
            minutes = time_left // 60
            seconds = time_left % 60
            session = await db.get_user_session(user_id, bot_id)
            
            type_label = "⭐ PREMIUM" if session.get('type') == 'premium' else "📺 FREE"
            status_msg = f"{type_label} | Temps restant: {minutes}m {seconds}s"
            return True, status_msg
        else:
            # Session existe mais expirée, on la supprime proprement
            await db.deactivate_session(user_id, bot_id)
            print(f"[DEBUG] Session expirée pour user {user_id} bot {bot_id}, désactivation...")
    
    # Pas de session active → proposer la Mini App avec l'ID_PUBS du bon bot
    web_app_url = ADSGRAM_WEBAPP_URL
    
    if not web_app_url:
        web_app_url = f"https://{client.username}.onrender.com"
    
    # Récupérer l'ID_PUBS du bot courant
    id_pubs = await get_id_pubs_for_client(client)
    
    # 🔴 VÉRIFICATION CRITIQUE
    if not id_pubs:
        await message.reply_text(
            "❌ <b>Erreur de configuration</b>\n\n"
            "Le bot n'a pas d'ID_PUBS configuré. Contactez le support.",
            parse_mode=ParseMode.HTML
        )
        return False, None
    
    print(f"[DEBUG] Redirection Mini App: {web_app_url} avec ID_PUBS={id_pubs} bot_id={bot_id}")
    
    # RÉCUPÉRER LE LIEN ORIGINAL pour le bouton "Cliquez ici après la pub"
    orig_post_link = None
    try:
        if message.text and len(message.text) > 7:
            base64_part = message.text.split(" ", 1)[1] if " " in message.text else message.text.split(" ", 1)[0]
            orig_post_link = f"https://t.me/{client.username}?start={base64_part}"
    except:
        pass
    
    # Passer l'ID_PUBS dans l'URL pour que la Mini App sache quel bot
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📺 Débloquer (Regarder Pub)", 
            web_app=WebAppInfo(url=f"{web_app_url}/index.html?id_pubs={id_pubs}")
        )],
        [InlineKeyboardButton(
            "⭐ Devenir Premium", 
            web_app=WebAppInfo(url=f"{web_app_url}/prime.html?id_pubs={id_pubs}")
        )],
        [InlineKeyboardButton(
            "❓ Comment ça marche ?", url="https://t.me/zeexclub/563")]
    ])
    
    # Message avec le lien de retour si disponible
    return_text = (
    "🌸 うぅ… {first}… gomennasai… (T_T)\n\n"
    "Pas de session active… Yume peut pas t'envoyer les fichiers tout de suite ♡\n\n"
    "Regarde juste une petite pub stp～\n"
    "→ 10 min gratuites pour tout télécharger !\n\n"
    "Après, reclique sur le lien et hop, tes fichiers arrivent～ promis !\n\n"
    "Aide Yume ? 👇\n"
    "[Regarder la pub 🚀]"
)
    
    # Ajouter le lien de retour si on l'a récupéré
    if orig_post_link:
        return_text += (
            f"\n\n<b>Reprend ce que tu voulais :</b>\n"
            f"<b> <a href='{orig_post_link}'>Tu Voulais Ceci 🥀🌺</a></b>"
        )
    
    await message.reply_text(return_text, reply_markup=keyboard)
    return False, None


async def determine_media_type(msg):
    """Détermine le type de média et retourne l'action appropriée"""
    if msg.video:
        return ChatAction.UPLOAD_VIDEO
    elif msg.document:
        return ChatAction.UPLOAD_DOCUMENT
    elif msg.photo:
        return ChatAction.UPLOAD_PHOTO
    elif msg.audio:
        return ChatAction.UPLOAD_AUDIO
    else:
        return ChatAction.TYPING


async def send_with_progress(client, message, msg):
    """Envoie le média avec la bonne action et gestion des erreurs"""
    try:
        action = await determine_media_type(msg)
        await client.send_chat_action(message.chat.id, action)
        
        original_caption = msg.caption.html if msg.caption else ""
        caption = f"{original_caption}\n\n{CUSTOM_CAPTION}" if CUSTOM_CAPTION else original_caption
        
        sent_msg = await msg.copy(
            chat_id=message.from_user.id,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None,
            protect_content=PROTECT_CONTENT
        )
        await asyncio.sleep(0.9)
        return sent_msg
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await send_with_progress(client, message, msg)
    except Exception as e:
        print(f"Erreur lors de l'envoi: {e}")
        return None


# ============================================================
# COMMANDE /START (AVEC DEBUG)
# ============================================================

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # DEBUG
    print(f"[DEBUG] Commande /start reçue de user {user_id}")
    print(f"[DEBUG] Texte: {message.text}")

    # Vérification ban
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ Tu as été banni du bot.</b>\n\n"
            "<i>Contacte le support si tu penses que c'est une erreur.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )
    
    # Vérification Force Sub
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    FILE_AUTO_DELETE = await db.get_del_timer()

    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    text = message.text
    
    # Si c'est un lien de fichier (base64)
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return

        # ===== VÉRIFICATION SESSION =====
        print(f"[DEBUG] Vérification accès pour user {user_id}")
        has_access, status_msg = await check_user_access(client, user_id, message)
        print(f"[DEBUG] Résultat: has_access={has_access}")
        
        if not has_access:
            return  # L'utilisateur a reçu les boutons pour débloquer
        # ===== FIN VÉRIFICATION =====

        string = await decode(base64_string)
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return

        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>⏳ Préparation des médias...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("❌ Erreur lors de la récupération des médias")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        sent_messages = []

        for msg in messages:
            sent_msg = await send_with_progress(client, message, msg)
            if sent_msg:
                sent_messages.append(sent_msg)

        # Afficher le statut de session
        if status_msg and sent_messages:
            await message.reply_text(f"<b>✅ {status_msg}</b>")

        # Auto-delete si configuré
        if FILE_AUTO_DELETE > 0 and sent_messages:
            notification_msg = await message.reply(
                f"🌸 うぅ… Abdoul… nonnn… (T_T) 💦\n\n"
    f"<b>❗️ IMPORTANT ❗️</b>\n"
    f"⚠️ Tes fichiers vont disparaître dans {get_exp_time(FILE_AUTO_DELETE)}…\n"
    f"(à cause des droits d'auteur… Yume est trop triste…)\n\n"
    f"📌 Transfère-les vite vite pour pas les perdre, steuplé～ ♡\n"
    f"Yume veut pas que tu sois déçu… aide-moi hein ? ૮₍ ˶•́︿•̀˶ ₎ა\n\n"
    "Vite vite transfère～ !!! 🌷💕"
            )

            await asyncio.sleep(FILE_AUTO_DELETE)

            for snt_msg in sent_messages:
                try:
                    await snt_msg.delete()
                except Exception as e:
                    print(f"Error deleting message {snt_msg.id}: {e}")

            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔄 Récupérer à nouveau", url=reload_url)]]
                ) if reload_url else None

                await notification_msg.edit(
                    "<b>🗑️ Le(s) média(s) a/ont été supprimé(s) !</b>\n\n"
                    "<i>Cliquez ci-dessous pour les récupérer à nouveau</i>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification: {e}")
    
    # Start normal sans fichier
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🌺 Ma maison", url="https://t.me/kingceyy")],
                [
                    InlineKeyboardButton("ℹ️ Groupe de demande", url="https://t.me/+udEvzGuvVLJjNmQ8"),
                    InlineKeyboardButton("❓ Aide", url="https://t.me/Kingcey")]
            ]
        )
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            message_effect_id=5104841245755180586
        )


# ============================================================
# CALLBACK "MA SESSION"
# ============================================================

@Bot.on_callback_query(filters.regex("^check_session$"))
async def check_session_callback(client: Client, callback_query: CallbackQuery):
    """Vérifie et affiche le statut de la session de l'utilisateur"""
    user_id = callback_query.from_user.id
    
    # Récupérer bot_id depuis le client
    try:
        me = await client.get_me()
        cloned = await db.get_cloned_bot(me.id)
        bot_id = me.id if cloned else 0
    except Exception:
        bot_id = 0

    has_session = await db.has_active_session(user_id, bot_id)
    
    if has_session:
        time_left = await db.get_session_time_left(user_id, bot_id)
        minutes = time_left // 60
        seconds = time_left % 60
        session = await db.get_user_session(user_id, bot_id)
        
        type_emoji = "⭐" if session.get('type') == 'premium' else "📺"
        type_text = "PREMIUM" if session.get('type') == 'premium' else "GRATUITE"
        
        text = (
            f"<b>{type_emoji} Session {type_text} Active</b>\n\n"
            f"⏱ Temps restant: <code>{minutes}m {seconds}s</code>\n"
            f"🕐 Expire: <code>{session['expires_at'][:19].replace('T', ' ')}</code>\n\n"
            f"<i>Vous pouvez télécharger des fichiers sans restrictions.</i>"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Rafraîchir", callback_data="check_session")],
            [InlineKeyboardButton("❌ Fermer", callback_data="close")]
        ])
    else:
        web_app_url = ADSGRAM_WEBAPP_URL or f"https://{client.username}.onrender.com"
        
        text = (
            "<b>🔒 Aucune Session Active</b>\n\n"
            "Vous n'avez pas d'accès actif aux fichiers.\n\n"
            "📺 <b>Obtenir l'accès :</b>\n"
            f"• Regardez une pub pour {await db.get_free_session_duration()} min gratuites\n"
            "• Ou passez Premium pour un accès illimité"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📺 Débloquer", web_app=WebAppInfo(url=f"{web_app_url}/index.html"))],
            [InlineKeyboardButton("⭐ Premium", web_app=WebAppInfo(url=f"{web_app_url}/prime.html"))],
            [InlineKeyboardButton("❌ Fermer", callback_data="close")]
        ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()


# ============================================================
# COMMANDE ADMIN /PRIME
# ============================================================

@Bot.on_message(filters.command("prime") & filters.private & admin)
async def give_premium_session(client: Client, message: Message):
    """Donne une session premium à un utilisateur: /prime user_id duration_seconds"""
    try:
        args = message.command
        if len(args) < 3:
            return await message.reply_text(
                "<b>❌ Utilisation incorrecte</b>\n\n"
                "<code>/prime user_id durée_en_secondes</code>\n\n"
                "Exemples:\n"
                "• 1 heure = 3600\n"
                "• 1 jour = 86400\n"
                "• 7 jours = 604800\n\n"
                "<b>Formats acceptés :</b>\n"
                "<code>/prime 123456789 3600</code> (1h)\n"
                "<code>/prime 123456789 86400</code> (1 jour)",
                quote=True
            )
        
        user_id = int(args[1])
        duration = int(args[2])
        
        # Déterminer le bot_id (0 pour bot mère par défaut, ou spécifier)
        bot_id = 0
        if len(args) >= 4:
            bot_id = int(args[3])
        
        # Créer la session premium
        await db.create_premium_session(user_id, duration, message.from_user.id, bot_id)
        
        # Calculer date expiration
        expiry = datetime.now() + timedelta(seconds=duration)
        
        # Répondre à l'admin
        days = duration // 86400
        hours = (duration % 86400) // 3600
        mins = (duration % 3600) // 60
        
        bot_info = f" (Bot ID: {bot_id})" if bot_id != 0 else " (Bot Mère)"
        
        await message.reply_text(
            f"<b>✅ Session Premium Accordée</b>{bot_info}\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Durée:</b> {days}j {hours}h {mins}m\n"
            f"<b>Expire le:</b> <code>{expiry.strftime('%d/%m/%Y %H:%M')}</code>\n\n"
            f"<i>L'utilisateur peut maintenant télécharger sans restrictions.</i>",
            quote=True
        )
        
        # Notifier l'utilisateur
        try:
            await client.send_message(
                user_id,
                "<b>🎉 Félicitations !</b>\n\n"
                f"Vous avez reçu un accès <b>PREMIUM</b> de la part de l'administrateur.\n\n"
                f"⏱ <b>Durée:</b> {days}j {hours}h {mins}m\n"
                f"🕐 <b>Expire le:</b> <code>{expiry.strftime('%d/%m/%Y %H:%M')}</code>\n\n"
                "Profitez de l'accès illimité sans publicités !\n\n"
                f"<i>Par: @{message.from_user.username or message.from_user.id}</i>"
            )
        except Exception as e:
            await message.reply_text(
                f"<b>⚠️ Note:</b> Impossible de notifier l'utilisateur ({e})",
                quote=True
            )
            
    except ValueError:
        await message.reply_text(
            "❌ User ID et durée doivent être des nombres entiers",
            quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ Erreur: <code>{str(e)}</code>", quote=True)


# ============================================================
# COMMANDE ADMIN /DELPRIME - SUPPRIMER UNE SESSION
# ============================================================

@Bot.on_message(filters.command("delprime") & filters.private & admin)
async def delete_premium_session(client: Client, message: Message):
    """Supprime la session d'un utilisateur: /delprime user_id [bot_id]"""
    try:
        args = message.command
        if len(args) < 2:
            return await message.reply_text(
                "<b>❌ Utilisation incorrecte</b>\n\n"
                "<code>/delprime user_id [bot_id]</code>\n\n"
                "<b>Exemple:</b>\n"
                "<code>/delprime 123456789</code>\n"
                "<code>/delprime 123456789 123456789</code> (pour un bot cloné)",
                quote=True
            )
        
        user_id = int(args[1])
        bot_id = int(args[2]) if len(args) >= 3 else 0
        
        # Vérifier si l'utilisateur a une session
        session = await db.get_user_session(user_id, bot_id)
        if not session:
            return await message.reply_text(
                f"<b>⚠️ Aucune session trouvée</b>\n\n"
                f"L'utilisateur <code>{user_id}</code> n'a pas de session active"
                f"{' pour ce bot' if bot_id != 0 else ''}.",
                quote=True
            )
        
        # Supprimer la session
        await db.remove_session(user_id, bot_id)
        
        bot_info = f" (Bot ID: {bot_id})" if bot_id != 0 else " (Bot Mère)"
        
        await message.reply_text(
            f"<b>✅ Session Supprimée</b>{bot_info}\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Type:</b> {session.get('type', 'inconnu').upper()}\n\n"
            f"<i>L'utilisateur doit maintenant regarder une pub ou acheter Premium pour accéder aux fichiers.</i>",
            quote=True
        )
        
        # Notifier l'utilisateur
        try:
            await client.send_message(
                user_id,
                "<b>⏰ Votre session a expiré</b>\n\n"
                "Votre accès Premium/Gratuit a été révoqué par un administrateur.\n\n"
                "Pour continuer à télécharger des fichiers :\n"
                "• 📺 Regardez une publicité\n"
                "• ⭐ Achetez un accès Premium\n\n"
                "<i>Ce message est automatique.</i>"
            )
        except Exception as e:
            await message.reply_text(
                f"<b>⚠️ Note:</b> Impossible de notifier l'utilisateur ({e})",
                quote=True
            )
            
    except ValueError:
        await message.reply_text(
            "❌ User ID doit être un nombre entier",
            quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ Erreur: <code>{str(e)}</code>", quote=True)


# ============================================================
# COMMANDE ADMIN /BROADCAST - DIFFUSION À TOUS LES UTILISATEURS
# ============================================================

@Bot.on_message(filters.command("broadcast") & filters.private & admin)
async def broadcast_message(client: Client, message: Message):
    """
    Diffuse un message à tous les utilisateurs du bot.
    Usage: Répondre à un message avec /broadcast
    """
    # Vérifier si c'est une réponse à un message
    if not message.reply_to_message:
        return await message.reply_text(
            "<b>❌ Utilisation incorrecte</b>\n\n"
            "Cette commande doit être utilisée en réponse à un message.\n\n"
            "<b>Exemple:</b>\n"
            "1. Envoyez ou transférez le message à diffuser\n"
            "2. Répondez à ce message avec <code>/broadcast</code>",
            quote=True
        )
    
    # Confirmation avant envoi
    target_msg = message.reply_to_message
    
    # Compter les utilisateurs
    all_users = await db.full_userbase()
    total_users = len(all_users)
    
    if total_users == 0:
        return await message.reply_text(
            "<b>⚠️ Aucun utilisateur</b>\n\n"
            "La base de données ne contient aucun utilisateur.",
            quote=True
        )
    
    # Message de confirmation
    confirm_msg = await message.reply_text(
        f"<b>📢 Confirmation de diffusion</b>\n\n"
        f"<b>Nombre d'utilisateurs:</b> {total_users}\n"
        f"<b>Type de message:</b> {target_msg.media or 'Texte'}\n\n"
        f"<i>Envoi en cours...</i>",
        quote=True
    )
    
    # Statistiques
    sent_count = 0
    failed_count = 0
    blocked_count = 0
    
    # Envoyer à tous les utilisateurs
    for user_id in all_users:
        try:
            # Copier le message (conserve le formatage, médias, etc.)
            await target_msg.copy(user_id)
            sent_count += 1
            
            # Petite pause pour éviter le rate limit
            await asyncio.sleep(0.1)
            
        except UserIsBlocked:
            blocked_count += 1
            print(f"[BROADCAST] User {user_id} a bloqué le bot")
        except InputUserDeactivated:
            blocked_count += 1
            print(f"[BROADCAST] User {user_id} est désactivé")
        except FloodWait as e:
            await asyncio.sleep(e.x)
            try:
                await target_msg.copy(user_id)
                sent_count += 1
            except:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            print(f"[BROADCAST] Erreur pour user {user_id}: {e}")
    
    # Résultat final
    result_text = (
        f"<b>✅ Diffusion terminée</b>\n\n"
        f"📊 <b>Statistiques:</b>\n"
        f"• ✅ Envoyés: {sent_count}\n"
        f"• ❌ Échoués: {failed_count}\n"
        f"• 🚫 Bloqués/Désactivés: {blocked_count}\n"
        f"• 📊 Total: {total_users}\n\n"
        f"<i>Le message a été diffusé à tous les utilisateurs actifs.</i>"
    )
    
    await confirm_msg.edit_text(result_text)


# ============================================================
# COMMANDE /COMMANDS
# ============================================================

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Fermer", callback_data="close")]])
    await message.reply(text=CMD_TXT, reply_markup=reply_markup, quote=True)


# ============================================================
# FORCE SUB (inchangé)
# ============================================================

chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i>Vérification en cours...</i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await db.show_channels()
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>🔍 Vérification {count}/{len(all_channels)}...</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>❌ Erreur technique</i></b>\n"
                        f"<i>Contactez @ZeeXDevBot</i>\n\n"
                        f"<code>Raison: {e}</code>"
                    )

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='🔄 Vérifier à nouveau',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Final Error: {e}")
        await temp.edit(
            f"<b><i>❌ Erreur critique</i></b>\n"
            f"<i>Contactez @ZeeXDevBot</i>\n\n"
            f"<code>Détails: {e}</code>"
        )
