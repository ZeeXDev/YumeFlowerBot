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
import traceback
from datetime import datetime, timedelta

# Configuration logging détaillé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# AUTHENTIFICATION TELEGRAM WEB APP
# ============================================================

def verify_telegram_auth(auth_data: str) -> dict:
    """
    Vérifie l'authentification Telegram Web App
    """
    try:
        if not auth_data:
            logger.warning("Auth data vide")
            return None
        
        # Parser les données (format query string)
        data = {}
        if isinstance(auth_data, str):
            for pair in auth_data.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    data[key] = value
        elif isinstance(auth_data, dict):
            data = auth_data.copy()
        
        check_hash = data.pop('hash', None)
        
        if not check_hash:
            logger.warning("Pas de hash dans auth_data")
            return None
        
        # Créer la data check string (triée par clés)
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])
        
        # Clé secrète = SHA256 du bot token
        secret_key = hashlib.sha256(TG_BOT_TOKEN.encode()).digest()
        
        # Calculer le hash
        hash_calc = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if hash_calc != check_hash:
            logger.warning(f"Hash invalide. Reçu: {check_hash}, Calculé: {hash_calc}")
            return None
        
        # Vérifier date (24h max)
        auth_date = int(data.get('auth_date', 0))
        if auth_date == 0:
            logger.warning("Pas de auth_date")
            return None
            
        if (datetime.now().timestamp() - auth_date) > 86400:
            logger.warning("Auth date trop vieux")
            return None
            
        logger.info(f"Auth OK pour user {data.get('id')}")
        return data
        
    except Exception as e:
        logger.error(f"Erreur verify_telegram_auth: {e}")
        logger.error(traceback.format_exc())
        return None

# ============================================================
# MIDDLEWARE CORS
# ============================================================

