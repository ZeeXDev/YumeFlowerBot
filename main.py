import asyncio
import os
from aiohttp import web
from plugins.web_server import web_server
from bot import Bot
import pyrogram.utils

# Configuration Pyrogram (évite les erreurs d'ID de canal)
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

async def main():
    # Démarrage du serveur web (Mini App + API)
    print("🌐 Démarrage du serveur web...")
    app = await web_server()
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Port Render (10000 par défaut, ou 8000/8080 en local)
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Serveur web actif sur le port {port}")
    print(f"🌍 URL: http://localhost:{port} (local) ou votre URL Render")

    # Démarrage du bot Telegram
    print("🤖 Démarrage du bot Telegram...")
    bot = Bot()
    await bot.start()
    
    print("✅ Bot démarré avec succès!")
    print("⏳ Le bot est en ligne et écoute les messages...")

    # Garder le programme en vie indéfiniment
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
