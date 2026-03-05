#Cluster0 Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >..
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import os
from os import environ, getenv
import logging
from logging.handlers import RotatingFileHandler

# ==========================================
# CONFIGURATION BOT TELEGRAM
# ==========================================

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8020965278:AAEdbGIXLo8s3PAhqzJSDnSRCS5UCq68qGU")
APP_ID = int(os.environ.get("APP_ID", "25926022"))
API_HASH = os.environ.get("API_HASH", "30db27d9e56d854fb5e943723268db32")

# ==========================================
# CONFIGURATION BASE DE DONNÉES & CHANNEL
# ==========================================

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003173430503"))
OWNER = os.environ.get("OWNER", "ZeeXDevBot")
OWNER_ID = int(os.environ.get("OWNER_ID", "8140299716"))

# Base de données MongoDB (optionnel, pour futur scaling)
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://elisabethboko45_db_user:kmrLKNKnfe8lK1df@cluster0.isv90ao.mongodb.net/?appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "Cluster0")

# ==========================================
# CONFIGURATION SERVEUR WEB & MINI APP
# ==========================================

PORT = os.environ.get("PORT", "8001")

# URL de la Mini App (laisser vide pour auto-détection: https://{bot_username}.onrender.com)
# Exemple: https://monbot.onrender.com
ADSGRAM_WEBAPP_URL = "https://waramugi.vercel.app"  # Ton URL Vercel


# Mot de passe pour accéder à la page admin (/admin)
# IMPORTANT: Changez ceci en production!
ADMIN_PASSWORD = "kingcey00"

# Durée des sessions gratuites en MINUTES (défaut: 10 minutes)
# Anciennement en heures pour AdsGram, maintenant en minutes pour plus de flexibilité
FREE_SESSION_DURATION = int(os.environ.get("FREE_SESSION_DURATION", "10"))

# ==========================================
# CONFIGURATION FORCE SUB & LIENS
# ==========================================

FSUB_LINK_EXPIRY = int(getenv("FSUB_LINK_EXPIRY", "840"))
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/BTZF_CHAT")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))

# ==========================================
# MÉDIAS & IMAGES
# ==========================================

START_PIC = os.environ.get("START_PIC", "https://files.catbox.moe/tor45x.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://files.catbox.moe/42lm1v.jpg")

# ==========================================
# TEXTES & MESSAGES
# ==========================================

HELP_TXT = "<b><blockquote>◈ 🌸 Kyaa～ ! Salut Abdoul ! ૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა ♡  \nMoi c'est YumeFlower～ la petite fleur magique qui garde tous tes animes et mangas préférés ! 🌷💕  \nC'est un bot open-source propulsé par @kingceyy～\nJe t'offre plein de jolis fichiers d'animes/manga, juste pour toi～ !  \nViens jouer avec moi tous les jours, hein ? On va regarder des trucs trop kawaii ensemble～ !!! ✨\nNya\~ ♡</blockquote></b>"

ABOUT_TXT = "<b>✨ YumeFlower — plus qu'un bot ✨</b>\n\n<blockquote>Tu crois que tu utilises juste un bot pour télécharger des animes ?\nNon. Tu es assis sur une mine d'or. 💰</blockquote>\n\n<b>🌸 CLONE TON PROPRE BOT</b>\n\n<blockquote>En une seule commande — /clone — tu obtiens ton propre bot.\nTon nom. Ton image. Ta communauté.\nPersonne ne peut te le prendre. Il t'appartient.</blockquote>\n\n<b>💸 ET TU GAGNES DE L'ARGENT. VRAIMENT.</b>\n\n<blockquote>Chaque utilisateur qui regarde une pub sur ton bot ?\n→ Tu gagnes. Automatiquement. Sans rien faire.\n\n1</b>\navec un cpm allant à 2$\nGagne jusqu'à meme 300$/mois</b>\n\nÇa tourne 24h/24, même quand tu dors. 😴💤</blockquote>\n\n<b>🚀 POURQUOI ATTENDRE ?</b>\n\n<blockquote>➤ Gratuit. Illimité. Instantané.\n➤ Aucune compétence requise.\n➤ Ton bot, tes règles, ton argent.</blockquote>\n\nTape <b>/clone</b> et rejoins ceux qui ont déjà compris. 🌸"

