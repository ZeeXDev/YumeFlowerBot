from aiohttp import web
from aiohttp.web_middlewares import middleware
from database.database import db
from config import TG_BOT_TOKEN, FREE_SESSION_DURATION, ADMIN_PASSWORD
import json
import hashlib
import hmac
import logging
import secrets
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
        data = json.loads(auth_data)
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
# ROUTES
# ============================================================

routes = web.RouteTableDef()

# -----------------------------------------------------------
# Routes Pages Web (Mini App)
# -----------------------------------------------------------

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    """Sert la page principale index.html"""
    return web.FileResponse('WebApp/index.html')

@routes.get("/prime", allow_head=True)
async def prime_page(request):
    """Sert la page premium"""
    return web.FileResponse('WebApp/prime.html')

@routes.get("/admin", allow_head=True)
async def admin_page(request):
    """Sert la page admin"""
    return web.FileResponse('WebApp/admin.html')

# -----------------------------------------------------------
# API Mini App - Sessions
# -----------------------------------------------------------

@routes.post("/api/check-session")
async def api_check_session(request):
    """Vérifie si l'utilisateur a une session active"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        if not user_id or not auth:
            return web.json_response({'error': 'Missing parameters'}, status=400)
        
        # Vérifier auth Telegram
        user_data = verify_telegram_auth(auth)
        if not user_data or int(user_data.get('id')) != int(user_id):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Vérifier session
        has_session = await db.has_active_session(user_id)
        time_left = await db.get_session_time_left(user_id) if has_session else 0
        session = await db.get_user_session(user_id)
        
        return web.json_response({
            'has_access': has_session,
            'time_left': time_left,
            'expires_at': session.get('expires_at') if session else None,
            'type': session.get('type') if session else None,
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
        
        if not user_id or not auth:
            return web.json_response({'error': 'Missing parameters'}, status=400)
        
        # Vérifier auth Telegram
        user_data = verify_telegram_auth(auth)
        if not user_data or int(user_data.get('id')) != int(user_id):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Vérifier si déjà session active
        if await db.has_active_session(user_id):
            return web.json_response({
                'success': False,
                'message': 'Session already active'
            })
        
        # Créer session gratuite (durée configurée en minutes)
        duration = await db.get_free_session_duration()
        session = await db.create_free_session(user_id, duration)
        
        logger.info(f"Free session created for user {user_id}, duration: {duration}min")
        
        return web.json_response({
            'success': True,
            'duration': duration,
            'expires_at': session['expires_at']
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
        payment_data = data.get('payment_method')
        plan = data.get('plan', 'monthly')
        
        if not user_id or not auth:
            return web.json_response({'error': 'Missing parameters'}, status=400)
        
        # Vérifier auth Telegram
        user_data = verify_telegram_auth(auth)
        if not user_data or int(user_data.get('id')) != int(user_id):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Déterminer la durée selon le plan
        duration_days = 7 if plan == 'weekly' else 30 if plan == 'monthly' else 365
        
        # Créer session premium (durée en jours * 24h * 60min)
        duration_minutes = duration_days * 24 * 60
        session = await db.create_premium_session(user_id, duration_minutes)
        
        logger.info(f"Premium session created for user {user_id}, plan: {plan}, duration: {duration_days} days")
        
        return web.json_response({
            'success': True,
            'duration': duration_days,
            'expires_at': session['expires_at']
        })
        
    except Exception as e:
        logger.error(f"Error in payment: {e}")
        return web.json_response({'error': str(e)}, status=500)

# -----------------------------------------------------------
# API Admin
# -----------------------------------------------------------

@routes.post("/api/admin/login")
async def api_admin_login(request):
    """Login admin - retourne un token si password correct"""
    try:
        data = await request.json()
        password = data.get('password')
        
        if not password:
            return web.json_response({
                'success': False,
                'error': 'Password required'
            }, status=400)
        
        # Vérifier le password
        if password == ADMIN_PASSWORD:
            # Créer un token simple (en production, utiliser JWT)
            token = secrets.token_urlsafe(32)
            
            logger.info("✅ Admin login successful")
            
            return web.json_response({
                'success': True,
                'token': token
            })
        else:
            logger.warning("❌ Admin login failed - invalid password")
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
async def api_admin_stats_get(request):
    """Retourne les statistiques admin (GET)"""
    try:
        # En production, vérifier le token d'authentification dans les headers
        
        all_users = await db.full_userbase()
        all_sessions = await db.storage.find_all(db.user_sessions_name)
        
        # Compter sessions actives
        active_sessions = 0
        for session in all_sessions:
            if session.get('is_active'):
                try:
                    expiry = datetime.fromisoformat(session['expires_at'])
                    if datetime.now() < expiry:
                        active_sessions += 1
                except:
                    pass
        
        # Compter publicités visionnées (approximation)
        ads_watched = len([s for s in all_sessions if s.get('type') == 'free'])
        
        # Compter utilisateurs premium
        premium_users = 0
        for session in all_sessions:
            if session.get('type') == 'premium' and session.get('is_active'):
                try:
                    expiry = datetime.fromisoformat(session['expires_at'])
                    if datetime.now() < expiry:
                        premium_users += 1
                except:
                    pass
        
        return web.json_response({
            'success': True,
            'total_users': len(all_users),
            'active_sessions': active_sessions,
            'ads_watched': ads_watched,
            'premium_users': premium_users
        })
        
    except Exception as e:
        logger.error(f"Error in admin stats: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

@routes.post("/api/admin/stats")
async def api_admin_stats_post(request):
    """Retourne les statistiques admin (POST - legacy)"""
    try:
        data = await request.json()
        password = data.get('password')
        
        if password != ADMIN_PASSWORD:
            return web.json_response({'error': 'Invalid password'}, status=403)
        
        all_users = await db.full_userbase()
        all_sessions = await db.storage.find_all(db.user_sessions_name)
        
        # Compter sessions actives
        active_sessions = 0
        for session in all_sessions:
            if session.get('is_active'):
                try:
                    expiry = datetime.fromisoformat(session['expires_at'])
                    if datetime.now() < expiry:
                        active_sessions += 1
                except:
                    pass
        
        return web.json_response({
            'success': True,
            'total_users': len(all_users),
            'active_sessions': active_sessions,
            'config': {
                'free_session_duration': await db.get_free_session_duration()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in admin stats: {e}")
        return web.json_response({'error': str(e)}, status=500)

@routes.post("/api/admin/config")
async def api_admin_config(request):
    """Modifie la configuration (durée sessions, etc.)"""
    try:
        data = await request.json()
        
        # En production, vérifier le token d'authentification
        
        # Mettre à jour durée gratuite si fournie
        if 'free_duration' in data:
            await db.set_free_session_duration(int(data['free_duration']))
            logger.info(f"Free session duration updated to {data['free_duration']} minutes")
        
        # Mettre à jour durée mensuelle
        if 'monthly_duration' in data:
            # Stocker dans la DB si nécessaire
            logger.info(f"Monthly duration: {data['monthly_duration']} days")
        
        # Mettre à jour durée annuelle
        if 'yearly_duration' in data:
            # Stocker dans la DB si nécessaire
            logger.info(f"Yearly duration: {data['yearly_duration']} days")
        
        current_duration = await db.get_free_session_duration()
        return web.json_response({
            'success': True,
            'free_session_duration': current_duration,
            'message': 'Configuration updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in admin config: {e}")
        return web.json_response({'error': str(e)}, status=500)

# -----------------------------------------------------------
# Anciennes Routes AdsGram (Conservées pour compatibilité)
# -----------------------------------------------------------

@routes.get("/adsgram/reward")
async def adsgram_reward_handler(request):
    """
    Endpoint appelé par AdsGram quand un utilisateur termine une pub
    URL: /adsgram/reward?userid=[userId]
    """
    try:
        user_id = request.query.get('userid')
        
        if not user_id:
            return web.json_response(
                {"status": "error", "message": "userid required"},
                status=400
            )
        
        try:
            user_id = int(user_id)
        except ValueError:
            return web.json_response(
                {"status": "error", "message": "invalid userid"},
                status=400
            )
        
        # Vérifier si l'utilisateur peut regarder une pub
        can_watch = await db.can_watch_ad(user_id)
        
        if not can_watch:
            logger.warning(f"AdsGram reward: user {user_id} already has recent session")
            return web.json_response({
                "status": "success",
                "message": "session already active",
                "user_id": user_id
            })
        
        # Activer la session gratuite (convertir heures en minutes)
        duration_minutes = FREE_SESSION_DURATION * 60 if FREE_SESSION_DURATION > 10 else FREE_SESSION_DURATION
        await db.create_free_session(user_id, duration_minutes)
        
        logger.info(f"✅ AdsGram: Session activated for user {user_id}")
        
        return web.json_response({
            "status": "success",
            "message": "reward granted",
            "user_id": user_id,
            "duration_minutes": duration_minutes
        })
        
    except Exception as e:
        logger.error(f"Error in adsgram reward: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )

@routes.get("/adsgram/test")
async def adsgram_test_handler(request):
    """Endpoint de test pour AdsGram"""
    try:
        user_id = request.query.get('userid')
        
        if not user_id:
            return web.json_response({
                "status": "info",
                "message": "Add ?userid=YOUR_ID to test"
            })
        
        try:
            user_id = int(user_id)
        except ValueError:
            return web.json_response({
                "status": "error",
                "message": "userid must be a number"
            }, status=400)
        
        has_session = await db.has_active_session(user_id)
        can_watch = await db.can_watch_ad(user_id)
        session = await db.get_user_session(user_id)
        
        return web.json_response({
            "status": "success",
            "user_id": user_id,
            "has_active_session": has_session,
            "can_watch_ad": can_watch,
            "session_data": session
        })
        
    except Exception as e:
        logger.error(f"Error in adsgram test: {e}")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

# ============================================================
# MIDDLEWARE CORS
# ============================================================

@middleware
async def cors_middleware(request, handler):
    """Autorise les requêtes CORS pour la Mini App Telegram"""
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Telegram-Init-Data'
    return response

# ============================================================
# CREATION APP
# ============================================================

async def web_server():
    """Crée et retourne l'application web aiohttp"""
    web_app = web.Application(middlewares=[cors_middleware])
    web_app.add_routes(routes)
    
    # Servir fichiers statiques (CSS, JS, images)
    web_app.router.add_static('/static/', path='WebApp', name='static')
    
    logger.info("✅ Web server initialized")
    logger.info(f"📁 Static files served from: WebApp/")
    logger.info(f"🔐 Admin password: {ADMIN_PASSWORD}")
    
    return web_app