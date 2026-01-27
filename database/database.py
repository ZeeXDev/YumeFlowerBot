#Codeflix_Botz
#rohit_1888 on Tg

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

logging.basicConfig(level=logging.INFO)


class Rohit:
    def __init__(self):
        # Connexion MongoDB
        self.client = AsyncIOMotorClient(DB_URI)
        self.db = self.client[DB_NAME]
        
        # Collections
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
        
        # Références aux collections MongoDB
        self.users_col = self.db[self.user_data_name]
        self.admins_col = self.db[self.admins_data_name]
        self.banned_col = self.db[self.banned_user_name]
        self.del_timer_col = self.db[self.del_timer_name]
        self.fsub_col = self.db[self.fsub_name]
        self.rqst_fsub_col = self.db[self.rqst_fsub_channel_name]
        self.sessions_col = self.db[self.user_sessions_name]
        self.config_col = self.db[self.config_name]

    # ==========================================
    # USER DATA
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
    # ADMIN DATA
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
    # BAN USER DATA
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
    # AUTO DELETE TIMER SETTINGS
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
    # CHANNEL MANAGEMENT
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
    # REQUEST FORCE-SUB MANAGEMENT
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
    # SESSIONS MANAGEMENT (FREE & PREMIUM)
    # ==========================================
    
    async def get_user_session(self, user_id: int) -> Optional[Dict]:
        """Récupère les informations de session d'un utilisateur"""
        return await self.sessions_col.find_one({'_id': user_id})

    async def create_free_session(self, user_id: int, duration_minutes: int = 10) -> Dict:
        """Crée une session gratuite après pub"""
        now = datetime.now(timezone.utc)
        expiry_time = now + timedelta(minutes=duration_minutes)
        session_data = {
            '_id': user_id,
            'type': 'free',
            'is_active': True,
            'created_at': now.isoformat(),
            'expires_at': expiry_time.isoformat(),
            'last_ad_watch': now.isoformat()
        }
        await self.sessions_col.update_one(
            {'_id': user_id},
            {'$set': session_data},
            upsert=True
        )
        print(f"[DB] Session créée pour user {user_id}, expire à {expiry_time}")
        return session_data

    async def create_premium_session(self, user_id: int, duration_seconds: int, admin_id: int = None) -> Dict:
        """Crée une session premium (via paiement ou admin)"""
        now = datetime.now(timezone.utc)
        expiry_time = now + timedelta(seconds=duration_seconds)
        session_data = {
            '_id': user_id,
            'type': 'premium',
            'is_active': True,
            'created_at': now.isoformat(),
            'expires_at': expiry_time.isoformat(),
            'granted_by': admin_id,
            'payment_method': 'manual' if admin_id else 'crypto'
        }
        await self.sessions_col.update_one(
            {'_id': user_id},
            {'$set': session_data},
            upsert=True
        )
        return session_data

    async def set_free_session(self, user_id: int, duration_hours: int = 20) -> None:
        """Méthode compatible avec l'ancien système AdsGram (utilise des heures)"""
        # Convertir heures en minutes pour la cohérence
        await self.create_free_session(user_id, duration_hours * 60)

    async def has_active_session(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur a une session active (free ou premium)"""
        session = await self.get_user_session(user_id)
        if not session or not session.get('is_active'):
            return False
        
        try:
            # Gérer les dates avec ou sans timezone
            expiry_str = session['expires_at']
            if expiry_str.endswith('Z'):
                expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            else:
                expiry = datetime.fromisoformat(expiry_str)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            
            print(f"[DEBUG] Session check - Now: {now}, Expiry: {expiry}, Diff: {(expiry - now).total_seconds()}s")
            
            if now > expiry:
                # Session expirée, la désactiver
                await self.deactivate_session(user_id)
                return False
            
            return True
        except Exception as e:
            print(f"[ERROR] Erreur vérification session: {e}")
            return False

    async def deactivate_session(self, user_id: int) -> None:
        """Désactive une session"""
        await self.sessions_col.update_one(
            {'_id': user_id},
            {'$set': {'is_active': False}}
        )

    async def remove_session(self, user_id: int) -> None:
        """Supprime complètement une session"""
        await self.sessions_col.delete_one({'_id': user_id})

    async def get_session_time_left(self, user_id: int) -> int:
        """Retourne le nombre de secondes restantes"""
        session = await self.get_user_session(user_id)
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
        """
        VÉRIFICATION DÉSACTIVÉE - SPAM AUTORISÉ
        Les utilisateurs peuvent regarder des pubs en boucle sans limite de temps
        """
        # Toujours retourner True pour permettre le spam de pubs
        return True

    async def force_reset_ad_timer(self, user_id: int) -> None:
        """Reset le timer de pub (pour tests ou admin)"""
        await self.sessions_col.update_one(
            {'_id': user_id},
            {'$unset': {'last_ad_watch': ''}}
        )
        print(f"[DB] Timer reset for user {user_id}")

    # ==========================================
    # ADMIN CONFIGURATION
    # ==========================================
    
    async def set_free_session_duration(self, minutes: int) -> None:
        """Définit la durée des sessions gratuites en minutes (config admin)"""
        await self.config_col.update_one(
            {'_id': 'settings'},
            {'$set': {'free_session_duration': minutes}},
            upsert=True
        )

    async def get_free_session_duration(self) -> int:
        """Récupère la durée configurée (défaut: 10 minutes)"""
        config = await self.config_col.find_one({'_id': 'settings'})
        return config.get('free_session_duration', 10) if config else 10


# Initialisation de la base de données
db = Rohit()