START_MSG = os.environ.get("START_MESSAGE", 
    "<b><blockquote>Nyaaaa～ !!! ♡(≧▽≦)♡\nKonnnnichiwaaaa {first}</b></blockquote>\nMoi c\'est YumeFlower～ la plus mignonne des bots de stockage ૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა🌸\n\n<i>Je peux t\'aider à créé tes propres bots de stockage et t gagner de l\'argent grâce aux publicité affiché à travers ton bot\n- /clone [Créé ton bot] ✓</i>")

FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", 
    "<b>🌸 うぅ… sniff sniff… ♡\nOnii-chan / onee-chan… je suis trop désoléeaaa… (T_T)\n/nImpossible de te donner les fichiers… parce que tu n'es pas encore dans le(s) canal(aux) secret(s)… ૮₍ ˶•‌︿•‌˶ ₎ა💦 \n\nRejoins-les d'abord, s'il te plaaaait… puis réessaie ?\nYumeFlower t'attend avec plein de bisous et de fichiers tout doux… promis juré ! 🌷😢💕\n\n… Ne m'abandonne pas hein ? … ♡</b>")

CMD_TXT = """<blockquote><b>» Commandes administrateur :</b></blockquote>

<b>›› /dlt_time :</b> Définir le temps de suppression automatique
<b>›› /check_dlt_time :</b> Vérifier le temps de suppression actuel
<b>›› /dbroadcast :</b> Diffuser un document/vidéo
<b>›› /ban :</b> Bannir un utilisateur
<b>›› /unban :</b> Débannir un utilisateur
<b>›› /banlist :</b> Obtenir la liste des utilisateurs bannis
<b>›› /addchnl :</b> Ajouter un canal d'abonnement obligatoire
<b>›› /delchnl :</b> Supprimer un canal d'abonnement obligatoire
<b>›› /listchnl :</b> Voir les canaux ajoutés
<b>›› /fsub_mode :</b> Activer/désactiver le mode abonnement obligatoire
<b>›› /pbroadcast :</b> Envoyer une photo à tous les utilisateurs
<b>›› /add_admin :</b> Ajouter un administrateur
<b>›› /deladmin :</b> Supprimer un administrateur
<b>›› /custom_batch : </b> Batch personnalisée</b>
<b>›› /pbroadcast : pour envoyer un message à épinglé
<b>›› /dbroadcast : pour envoyer un message éphémere aux utilisateurs
<b>›› /admins :</b> Obtenir la liste des administrateurs
<b>›› /prime :</b> Donner une session premium à un utilisateur (ex: /prime 123456 3600)
<b>›› /removesession :</b> Supprimer la session d'un utilisateur

<b>›› /clone :</b> Cloner le bot (créer votre propre bot)
<b>›› /gestion :</b> Gérer votre bot cloné
<b>›› /list :</b> Liste des bots clonés (Owner uniquement)
<b>›› /bots :</b> Vue d'ensemble des bots (Owner uniquement)
<b>›› /stats :</b> Statistiques de votre bot
"""

# ==========================================
# OPTIONS DE PROTECTION & AFFICHAGE
# ==========================================

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False #Mettez True si vous voulez empêcher le transfert de fichiers depuis le bot
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'False'

BOT_STATS_TEXT = "<b>TEMPS DE FONCTIONNEMENT DU BOT</b>\n{uptime}"
USER_REPLY_TEXT = "Impossible d'utilisé ! Vous n'êtes pas un administrateur !!"

# ==========================================
# CONFIGURATION LOGGING
# ==========================================

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ==========================================
# CONFIGURATION SYSTÈME DE CLONAGE
# ==========================================

# Username du bot mère (pour le bouton "Créer votre propre bot")
MOTHER_BOT_USERNAME = os.environ.get("MOTHER_BOT_USERNAME", "YumeFlowerBot")

# Gain par impression (en dollars)
EARNING_PER_IMPRESSION = float(os.environ.get("EARNING_PER_IMPRESSION", "0.001"))

# Seuil minimum de retrait (en dollars)
MIN_WITHDRAWAL_AMOUNT = float(os.environ.get("MIN_WITHDRAWAL_AMOUNT", "7.00"))

# Durée par défaut des sessions gratuites (minutes)
DEFAULT_FREE_SESSION_MINUTES = int(os.environ.get("DEFAULT_FREE_SESSION_MINUTES", "10"))
