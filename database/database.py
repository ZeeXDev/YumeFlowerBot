# Creating the complete database.py file with cloning system

#Codeflix_Botz
#rohit_1888 on Tg

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging
import secrets
import string

from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

logging.basicConfig(level=logging.INFO)


class Rohit:
    def __init__(self):
        # Connexion MongoDB
        self.client = AsyncIOMotorClient(DB_URI)
        self.db = self.client[DB_NAME]
        
        # Collections existantes
        self.channel_data_name = 'channels'
        self.admins_data_name = 'admins'
        self.user_data_name = 'users'
        self.banned_user_name = 'banned_user'
        self.autho_user_name = 'autho_user'
        self.del_timer_name = 'del_timer'
        self.fsub_name = 'fsub'
        self.rqst_fsub_name = 'request_forcesub'
        self.rqst_fsub_channel_name = 'request_forcesub_channel'
        self.user_sessions_name = 'user_sessions'
        self.config_name = 'config'
        
        # NOUVELLES COLLECTIONS POUR LE SYSTÈME DE CLONAGE
        self.cloned_bots_name = 'cloned_bots'
        self.bot_admins_name = 'bot_admins'  # MAITRE et ADMIN par bot
        self.bot_stats_name = 'bot_stats'
        self.bot_earnings_name = 'bot_earnings'
        self.id_codes_name = 'id_codes'  # ID_PUBS et ID_CODE
        
        # Références aux collections MongoDB
        self.users_col = self.db[self.user_data_name]
        self.admins_col = self.db[self.admins_data_name]
        self.banned_col = self.db[self.banned_user_name]
        self.del_timer_col = self.db[self.del_timer_name]
        self.fsub_col = self.db[self.fsub_name]
        self.rqst_fsub_col = self.db[self.rqst_fsub_channel_name]
        self.sessions_col = self.db[self.user_sessions_name]
        self.config_col = self.db[self.config_name]
        
        # Nouvelles collections
        self.cloned_bots_col = self.db[self.cloned_bots_name]
        self.bot_admins_col = self.db[self.bot_admins_name]
        self.bot_stats_col = self.db[self.bot_stats_name]
        self.bot_earnings_col = self.db[self.bot_earnings_name]
        self.id_codes_col = self.db[self.id_codes_name]

    # ==========================================
    # USER DATA (EXISTANT)
    # ==========================================
    
    async def present_user(self, user_id: int) -> bool:
        found = await self.users_col.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int) -> None:
        if not await self.present_user(user_id):
            await self.users_col.insert_one({'_id': user_id})

    async def full_userbase(self) -> List[int]:
        users = await self.users_col.find({}, {'_id': 1}).to_list(length=None)
        return [user['_id'] for user in users]

    async def del_user(self, user_id: int) -> None:
        await self.users_col.delete_one({'_id': user_id})

    # ==========================================
    # ADMIN DATA (EXISTANT)
    # ==========================================
    
    async def admin_exist(self, admin_id: int) -> bool:
        found = await self.admins_col.find_one({'_id': admin_id})
        return bool(found)

    async def add_admin(self, admin_id: int) -> None:
        if not await self.admin_exist(admin_id):
            await self.admins_col.insert_one({'_id': admin_id})

    async def del_admin(self, admin_id: int) -> None:
        if await self.admin_exist(admin_id):
            await self.admins_col.delete_one({'_id': admin_id})

    async def get_all_admins(self) -> List[int]:
        admins = await self.admins_col.find({}, {'_id': 1}).to_list(length=None)
        return [admin['_id'] for admin in admins]

    # ==========================================
    # BAN USER DATA (EXISTANT)
    # ==========================================
    
    async def ban_user_exist(self, user_id: int) -> bool:
        found = await self.banned_col.find_one({'_id': user_id})
        return bool(found)

    async def add_ban_user(self, user_id: int) -> None:
        if not await self.ban_user_exist(user_id):
            await self.banned_col.insert_one({'_id': user_id})

    async def del_ban_user(self, user_id: int) -> None:
        if await self.ban_user_exist(user_id):
            await self.banned_col.delete_one({'_id': user_id})

    async def get_ban_users(self) -> List[int]:
        banned = await self.banned_col.find({}, {'_id': 1}).to_list(length=None)
        return [user['_id'] for user in banned]

    # ==========================================
    # AUTO DELETE TIMER SETTINGS (EXISTANT)
    # ==========================================
    
    async def set_del_timer(self, value: int) -> None:
        await self.del_timer_col.update_one(
            {'_id': 'timer'},
            {'$set': {'value': value}},
            upsert=True
        )

    async def get_del_timer(self) -> int:
        data = await self.del_timer_col.find_one({'_id': 'timer'})
        return data.get('value', 0) if data else 0

    # ==========================================
    # CHANNEL MANAGEMENT (EXISTANT)
    # ==========================================
    
    async def channel_exist(self, channel_id: int) -> bool:
        found = await self.fsub_col.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int, mode: str = "off") -> None:
        if not await self.channel_exist(channel_id):
            await self.fsub_col.insert_one({'_id': channel_id, 'mode': mode})

    async def rem_channel(self, channel_id: int) -> None:
        if await self.channel_exist(channel_id):
            await self.fsub_col.delete_one({'_id': channel_id})

    async def show_channels(self) -> List[int]:
        channels = await self.fsub_col.find({}, {'_id': 1}).to_list(length=None)
        return [ch['_id'] for ch in channels]

    async def get_channel_mode(self, channel_id: int) -> str:
        data = await self.fsub_col.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    async def set_channel_mode(self, channel_id: int, mode: str) -> None:
        await self.fsub_col.update_one(
            {'_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )

    # ==========================================
    # REQUEST FORCE-SUB MANAGEMENT (EXISTANT)
    # ==========================================
    
    async def req_user(self, channel_id: int, user_id: int) -> None:
        try:
            await self.rqst_fsub_col.update_one(
                {'_id': int(channel_id)},
                {'$addToSet': {'user_ids': int(user_id)}},
                upsert=True
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to add user to request list: {e}")

    async def del_req_user(self, channel_id: int, user_id: int) -> None:
        await self.rqst_fsub_col.update_one(
            {'_id': channel_id},
            {'$pull': {'user_ids': user_id}}
        )

    async def req_user_exist(self, channel_id: int, user_id: int) -> bool:
        try:
            found = await self.rqst_fsub_col.find_one({'_id': int(channel_id)})
            if found:
                user_ids = found.get('user_ids', [])
                return int(user_id) in user_ids
            return False
        except Exception as e:
            print(f"[DB ERROR] Failed to check request list: {e}")
            return False

    async def reqChannel_exist(self, channel_id: int) -> bool:
        channel_ids = await self.show_channels()
        return channel_id in channel_ids

    # ==========================================
    # SESSIONS MANAGEMENT (EXISTANT - MODIFIÉ)
    # ==========================================
    
    async def get_user_session(self, user_id: int, bot_id: int = None) -> Optional[Dict]:
        """Récupère les informations de session d'un utilisateur pour un bot spécifique"""
        query = {'_id': user_id}
        if bot_id:
            query['bot_id'] = bot_id
        return await self.sessions_col.find_one(query)

    async def create_free_session(self, user_id: int, duration_minutes: int = 10, bot_id: int = None) -> Dict:
        """Crée une session gratuite après pub"""
        now = datetime.now(timezone.utc)
        expiry_time = now + timedelta(minutes=duration_minutes)
        session_data = {
            '_id': f"{user_id}_{bot_id}" if bot_id else user_id,
            'user_id': user_id,
            'bot_id': bot_id,
            'type': 'free',
            'is_active': True,
            'created_at': now.isoformat(),
            'expires_at': expiry_time.isoformat(),
            'last_ad_watch': now.isoformat()
        }
        await self.sessions_col.update_one(
            {'_id': session_data['_id']},
            {'$set': session_data},
            upsert=True
        )
        print(f"[DB] Session créée pour user {user_id} sur bot {bot_id}, expire à {expiry_time}")
        return session_data

    async def create_premium_session(self, user_id: int, duration_seconds: int, admin_id: int = None, bot_id: int = None) -> Dict:
        """Crée une session premium (via paiement ou admin)"""
        now = datetime.now(timezone.utc)
        expiry_time = now + timedelta(seconds=duration_seconds)
        session_id = f"{user_id}_{bot_id}" if bot_id else user_id
        session_data = {
            '_id': session_id,
            'user_id': user_id,
            'bot_id': bot_id,
            'type': 'premium',
            'is_active': True,
            'created_at': now.isoformat(),
            'expires_at': expiry_time.isoformat(),
            'granted_by': admin_id,
            'payment_method': 'manual' if admin_id else 'crypto'
        }
        await self.sessions_col.update_one(
            {'_id': session_id},
            {'$set': session_data},
            upsert=True
        )
        return session_data

    async def set_free_session(self, user_id: int, duration_hours: int = 20) -> None:
        """Méthode compatible avec l'ancien système AdsGram"""
        await self.create_free_session(user_id, duration_hours * 60)

    async def has_active_session(self, user_id: int, bot_id: int = None) -> bool:
        """Vérifie si l'utilisateur a une session active"""
        session = await self.get_user_session(user_id, bot_id)
        if not session or not session.get('is_active'):
            return False
        
        try:
            expiry_str = session['expires_at']
            if expiry_str.endswith('Z'):
                expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            else:
                expiry = datetime.fromisoformat(expiry_str)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            
            if now > expiry:
                await self.deactivate_session(user_id, bot_id)
                return False
            
            return True
        except Exception as e:
            print(f"[ERROR] Erreur vérification session: {e}")
            return False

    async def deactivate_session(self, user_id: int, bot_id: int = None) -> None:
        """Désactive une session"""
        session_id = f"{user_id}_{bot_id}" if bot_id else user_id
        await self.sessions_col.update_one(
            {'_id': session_id},
            {'$set': {'is_active': False}}
        )

    async def remove_session(self, user_id: int, bot_id: int = None) -> None:
        """Supprime complètement une session"""
        session_id = f"{user_id}_{bot_id}" if bot_id else user_id
        await self.sessions_col.delete_one({'_id': session_id})

    async def get_session_time_left(self, user_id: int, bot_id: int = None) -> int:
        """Retourne le nombre de secondes restantes"""
        session = await self.get_user_session(user_id, bot_id)
        if not session or not session.get('is_active'):
            return 0
        
        try:
            expiry_str = session['expires_at']
            if expiry_str.endswith('Z'):
                expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            else:
                expiry = datetime.fromisoformat(expiry_str)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            remaining = (expiry - now).total_seconds()
            return max(0, int(remaining))
        except Exception as e:
            print(f"[ERROR] Erreur calcul temps restant: {e}")
            return 0

    async def can_watch_ad(self, user_id: int) -> bool:
        """VÉRIFICATION DÉSACTIVÉE - SPAM AUTORISÉ"""
        return True

    async def force_reset_ad_timer(self, user_id: int) -> None:
        """Reset le timer de pub"""
        await self.sessions_col.update_one(
            {'_id': user_id},
            {'$unset': {'last_ad_watch': ''}}
        )

    # ==========================================
    # ADMIN CONFIGURATION (EXISTANT)
    # ==========================================
    
    async def set_free_session_duration(self, minutes: int) -> None:
        await self.config_col.update_one(
            {'_id': 'settings'},
            {'$set': {'free_session_duration': minutes}},
            upsert=True
        )

    async def get_free_session_duration(self) -> int:
        config = await self.config_col.find_one({'_id': 'settings'})
        return config.get('free_session_duration', 10) if config else 10

    # ==========================================
    # SYSTÈME DE CLONAGE - BOTS CLONÉS
    # ==========================================
    
    def generate_unique_id(self, length: int = 10) -> str:
        """Génère un ID unique alphanumérique"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def create_cloned_bot(self, bot_token: str, master_id: int, bot_username: str, 
                               bot_id: int, api_id: int = None, api_hash: str = None) -> Dict:
        """Crée un nouveau bot cloné"""
        now = datetime.now(timezone.utc)
        
        # Générer ID_PUBS et ID_CODE liés
        id_pubs = self.generate_unique_id(12)
        id_code = self.generate_unique_id(16)
        
        # Vérifier unicité
        while await self.id_codes_col.find_one({'id_pubs': id_pubs}):
            id_pubs = self.generate_unique_id(12)
        while await self.id_codes_col.find_one({'id_code': id_code}):
            id_code = self.generate_unique_id(16)
        
        bot_data = {
            '_id': bot_id,
            'bot_token': bot_token,
            'bot_username': bot_username,
            'master_id': master_id,
            'created_at': now.isoformat(),
            'is_active': True,
            'settings': {
                'start_message': None,
                'start_photo': None,
                'custom_buttons': [],
                'channel_id': None,
                'force_sub_channels': []
            },
            'stats': {
                'total_users': 0,
                'total_files_sent': 0,
                'total_ads_watched': 0
            }
        }
        
        # Sauvegarder le bot
        await self.cloned_bots_col.insert_one(bot_data)
        
        # Sauvegarder les IDs liés
        await self.id_codes_col.insert_one({
            '_id': bot_id,
            'bot_id': bot_id,
            'id_pubs': id_pubs,
            'id_code': id_code,
            'master_id': master_id,
            'created_at': now.isoformat()
        })
        
        # Créer l'entrée de gains
        await self.bot_earnings_col.insert_one({
            '_id': bot_id,
            'bot_id': bot_id,
            'balance': 0.0,
            'total_earned': 0.0,
            'total_withdrawn': 0.0,
            'transactions': [],
            'master_id': master_id
        })
        
        # Ajouter le maître comme admin de type 'maitre'
        await self.add_bot_admin(bot_id, master_id, 'maitre', master_id)
        
        return {
            'bot_data': bot_data,
            'id_pubs': id_pubs,
            'id_code': id_code
        }

    async def get_cloned_bot(self, bot_id: int) -> Optional[Dict]:
        """Récupère les infos d'un bot cloné"""
        return await self.cloned_bots_col.find_one({'_id': bot_id})

    async def get_cloned_bot_by_token(self, bot_token: str) -> Optional[Dict]:
        """Récupère un bot par son token"""
        return await self.cloned_bots_col.find_one({'bot_token': bot_token})

    async def get_all_cloned_bots(self, master_id: int = None) -> List[Dict]:
        """Récupère tous les bots clonés (ou ceux d'un maître spécifique)"""
        query = {}
        if master_id:
            query['master_id'] = master_id
        return await self.cloned_bots_col.find(query).to_list(length=None)

    async def update_bot_settings(self, bot_id: int, settings: Dict) -> bool:
        """Met à jour les paramètres d'un bot"""
        result = await self.cloned_bots_col.update_one(
            {'_id': bot_id},
            {'$set': {'settings': settings}}
        )
        return result.modified_count > 0

    async def delete_cloned_bot(self, bot_id: int) -> bool:
        """Supprime un bot cloné"""
        result = await self.cloned_bots_col.delete_one({'_id': bot_id})
        await self.id_codes_col.delete_one({'_id': bot_id})
        await self.bot_earnings_col.delete_one({'_id': bot_id})
        await self.bot_admins_col.delete_many({'bot_id': bot_id})
        return result.deleted_count > 0

    async def regenerate_id_code(self, bot_id: int, master_id: int) -> Optional[Dict]:
        """Régénère l'ID_CODE et ID_PUBS d'un bot"""
        bot = await self.get_cloned_bot(bot_id)
        if not bot or bot['master_id'] != master_id:
            return None
        
        new_id_pubs = self.generate_unique_id(12)
        new_id_code = self.generate_unique_id(16)
        
        # Vérifier unicité
        while await self.id_codes_col.find_one({'id_pubs': new_id_pubs}):
            new_id_pubs = self.generate_unique_id(12)
        while await self.id_codes_col.find_one({'id_code': new_id_code}):
            new_id_code = self.generate_unique_id(16)
        
        await self.id_codes_col.update_one(
            {'_id': bot_id},
            {'$set': {
                'id_pubs': new_id_pubs,
                'id_code': new_id_code,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            'id_pubs': new_id_pubs,
            'id_code': new_id_code
        }

    # ==========================================
    # SYSTÈME DE CLONAGE - ADMINS DE BOT
    # ==========================================
    
    async def add_bot_admin(self, bot_id: int, user_id: int, role: str, added_by: int) -> bool:
        """Ajoute un admin à un bot (role: 'maitre' ou 'admin')"""
        if role not in ['maitre', 'admin']:
            return False
        
        await self.bot_admins_col.update_one(
            {'bot_id': bot_id, 'user_id': user_id},
            {'$set': {
                'bot_id': bot_id,
                'user_id': user_id,
                'role': role,
                'added_by': added_by,
                'added_at': datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        return True

    async def remove_bot_admin(self, bot_id: int, user_id: int) -> bool:
        """Supprime un admin d'un bot"""
        result = await self.bot_admins_col.delete_one({
            'bot_id': bot_id,
            'user_id': user_id
        })
        return result.deleted_count > 0

    async def get_bot_admins(self, bot_id: int) -> List[Dict]:
        """Récupère tous les admins d'un bot"""
        return await self.bot_admins_col.find({'bot_id': bot_id}).to_list(length=None)

    async def get_user_bot_role(self, bot_id: int, user_id: int) -> Optional[str]:
        """Récupère le rôle d'un utilisateur sur un bot (maitre, admin, ou None)"""
        admin_data = await self.bot_admins_col.find_one({
            'bot_id': bot_id,
            'user_id': user_id
        })
        return admin_data['role'] if admin_data else None

    async def is_bot_admin(self, bot_id: int, user_id: int) -> bool:
        """Vérifie si l'utilisateur est admin d'un bot"""
        admin_data = await self.bot_admins_col.find_one({
            'bot_id': bot_id,
            'user_id': user_id
        })
        return admin_data is not None

    async def is_bot_master(self, bot_id: int, user_id: int) -> bool:
        """Vérifie si l'utilisateur est le maître du bot"""
        bot = await self.get_cloned_bot(bot_id)
        if bot and bot['master_id'] == user_id:
            return True
        admin_data = await self.bot_admins_col.find_one({
            'bot_id': bot_id,
            'user_id': user_id,
            'role': 'maitre'
        })
        return admin_data is not None

    # ==========================================
    # SYSTÈME DE CLONAGE - ID CODES
    # ==========================================
    
    async def get_id_codes(self, bot_id: int = None, id_pubs: str = None, id_code: str = None) -> Optional[Dict]:
        """Récupère les ID codes par bot_id, id_pubs ou id_code"""
        query = {}
        if bot_id:
            query['_id'] = bot_id
        if id_pubs:
            query['id_pubs'] = id_pubs
        if id_code:
            query['id_code'] = id_code
        
        if not query:
            return None
        return await self.id_codes_col.find_one(query)

    async def get_bot_by_id_pubs(self, id_pubs: str) -> Optional[Dict]:
        """Récupère un bot par son ID_PUBS"""
        id_data = await self.id_codes_col.find_one({'id_pubs': id_pubs})
        if id_data:
            return await self.get_cloned_bot(id_data['bot_id'])
        return None

    # ==========================================
    # SYSTÈME DE CLONAGE - GAGN ET RETRAITS
    # ==========================================
    
    async def add_earning(self, bot_id: int, amount: float, source: str = 'ad_impression') -> bool:
        """Ajoute des gains à un bot"""
        transaction = {
            'type': 'earning',
            'amount': amount,
            'source': source,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        result = await self.bot_earnings_col.update_one(
            {'_id': bot_id},
            {
                '$inc': {
                    'balance': amount,
                    'total_earned': amount
                },
                '$push': {'transactions': transaction}
            }
        )
        return result.modified_count > 0

    async def request_withdrawal(self, bot_id: int, amount: float, method: str = 'crypto') -> Dict:
        """Demande un retrait (minimum 7$)"""
        earnings = await self.bot_earnings_col.find_one({'_id': bot_id})
        
        if not earnings:
            return {'success': False, 'error': 'Bot not found'}
        
        if earnings['balance'] < 7.0:
            return {'success': False, 'error': 'Minimum withdrawal is $7'}
        
        if earnings['balance'] < amount:
            return {'success': False, 'error': 'Insufficient balance'}
        
        transaction = {
            'type': 'withdrawal',
            'amount': amount,
            'method': method,
            'status': 'pending',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await self.bot_earnings_col.update_one(
            {'_id': bot_id},
            {
                '$inc': {'balance': -amount},
                '$push': {'transactions': transaction}
            }
        )
        
        return {
            'success': True,
            'transaction': transaction,
            'remaining_balance': earnings['balance'] - amount
        }

    async def get_bot_earnings(self, bot_id: int) -> Optional[Dict]:
        """Récupère les gains d'un bot"""
        return await self.bot_earnings_col.find_one({'_id': bot_id})

    async def admin_credit_balance(self, bot_id: int, amount: float) -> bool:
        """Crédite le solde d'un bot (admin/owner only)"""
        transaction = {
            'type': 'credit',
            'amount': amount,
            'source': 'admin',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        result = await self.bot_earnings_col.update_one(
            {'_id': bot_id},
            {
                '$inc': {
                    'balance': amount,
                    'total_earned': amount
                },
                '$push': {'transactions': transaction}
            }
        )
        return result.modified_count > 0

    # ==========================================
    # SYSTÈME DE CLONAGE - STATISTIQUES
    # ==========================================
    
    async def increment_bot_stat(self, bot_id: int, stat_name: str, increment: int = 1) -> bool:
        """Incrémente une statistique d'un bot"""
        valid_stats = ['total_users', 'total_files_sent', 'total_ads_watched']
        if stat_name not in valid_stats:
            return False
        
        result = await self.cloned_bots_col.update_one(
            {'_id': bot_id},
            {'$inc': {f'stats.{stat_name}': increment}}
        )
        return result.modified_count > 0

    async def get_bot_stats(self, bot_id: int) -> Optional[Dict]:
        """Récupère les statistiques d'un bot"""
        bot = await self.get_cloned_bot(bot_id)
        if bot:
            return bot.get('stats', {})
        return None

    async def get_all_bots_stats(self) -> List[Dict]:
        """Récupère les stats de tous les bots (pour owner)"""
        bots = await self.cloned_bots_col.find({}).to_list(length=None)
        stats = []
        for bot in bots:
            earnings = await self.get_bot_earnings(bot['_id'])
            id_codes = await self.get_id_codes(bot_id=bot['_id'])
            stats.append({
                'bot_id': bot['_id'],
                'username': bot['bot_username'],
                'master_id': bot['master_id'],
                'created_at': bot['created_at'],
                'is_active': bot['is_active'],
                'stats': bot.get('stats', {}),
                'earnings': earnings,
                'id_pubs': id_codes.get('id_pubs') if id_codes else None
            })
        return stats


# Initialisation de la base de données
db = Rohit()
