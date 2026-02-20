from aiohttp import web
from aiohttp.web_middlewares import middleware
from database.database import db
from config import TG_BOT_TOKEN, FREE_SESSION_DURATION, ADMIN_PASSWORD, OWNER_ID
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
    """Autorise les requêtes CORS depuis n'importe quelle origine Telegram"""
    origin = request.headers.get('Origin', '')
    
    # Autoriser les origines Telegram et locales
    allowed_origins = [
        'https://web.telegram.org',
        'https://telegram.org',
        'http://localhost:3000',
        'http://localhost:8000',
        'http://localhost:8080',
        'https://localhost',
    ]
    
    # Autoriser aussi toutes les origines https (pour la production)
    is_allowed = (
        any(allowed in origin for allowed in allowed_origins) or 
        origin.startswith('https://') or
        'telegram' in origin.lower()
    )
    
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
    
    if is_allowed and origin:
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
        return web.json_response({
            "status": "online",
            "service": "YumeFlower2 Bot API",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return web.json_response({
            "status": "error",
            "error": str(e)
        }, status=500)

# ============================================================
# API POUR SYSTÈME DE CLONAGE - ID_PUBS
# ============================================================

@routes.post("/api/verify-id-pubs")
async def api_verify_id_pubs(request):
    """Vérifie un ID_PUBS et retourne les infos du bot"""
    try:
        data = await request.json()
        id_pubs = data.get('id_pubs', '').strip().upper()
        
        logger.info(f"Vérification ID_PUBS: {id_pubs}")
        
        if not id_pubs:
            return web.json_response({
                'success': False,
                'error': 'ID_PUBS manquant'
            }, status=400)
        
        # Chercher le bot par ID_PUBS
        id_data = await db.get_id_codes(id_pubs=id_pubs)
        
        if not id_data:
            return web.json_response({
                'success': False,
                'error': 'ID_PUBS invalide'
            })
        
        bot_data = await db.get_cloned_bot(id_data['bot_id'])
        
        if not bot_data:
            return web.json_response({
                'success': False,
                'error': 'Bot non trouvé'
            })
        
        return web.json_response({
            'success': True,
            'bot': {
                'id': bot_data['_id'],
                'username': bot_data['bot_username'],
                'name': bot_data.get('bot_username', 'Bot')
            },
            'id_pubs': id_pubs
        })
        
    except Exception as e:
        logger.error(f"Error in verify-id-pubs: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post("/api/watch-ad-clone")
async def api_watch_ad_clone(request):
    """
    Active une session gratuite après visionnage de pub pour un bot cloné
    Nécessite l'ID_PUBS pour identifier le bot
    """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        id_pubs = data.get('id_pubs', '').strip().upper()
        auth = data.get('auth')
        
        logger.info(f"Watch ad clone - User: {user_id}, ID_PUBS: {id_pubs}")
        
        if not user_id or not id_pubs:
            return web.json_response({
                'success': False,
                'error': 'Paramètres manquants'
            }, status=400)
        
        # Vérifier l'ID_PUBS
        id_data = await db.get_id_codes(id_pubs=id_pubs)
        
        if not id_data:
            return web.json_response({
                'success': False,
                'error': 'ID_PUBS invalide'
            })
        
        bot_id = id_data['bot_id']
        bot_data = await db.get_cloned_bot(bot_id)
        
        if not bot_data:
            return web.json_response({
                'success': False,
                'error': 'Bot non trouvé'
            })
        
        # Vérifier auth Telegram (optionnel mais recommandé)
        if auth:
            user_data = verify_telegram_auth(auth)
            if user_data and int(user_data.get('id', 0)) != int(user_id):
                logger.warning(f"Mismatch user_id: {user_id} vs {user_data.get('id')}")
        
        # Vérifier si déjà session active pour CE bot
        if await db.has_active_session(user_id, bot_id):
            return web.json_response({
                'success': False,
                'message': 'Session déjà active pour ce bot'
            })
        
        # Créer session gratuite pour CE bot spécifique
        duration = await db.get_free_session_duration()
        session = await db.create_free_session(user_id, duration, bot_id)
        
        # Incrémenter les stats
        await db.increment_bot_stat(bot_id, 'total_ads_watched')
        
        # AJOUTER DES GAINS AU BOT ($0.002 par impression = $2 CPM)
        earning_per_ad = 0.002
        await db.add_earning(bot_id, earning_per_ad, 'ad_impression')
        
        logger.info(f"Session créée pour user {user_id} sur bot {bot_id}")
        logger.info(f"Gains ajoutés au bot {bot_id}: ${earning_per_ad}")
        
        return web.json_response({
            'success': True,
            'duration': duration,
            'expires_at': session.get('expires_at'),
            'bot_username': bot_data['bot_username'],
            'message': 'Session activée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error in watch-ad-clone: {e}")
        logger.error(traceback.format_exc())
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post("/api/check-session-clone")
async def api_check_session_clone(request):
    """Vérifie si l'utilisateur a une session active pour un bot spécifique"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        id_pubs = data.get('id_pubs', '').strip().upper()
        
        if not user_id or not id_pubs:
            return web.json_response({
                'success': False,
                'error': 'Paramètres manquants'
            }, status=400)
        
        # Trouver le bot par ID_PUBS
        id_data = await db.get_id_codes(id_pubs=id_pubs)
        
        if not id_data:
            return web.json_response({
                'success': False,
                'error': 'ID_PUBS invalide'
            })
        
        bot_id = id_data['bot_id']
        
        # Vérifier session pour CE bot
        has_session = await db.has_active_session(user_id, bot_id)
        time_left = await db.get_session_time_left(user_id, bot_id) if has_session else 0
        session = await db.get_user_session(user_id, bot_id) if has_session else None
        
        return web.json_response({
            'success': True,
            'has_access': has_session and time_left > 0,
            'time_left': time_left,
            'expires_at': session.get('expires_at') if session else None,
            'type': session.get('type') if session else None,
            'bot_id': bot_id
        })
        
    except Exception as e:
        logger.error(f"Error in check-session-clone: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

# ============================================================
# API PAGE MAÎTRE (ID_CODE)
# ============================================================

@routes.post("/api/master/login")
async def api_master_login(request):
    """Connexion à la page Maître avec ID_CODE"""
    try:
        data = await request.json()
        id_code = data.get('id_code', '').strip().upper()
        auth = data.get('auth')
        
        logger.info(f"Tentative connexion maître avec ID_CODE")
        
        if not id_code:
            return web.json_response({
                'success': False,
                'error': 'ID_CODE manquant'
            }, status=400)
        
        # Vérifier l'ID_CODE
        id_data = await db.get_id_codes(id_code=id_code)
        
        if not id_data:
            return web.json_response({
                'success': False,
                'error': 'ID_CODE invalide'
            })
        
        # Vérifier auth Telegram si fourni
        if auth:
            user_data = verify_telegram_auth(auth)
            if user_data:
                # Vérifier que l'utilisateur est bien le maître
                master_id = id_data['master_id']
                if int(user_data.get('id', 0)) != master_id:
                    logger.warning(f"Tentative accès maître non autorisée: {user_data.get('id')} vs {master_id}")
                    return web.json_response({
                        'success': False,
                        'error': 'Non autorisé'
                    }, status=403)
        
        bot_data = await db.get_cloned_bot(id_data['bot_id'])
        earnings = await db.get_bot_earnings(id_data['bot_id'])
        stats = bot_data.get('stats', {}) if bot_data else {}
        
        return web.json_response({
            'success': True,
            'bot': {
                'id': bot_data['_id'],
                'username': bot_data['bot_username'],
                'created_at': bot_data['created_at']
            },
            'id_pubs': id_data['id_pubs'],
            'stats': {
                'total_users': stats.get('total_users', 0),
                'total_ads_watched': stats.get('total_ads_watched', 0),
                'total_files_sent': stats.get('total_files_sent', 0)
            },
            'earnings': {
                'balance': earnings['balance'] if earnings else 0,
                'total_earned': earnings['total_earned'] if earnings else 0,
                'total_withdrawn': earnings['total_withdrawn'] if earnings else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in master login: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post("/api/master/withdraw")
async def api_master_withdraw(request):
    """Demande de retrait pour un maître (manuel - envoie notification à l'OWNER)"""
    try:
        data = await request.json()
        id_code = data.get('id_code', '').strip().upper()
        amount = float(data.get('amount', 0))
        method = data.get('method', 'crypto')  # crypto, moov, orange, ecobank
        account_info = data.get('account_info', '')  # numéro de téléphone/compte
        
        if not id_code or amount <= 0:
            return web.json_response({
                'success': False,
                'error': 'Paramètres invalides'
            }, status=400)
        
        # Vérifier ID_CODE
        id_data = await db.get_id_codes(id_code=id_code)
        if not id_data:
            return web.json_response({
                'success': False,
                'error': 'ID_CODE invalide'
            })
        
        bot_id = id_data['bot_id']
        bot_data = await db.get_cloned_bot(bot_id)
        
        # Vérifier solde suffisant (minimum $7)
        earnings = await db.get_bot_earnings(bot_id)
        if not earnings or earnings['balance'] < 7.0:
            return web.json_response({
                'success': False,
                'error': 'Solde insuffisant (minimum $7)'
            })
        
        if earnings['balance'] < amount:
            return web.json_response({
                'success': False,
                'error': 'Montant supérieur au solde'
            })
        
        # Créer la demande de retrait (statut: pending)
        result = await db.request_withdrawal(bot_id, amount, method)
        
        if result['success']:
            # Envoyer notification à l'OWNER (manuel)
            try:
                from bot import Bot
                bot = Bot()
                
                method_names = {
                    'crypto': 'Crypto (BTC/USDT)',
                    'moov': 'Moov Money',
                    'orange': 'Orange Money',
                    'ecobank': 'Ecobank Xpress'
                }
                
                await bot.send_message(
                    OWNER_ID,
                    f"💸 <b>Nouvelle demande de retrait!</b>\n\n"
                    f"🤖 Bot: @{bot_data['bot_username']}\n"
                    f"👤 Maître ID: <code>{id_data['master_id']}</code>\n"
                    f"💵 Montant: ${amount:.2f}\n"
                    f"💳 Méthode: {method_names.get(method, method)}\n"
                    f"📱 Compte: <code>{account_info}</code>\n\n"
                    f"🆔 ID_PUBS: <code>{id_data['id_pubs']}</code>\n\n"
                    f"Utilisez /withdrawals pour voir toutes les demandes.",
                    parse_mode='HTML'
                )
            except Exception as notify_error:
                logger.error(f"Erreur notification owner: {notify_error}")
            
            logger.info(f"Retrait demandé pour bot {bot_id}: ${amount} via {method}")
        
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"Error in master withdraw: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post("/api/master/regenerate-code")
async def api_master_regenerate_code(request):
    """Régénère l'ID_CODE et ID_PUBS"""
    try:
        data = await request.json()
        id_code = data.get('id_code', '').strip().upper()
        auth = data.get('auth')
        
        if not id_code:
            return web.json_response({
                'success': False,
                'error': 'ID_CODE manquant'
            }, status=400)
        
        # Vérifier ID_CODE et auth
        id_data = await db.get_id_codes(id_code=id_code)
        if not id_data:
            return web.json_response({
                'success': False,
                'error': 'ID_CODE invalide'
            })
        
        # Vérifier auth
        if auth:
            user_data = verify_telegram_auth(auth)
            if user_data:
                if int(user_data.get('id', 0)) != id_data['master_id']:
                    return web.json_response({
                        'success': False,
                        'error': 'Non autorisé'
                    }, status=403)
        
        # Régénérer
        new_codes = await db.regenerate_id_code(id_data['bot_id'], id_data['master_id'])
        
        if new_codes:
            logger.info(f"ID_CODE régénéré pour bot {id_data['bot_id']}")
            return web.json_response({
                'success': True,
                'id_pubs': new_codes['id_pubs'],
                'id_code': new_codes['id_code']
            })
        else:
            return web.json_response({
                'success': False,
                'error': 'Erreur lors de la régénération'
            })
            
    except Exception as e:
        logger.error(f"Error in regenerate code: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

# ============================================================
# API EXISTANTES (BOT MÈRE)
# ============================================================

@routes.post("/api/check-session")
async def api_check_session(request):
    """Vérifie si l'utilisateur a une session active (bot mère)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        logger.info(f"Check session - User: {user_id}")
        
        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)
        
        # Vérifier session pour bot mère (pas de bot_id)
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
    """Active une session gratuite après visionnage de pub (bot mère)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        auth = data.get('auth')
        
        logger.info(f"Watch ad - User: {user_id}")
        
        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)
        
        # Vérifier auth Telegram
        if auth:
            user_data = verify_telegram_auth(auth)
            if not user_data:
                logger.warning(f"Auth échouée pour user {user_id}")
        
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
        
        # Créer session gratuite (bot mère, pas de bot_id)
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

# ============================================================
# API ADMIN (OWNER)
# ============================================================

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
        all_bots = await db.get_all_cloned_bots()
        
        # Calculer sessions actives
        active_sessions = 0
        premium_users = 0
        free_users = 0
        
        # Stats des bots clonés
        total_cloned_balance = 0
        total_ads_watched = 0
        
        for bot in all_bots:
            earnings = await db.get_bot_earnings(bot['_id'])
            if earnings:
                total_cloned_balance += earnings['balance']
                total_ads_watched += bot.get('stats', {}).get('total_ads_watched', 0)
        
        return web.json_response({
            'success': True,
            'total_users': len(all_users),
            'cloned_bots': len(all_bots),
            'cloned_bots_balance': total_cloned_balance,
            'total_ads_watched': total_ads_watched,
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


@routes.post("/api/admin/credit-bot")
async def api_admin_credit_bot(request):
    """Crédite le solde d'un bot (owner only)"""
    try:
        data = await request.json()
        bot_id = data.get('bot_id')
        amount = float(data.get('amount', 0))
        
        if not bot_id:
            return web.json_response({
                'success': False,
                'error': 'bot_id manquant'
            }, status=400)
        
        success = await db.admin_credit_balance(bot_id, amount)
        
        if success:
            logger.info(f"Bot {bot_id} crédité de ${amount}")
            return web.json_response({
                'success': True,
                'message': f'Bot crédité de ${amount}'
            })
        else:
            return web.json_response({
                'success': False,
                'error': 'Erreur lors du crédit'
            })
            
    except Exception as e:
        logger.error(f"Error in admin credit bot: {e}")
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


@routes.get("/api/admin/withdrawals")
async def api_admin_withdrawals(request):
    """Liste toutes les demandes de retrait en attente (OWNER)"""
    try:
        pending = await db.get_pending_withdrawals()
        
        return web.json_response({
            'success': True,
            'withdrawals': pending
        })
        
    except Exception as e:
        logger.error(f"Error in admin withdrawals: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post("/api/admin/approve-withdrawal")
async def api_admin_approve_withdrawal(request):
    """Approuve un retrait (OWNER)"""
    try:
        data = await request.json()
        bot_id = data.get('bot_id')
        tx_timestamp = data.get('timestamp')
        
        if not bot_id or not tx_timestamp:
            return web.json_response({
                'success': False,
                'error': 'Paramètres manquants'
            }, status=400)
        
        success = await db.approve_withdrawal(bot_id, tx_timestamp)
        
        if success:
            # Notifier le maître
            try:
                from bot import Bot
                bot = Bot()
                bot_data = await db.get_cloned_bot(bot_id)
                id_data = await db.get_id_codes(bot_id=bot_id)
                
                if bot_data and id_data:
                    await bot.send_message(
                        id_data['master_id'],
                        f"✅ <b>Retrait approuvé!</b>\n\n"
                        f"Votre demande de retrait a été traitée.\n"
                        f"Le montant sera envoyé sous peu.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Erreur notification maître: {e}")
        
        return web.json_response({
            'success': success
        })
        
    except Exception as e:
        logger.error(f"Error in approve withdrawal: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

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
    logger.info(f"👑 Owner ID: {OWNER_ID}")
    
    return web_app
