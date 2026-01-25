from aiohttp import web
from aiohttp.web_middlewares import middleware
from database.database import db
from config import TG_BOT_TOKEN, FREE_SESSION_DURATION, ADMIN_PASSWORD
import json
import hashlib
import hmac
import logging
import secrets
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================
# AUTHENTIFICATION TELEGRAM WEB APP
# ============================================================

def verify_telegram_auth(auth_data: str) -> dict:
    """
    Vérifie l'authentification Telegram Web App
    Valide le hash HMAC pour sécuriser les données
    """
    try:
        # Si auth_data est déjà un dict (cas rare), le convertir
        if isinstance(auth_data, dict):
            data = auth_data.copy()
        else:
            # Parser les données d'auth Telegram
            data = {}
            for pair in auth_data.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    data[key] = value
        
        check_hash = data.pop('hash', None)
        
        if not check_hash:
            return None
        
        # Créer la data check string (triée par clés)
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
        
        # Clé secrète = SHA256 du bot token
        secret_key = hashlib.sha256(TG_BOT_TOKEN.encode()).digest()
        
        # Calculer le hash
        hash_calc = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if hash_calc != check_hash:
            logger.warning("Invalid hash in Telegram auth")
            return None
        
        # Vérifier date (24h max)
        auth_date = datetime.fromtimestamp(int(data.get('auth_date', 0)))
        if (datetime.now() - auth_date).days > 1:
            logger.warning("Auth date too old")
            return None
            
        return data
    except Exception as e:
        logger.error(f"Error verifying Telegram auth: {e}")
        return None

# ============================================================
# MIDDLEWARE CORS (Autorise Vercel)
# ============================================================

@middleware
async def cors_middleware(request, handler):
    """Autorise les requêtes CORS depuis Vercel"""
    # Gérer les requêtes OPTIONS (preflight)
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    # Autoriser ton domaine Vercel spécifique
    origin = request.headers.get('Origin', '')
    allowed_origins = [
        'https://WaraMugiBot.vercel.app',
        'https://*.vercel.app',
        'http://localhost:3000',
        'http://localhost:8000',
        'https://web.telegram.org',
    ]
    
    # Vérifier si l'origine est autorisée
    if origin:
        for allowed in allowed_origins:
            if allowed == '*' or origin == allowed or (allowed.startswith('https://*.') and origin.endswith(allowed.replace('https://*.', '.'))):
                response.headers['Access-Control-Allow-Origin'] = origin
                break
        else:
            # Si pas dans la liste, quand même autoriser (pour le développement)
            response.headers['Access-Control-Allow-Origin'] = '*'
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Telegram-Init-Data'
    response.headers['Access-Control-Max-Age'] = '86400'
    
    return response

# ============================================================
# ROUTES API
# ============================================================

routes = web.RouteTableDef()

@routes.get("/")
async def health_check(request):
    """Vérification que le serveur est en ligne"""
    return web.json_response({
        "status": "online",
        "service": "WaraMugi Bot API",
        "timestamp": datetime.now().isoformat()
    })

