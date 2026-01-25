# =======================
# Imports standards
# =======================
import asyncio
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
from config import *

name = """
 BY CODEFLIX BOTS
"""

# =======================
# Classe principale du Bot
# =======================
class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER
        # URL pour la Mini App (utilisé dans start.py)
        self.web_app_domain = ADSGRAM_WEBAPP_URL or f"https://{self.username}.onrender.com" if hasattr(self, 'username') else ""

    # =======================
    # Démarrage du bot
    # =======================
    async def start(self):
        await super().start()

        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        
        # Mettre à jour le domaine web app avec le vrai username
        if not ADSGRAM_WEBAPP_URL:
            self.web_app_domain = f"https://{usr_bot_me.username}.onrender.com"

        # =======================
        # Vérification DB Channel
        # =======================
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(
                f"Bot must be admin in DB Channel. CHANNEL_ID={CHANNEL_ID}"
            )
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.username = usr_bot_me.username

        self.LOGGER(__name__).info("Bot Running..!")
        self.LOGGER(__name__).info("BOT DEPLOYED BY @BotZFlix")
        self.LOGGER(__name__).info("Bot Running..! Made by @ZeeXDev")

        # =======================
        # Message au propriétaire
        # =======================
        try:
            await self.send_message(
                OWNER_ID,
                "<b><blockquote> Bᴏᴛ Rᴇᴅéᴍᴀʀʀᴇʀ 🥰😘</blockquote></b>"
            )
        except:
            pass

    # =======================
    # Arrêt du bot
    # =======================
    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

    # =======================
    # Run loop
    # =======================
    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())

        self.LOGGER(__name__).info("Bot is now running. Thanks to @Kingcey")

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER(__name__).info("Shutting down...")
        finally:
            loop.run_until_complete(self.stop())
