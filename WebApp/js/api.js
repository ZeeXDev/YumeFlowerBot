/* ============================================================
   API.JS — Toutes les requêtes vers web_server.py
   YumeFlower WebApp
   Changer BASE_URL selon l'environnement
   ============================================================ */

const API = (() => {

  // ── CONFIGURATION ──────────────────────────────────────────
  // localhost pour test Termux, mettre l'URL Render en prod
  const BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8080'
    : 'https://YumeFlowerBot.onrender.com';   // ← changer ici pour Render

  const TIMEOUT_MS = 12000;

  // ── REQUEST HELPER ─────────────────────────────────────────
  async function request(method, path, body = null) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const options = {
      method,
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json' }
    };

    if (body) options.body = JSON.stringify(body);

    try {
      const res = await fetch(`${BASE_URL}${path}`, options);
      clearTimeout(timer);
      const data = await res.json();
      return { ok: res.ok, status: res.status, data };
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        return { ok: false, status: 0, data: { error: 'Délai dépassé. Réessayez.' } };
      }
      return { ok: false, status: 0, data: { error: err.message || 'Erreur réseau' } };
    }
  }

  const get  = (path)        => request('GET',  path);
  const post = (path, body)  => request('POST', path, body);

  // ── ID_PUBS ────────────────────────────────────────────────

  /**
   * Vérifie un ID_PUBS et retourne les infos du bot
   * POST /api/verify-id-pubs
   * { id_pubs: string }
   * → { success, bot: { id, username, name }, id_pubs }
   */
  async function verifyIdPubs(idPubs) {
    return post('/api/verify-id-pubs', { id_pubs: idPubs });
  }

  /**
   * Active une session gratuite après pub Monetag
   * POST /api/watch-ad-clone
   * { user_id, id_pubs, auth? }
   * → { success, duration, expires_at, bot_username, message }
   */
  async function watchAdClone(userId, idPubs, auth = null) {
    const body = { user_id: userId, id_pubs: idPubs };
    if (auth) body.auth = auth;
    return post('/api/watch-ad-clone', body);
  }

  /**
   * Vérifie la session active pour un bot cloné
   * POST /api/check-session-clone
   * { user_id, id_pubs }
   * → { success, has_access, time_left, expires_at, type, bot_id }
   */
  async function checkSessionClone(userId, idPubs) {
    return post('/api/check-session-clone', { user_id: userId, id_pubs: idPubs });
  }

  /**
   * Vérifie la session pour le bot mère (pas d'id_pubs)
   * POST /api/check-session
   * { user_id }
   * → { has_access, time_left, expires_at, type, duration, can_watch_ad }
   */
  async function checkSession(userId) {
    return post('/api/check-session', { user_id: userId });
  }

  /**
   * Active une session gratuite sur le bot mère
   * POST /api/watch-ad
   * { user_id }
   * → { success, duration, expires_at }
   */
  async function watchAd(userId, auth = null) {
    const body = { user_id: userId };
    if (auth) body.auth = auth;
    return post('/api/watch-ad', body);
  }

  // ── MASTER (ID_CODE) ───────────────────────────────────────

  /**
   * Connexion à la page Maître avec ID_CODE
   * POST /api/master/login
   * { id_code, auth? }
   * → { success, bot, id_pubs, stats, earnings }
   */
  async function masterLogin(idCode, auth = null) {
    const body = { id_code: idCode };
    if (auth) body.auth = auth;
    return post('/api/master/login', body);
  }

  /**
   * Demande de retrait
   * POST /api/master/withdraw
   * { id_code, amount, method, account_info }
   * → { success, message }
   */
  async function masterWithdraw(idCode, amount, method, accountInfo) {
    return post('/api/master/withdraw', {
      id_code: idCode,
      amount,
      method,
      account_info: accountInfo
    });
  }

  /**
   * Régénère ID_CODE et ID_PUBS
   * POST /api/master/regenerate-code
   * { id_code, auth? }
   * → { success, id_pubs, id_code }
   */
  async function masterRegenerate(idCode, auth = null) {
    const body = { id_code: idCode };
    if (auth) body.auth = auth;
    return post('/api/master/regenerate-code', body);
  }

  // ── ADMIN ──────────────────────────────────────────────────

  /**
   * Login admin owner
   * POST /api/admin/login
   * { password }
   * → { success, token }
   */
  async function adminLogin(password) {
    return post('/api/admin/login', { password });
  }

  /**
   * Stats globales admin
   * GET /api/admin/stats
   */
  async function adminStats() {
    return get('/api/admin/stats');
  }

  // ── PAYMENT ───────────────────────────────────────────────

  /**
   * Crée une session premium après paiement
   * POST /api/payment
   * { user_id, auth, plan }
   * → { success, duration, expires_at, plan }
   */
  async function createPayment(userId, auth, plan = 'monthly') {
    return post('/api/payment', { user_id: userId, auth, plan });
  }

  // ── HEALTH ────────────────────────────────────────────────

  /**
   * Vérifie que le serveur est en ligne
   * GET /
   */
  async function health() {
    return get('/');
  }

  // ── PUBLIC API ────────────────────────────────────────────
  return {
    BASE_URL,
    verifyIdPubs,
    watchAdClone,
    checkSessionClone,
    checkSession,
    watchAd,
    masterLogin,
    masterWithdraw,
    masterRegenerate,
    adminLogin,
    adminStats,
    createPayment,
    health
  };

})();