@routes.post("/api/check-session")
async def api_check_session(request):
    """Vérifie si l'utilisateur a une session active"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)
        
        # Vérifier auth Telegram (optionnel mais recommandé)
        if auth:
            user_data = verify_telegram_auth(auth)
            if not user_data or int(user_data.get('id', 0)) != int(user_id):
                return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Vérifier session
        has_session = await db.has_active_session(user_id)
        time_left = await db.get_session_time_left(user_id) if has_session else 0
        session = await db.get_user_session(user_id)
        
        return web.json_response({
            'has_access': has_session and time_left > 0,
            'time_left': time_left,
            'expires_at': session.get('expires_at') if session else None,
            'type': session.get('type') if session else None,
            'duration': await db.get_free_session_duration(),
            'can_watch_ad': await db.can_watch_ad(user_id)
        })
        
    except Exception as e:
        logger.error(f"Error in check-session: {e}")
        return web.json_response({'error': str(e)}, status=500)

@routes.post("/api/watch-ad")
async def api_watch_ad(request):
    """Active une session gratuite après visionnage de pub"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)
        
        # Vérifier auth Telegram
        if auth:
            user_data = verify_telegram_auth(auth)
            if not user_data or int(user_data.get('id', 0)) != int(user_id):
                return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Vérifier si déjà session active
        if await db.has_active_session(user_id):
            return web.json_response({
                'success': False,
                'message': 'Session already active'
            })
        
        # Vérifier cooldown entre pubs
        if not await db.can_watch_ad(user_id):
            return web.json_response({
                'success': False,
                'message': 'Please wait before watching another ad'
            })
        
        # Créer session gratuite
        duration = await db.get_free_session_duration()
        session = await db.create_free_session(user_id, duration)
        
        logger.info(f"Free session created for user {user_id}, duration: {duration}min")
        
        return web.json_response({
            'success': True,
            'duration': duration,
            'expires_at': session['expires_at'],
            'message': 'Session activated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in watch-ad: {e}")
        return web.json_response({'error': str(e)}, status=500)

@routes.post("/api/payment")
async def api_payment(request):
    """Créer une session premium après paiement"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        plan = data.get('plan', 'monthly')
        
        if not user_id or not auth:
            return web.json_response({'error': 'Missing parameters'}, status=400)
        
        # Vérifier auth Telegram
        user_data = verify_telegram_auth(auth)
        if not user_data or int(user_data.get('id', 0)) != int(user_id):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Déterminer la durée selon le plan
        duration_days = 7 if plan == 'weekly' else 30 if plan == 'monthly' else 365
        
        # Créer session premium (durée en minutes)
        duration_minutes = duration_days * 24 * 60
        session = await db.create_premium_session(user_id, duration_minutes)
        
        logger.info(f"Premium session created for user {user_id}, plan: {plan}")
        
        return web.json_response({
            'success': True,
            'duration': duration_days,
            'expires_at': session['expires_at'],
            'plan': plan
        })
        
    except Exception as e:
        logger.error(f"Error in payment: {e}")
        return web.json_response({'error': str(e)}, status=500)

# -----------------------------------------------------------
# API Admin
# -----------------------------------------------------------

@routes.post("/api/admin/login")
async def api_admin_login(request):
    """Login admin"""
    try:
        data = await request.json()
        password = data.get('password')
        
        if not password:
            return web.json_response({
                'success': False,
                'error': 'Password required'
            }, status=400)
        
        if password == ADMIN_PASSWORD:
            token = secrets.token_urlsafe(32)
            logger.info("✅ Admin login successful")
            
            return web.json_response({
                'success': True,
                'token': token
            })
        else:
            logger.warning("❌ Admin login failed")
            return web.json_response({
                'success': False,
                'error': 'Invalid password'
            }, status=401)
        
    except Exception as e:
        logger.error(f"Error in admin login: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

@routes.get("/api/admin/stats")
async def api_admin_stats(request):
    """Statistiques admin"""
    try:
        all_users = await db.full_userbase()
        all_sessions = await db.storage.find_all(db.user_sessions_name)
        
        # Compter sessions actives
        active_sessions = 0
        premium_users = 0
        free_users = 0
        
        for session in all_sessions:
            if session.get('is_active'):
                try:
                    expiry = datetime.fromisoformat(session['expires_at'])
                    if datetime.now() < expiry:
                        active_sessions += 1
                        if session.get('type') == 'premium':
                            premium_users += 1
                        else:
                            free_users += 1
                except:
                    pass
        
        return web.json_response({
            'success': True,
            'total_users': len(all_users),
            'active_sessions': active_sessions,
            'premium_users': premium_users,
            'free_users': free_users,
            'config': {
                'free_session_duration': await db.get_free_session_duration()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in admin stats: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

@routes.post("/api/admin/config")
async def api_admin_config(request):
    """Modifie la configuration"""
    try:
        data = await request.json()
        
        # Mettre à jour durée gratuite si fournie
        if 'free_duration' in data:
            await db.set_free_session_duration(int(data['free_duration']))
            logger.info(f"Free duration updated to {data['free_duration']} minutes")
        
        return web.json_response({
            'success': True,
            'free_session_duration': await db.get_free_session_duration()
        })
        
    except Exception as e:
        logger.error(f"Error in admin config: {e}")
        return web.json_response({'error': str(e)}, status=500)

# ============================================================
# CREATION APP
# ============================================================

async def web_server():
    """Crée et retourne l'application web aiohttp"""
    web_app = web.Application(middlewares=[cors_middleware])
    web_app.add_routes(routes)
    
    # Servir fichiers statiques uniquement si on est pas sur Vercel
    # (décommente si tu veux tester en local avec Render)
    # if os.path.exists('WebApp'):
    #     web_app.router.add_static('/', path='WebApp', name='static')
    
    logger.info("✅ Web server initialized")
    logger.info(f"🔐 Admin password configured: {'Yes' if ADMIN_PASSWORD else 'No'}")
    
    return web_app