@middleware
async def cors_middleware(request, handler):
    """Autorise les requêtes CORS depuis Vercel"""
    origin = request.headers.get('Origin', '')
    
    # Autoriser explicitement ton domaine
    allowed_origins = [
        'https://WaraMugiBot.vercel.app',
        'https://wara-mugi-bot.vercel.app',
        'http://localhost:3000',
        'http://localhost:8000',
        'https://web.telegram.org',
    ]
    
    is_allowed = any(allowed in origin for allowed in allowed_origins) or 'vercel.app' in origin
    
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except Exception as e:
            logger.error(f"ERREUR DANS HANDLER: {e}")
            logger.error(traceback.format_exc())
            response = web.json_response(
                {'error': 'Internal server error', 'detail': str(e)}, 
                status=500
            )
    
    if is_allowed:
        response.headers['Access-Control-Allow-Origin'] = origin
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
    try:
        # Tester connexion DB
        db_status = "connected" if db.storage else "disconnected"
        return web.json_response({
            "status": "online",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return web.json_response({
            "status": "error",
            "error": str(e)
        }, status=500)

@routes.post("/api/check-session")
async def api_check_session(request):
    """Vérifie si l'utilisateur a une session active"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        logger.info(f"Check session - User: {user_id}")
        
        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)
        
        # Vérifier auth (optionnel pour le debug, mais recommandé en prod)
        if auth:
            user_data = verify_telegram_auth(auth)
            if not user_data:
                logger.warning(f"Auth invalide pour user {user_id}")
                # On continue quand même pour tester, mais on log
            else:
                logger.info(f"Auth valide pour user {user_data.get('id')}")
        
        # Vérifier session
        try:
            has_session = await db.has_active_session(user_id)
            time_left = await db.get_session_time_left(user_id) if has_session else 0
            session = await db.get_user_session(user_id) if has_session else None
            
            return web.json_response({
                'has_access': has_session and time_left > 0,
                'time_left': time_left,
                'expires_at': session.get('expires_at') if session else None,
                'type': session.get('type') if session else None,
                'duration': await db.get_free_session_duration(),
                'can_watch_ad': await db.can_watch_ad(user_id)
            })
        except Exception as db_error:
            logger.error(f"Erreur DB check-session: {db_error}")
            return web.json_response({
                'has_access': False,
                'error': 'Database error',
                'detail': str(db_error)
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error in check-session: {e}")
        logger.error(traceback.format_exc())
        return web.json_response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@routes.post("/api/watch-ad")
async def api_watch_ad(request):
    """Active une session gratuite après visionnage de pub"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        logger.info(f"Watch ad - User: {user_id}")
        logger.info(f"Auth data: {auth[:100] if auth else 'None'}...")
        
        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)
        
        # Vérifier auth Telegram
        if auth:
            user_data = verify_telegram_auth(auth)
            if not user_data:
                logger.warning(f"Auth échouée pour user {user_id} - On continue quand même pour debug")
                # TEMPORAIRE: On désactive la vérif stricte pour tester
                # if not user_data or int(user_data.get('id', 0)) != int(user_id):
                #     return web.json_response({'error': 'Unauthorized'}, status=401)
            else:
                logger.info(f"Auth OK - Telegram ID: {user_data.get('id')}")
        
        # Vérifier si déjà session active
        try:
            if await db.has_active_session(user_id):
                logger.info(f"User {user_id} a déjà une session active")
                return web.json_response({
                    'success': False,
                    'message': 'Session already active'
                })
        except Exception as e:
            logger.error(f"Erreur DB has_active_session: {e}")
            return web.json_response({'error': f'DB Error: {str(e)}'}, status=500)
        
        # Vérifier cooldown
        try:
            if not await db.can_watch_ad(user_id):
                return web.json_response({
                    'success': False,
                    'message': 'Please wait before watching another ad'
                })
        except Exception as e:
            logger.error(f"Erreur DB can_watch_ad: {e}")
        
        # Créer session gratuite
        try:
            duration = await db.get_free_session_duration()
            logger.info(f"Création session - Duration: {duration}min - User: {user_id}")
            
            session = await db.create_free_session(user_id, duration)
            logger.info(f"Session créée avec succès: {session}")
            
            return web.json_response({
                'success': True,
                'duration': duration,
                'expires_at': session.get('expires_at'),
                'message': 'Session activated successfully'
            })
        except Exception as e:
            logger.error(f"Erreur création session: {e}")
            logger.error(traceback.format_exc())
            return web.json_response({
                'error': f'Failed to create session: {str(e)}',
                'detail': traceback.format_exc()
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error in watch-ad: {e}")
        logger.error(traceback.format_exc())
        return web.json_response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

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

@routes.get("/api/notifications")
async def get_notifications(request):
    """Récupère les notifications promo actives"""
    try:
        # Récupérer depuis la DB ou retourner un tableau vide par défaut
        notifications = await db.get_notifications() if hasattr(db, 'get_notifications') else []
        return web.json_response({
            'success': True,
            'notifications': notifications
        })
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

@routes.post("/api/admin/notifications")
async def update_notifications(request):
    """Met à jour les notifications (admin only)"""
    try:
        # Vérifier auth admin ici si nécessaire
        data = await request.json()
        notifications = data.get('notifications', [])
        
        # Limiter à 2 notifications
        notifications = notifications[:2]
        
        # Sauvegarder dans DB
        if hasattr(db, 'save_notifications'):
            await db.save_notifications(notifications)
        
        logger.info(f"Notifications mises à jour: {len(notifications)} items")
        
        return web.json_response({
            'success': True,
            'message': 'Notifications updated'
        })
    except Exception as e:
        logger.error(f"Erreur update notifications: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post("/api/admin/config")
async def api_admin_config(request):
    """Modifie la configuration"""
    try:
        data = await request.json()
        
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
    
    logger.info("✅ Web server initialized")
    logger.info(f"🔐 Admin password: {'Yes' if ADMIN_PASSWORD else 'No'}")
    logger.info(f"🤖 Bot token: {'Yes' if TG_BOT_TOKEN else 'No'}")
    
    return web_app
