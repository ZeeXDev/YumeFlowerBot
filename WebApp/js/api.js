const API_BASE = 'https://test-cey.onrender.com';

class API {
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

  static async adminLogin(password) {
    try {
      console.log('[API] Tentative login admin...');
      const response = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: password })
      });

      const data = await response.json();
      console.log('[API] Admin login response:', data);
      
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

  static getRemainingMinutes(expiresAt) {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diffMs = expires - now;
    return Math.max(0, Math.floor(diffMs / 60000));
  }

  static getRemainingSeconds(expiresAt) {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diffMs = expires - now;
    return Math.max(0, Math.floor(diffMs / 1000));
  }
}
