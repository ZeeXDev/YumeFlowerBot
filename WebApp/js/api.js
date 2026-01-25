/**
 * API CLIENT
 * ===========
 * Gestion de toutes les communications avec le backend Python
 * 
 * Endpoints disponibles :
 * - POST /api/check-session : Vérifier si l'utilisateur a une session active
 * - POST /api/watch-ad : Créer une session après visionnage pub Monetag
 * - POST /api/payment : Créer une session premium après paiement
 * - POST /api/admin/login : Authentification admin
 * - POST /api/admin/config : Modifier la configuration
 * - GET /api/admin/stats : Récupérer les statistiques
 */

const API_BASE = 'https://test-cey.onrender.com';

class API {
  /**
   * Vérifie si l'utilisateur a une session active
   * @param {number} userId - ID Telegram de l'utilisateur
   * @param {string} authData - initData de Telegram pour validation
   * @returns {Promise<Object>} - { has_access: boolean, expires_at?: string, type?: string }
   */
  static async checkSession(userId, authData) {
    try {
      const response = await fetch(`${API_BASE}/api/check-session`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': authData
        },
        body: JSON.stringify({ 
          user_id: userId,
          auth: authData 
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[API] Check session:', data);
      return data;
    } catch (error) {
      console.error('[API] Check session error:', error);
      return { 
        has_access: false,
        error: error.message 
      };
    }
  }

  /**
   * Crée une session gratuite après visionnage d'une pub Monetag
   * @param {number} userId - ID Telegram de l'utilisateur
   * @param {string} authData - initData de Telegram
   * @returns {Promise<Object>} - { success: boolean, duration?: number, expires_at?: string }
   */
  static async watchAd(userId, authData) {
    try {
      const response = await fetch(`${API_BASE}/api/watch-ad`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': authData
        },
        body: JSON.stringify({ 
          user_id: userId,
          auth: authData,
          timestamp: Date.now()
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[API] Watch ad response:', data);
      return data;
    } catch (error) {
      console.error('[API] Watch ad error:', error);
      return { 
        success: false,
        error: error.message 
      };
    }
  }

  /**
   * Crée une session premium après paiement
   * @param {number} userId - ID Telegram de l'utilisateur
   * @param {string} authData - initData de Telegram
   * @param {Object} paymentData - Données du paiement
   * @returns {Promise<Object>} - { success: boolean, duration?: number }
   */
  static async createPremiumSession(userId, authData, paymentData) {
    try {
      const response = await fetch(`${API_BASE}/api/payment`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': authData
        },
        body: JSON.stringify({ 
          user_id: userId,
          auth: authData,
          payment_method: paymentData.method,
          amount: paymentData.amount,
          currency: paymentData.currency,
          plan: paymentData.plan,
          transaction_id: paymentData.transactionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[API] Payment response:', data);
      return data;
    } catch (error) {
      console.error('[API] Payment error:', error);
      return { 
        success: false,
        error: error.message 
      };
    }
  }

  /**
   * ADMIN - Authentification
   * @param {string} password - Mot de passe admin
   * @returns {Promise<Object>} - { success: boolean, token?: string }
   */
  static async adminLogin(password) {
    try {
      const response = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Stocker le token en mémoire (pas localStorage car non supporté)
      if (data.success && data.token) {
        window.adminToken = data.token;
      }
      
      return data;
    } catch (error) {
      console.error('[API] Admin login error:', error);
      return { 
        success: false,
        error: error.message 
      };
    }
  }

  /**
   * ADMIN - Récupérer les statistiques
   * @returns {Promise<Object>} - Statistiques du système
   */
  static async getAdminStats() {
    try {
      const response = await fetch(`${API_BASE}/api/admin/stats`, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${window.adminToken || ''}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[API] Admin stats:', data);
      return data;
    } catch (error) {
      console.error('[API] Admin stats error:', error);
      return { 
        success: false,
        error: error.message 
      };
    }
  }

  /**
   * ADMIN - Mettre à jour la configuration
   * @param {Object} config - Nouvelle configuration
   * @returns {Promise<Object>} - { success: boolean }
   */
  static async updateConfig(config) {
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${window.adminToken || ''}`
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[API] Config updated:', data);
      return data;
    } catch (error) {
      console.error('[API] Update config error:', error);
      return { 
        success: false,
        error: error.message 
      };
    }
  }

  /**
   * Utilitaire : Formater la durée restante
   * @param {string} expiresAt - ISO timestamp
   * @returns {number} - Minutes restantes
   */
  static getRemainingMinutes(expiresAt) {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diffMs = expires - now;
    return Math.max(0, Math.floor(diffMs / 60000));
  }

  /**
   * Utilitaire : Formater la durée restante en secondes
   * @param {string} expiresAt - ISO timestamp
   * @returns {number} - Secondes restantes
   */
  static getRemainingSeconds(expiresAt) {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diffMs = expires - now;
    return Math.max(0, Math.floor(diffMs / 1000));
  }
}