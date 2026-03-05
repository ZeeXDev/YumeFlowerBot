/* ============================================================
   API.JS — Toutes les requêtes vers web_server.py
   YumeFlower WebApp
   ============================================================ */

const API = (() => {

  // ── CONFIGURATION ──────────────────────────────────────────
  // localhost pour test Termux, mettre l'URL Render en prod
  const BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8080'
    : 'https://yumeflowerbot.koyeb.app';   // ← sans /api ici !

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
      const url = `${BASE_URL}${path}`;  // ← path inclut déjà /api/
      console.log(`[API] ${method} ${url}`, body);
      
      const res = await fetch(url, options);
      clearTimeout(timer);
      
      const data = await res.json();
      console.log(`[API] Response:`, data);
      
      return { ok: res.ok, status: res.status, data };
    } catch (err) {
      clearTimeout(timer);
      console.error(`[API] Error:`, err);
      
      if (err.name === 'AbortError') {
        return { ok: false, status: 0, data: { error: 'Délai dépassé. Réessayez.' } };
      }
      return { ok: false, status: 0, data: { error: err.message || 'Erreur réseau' } };
    }
  }

  const get  = (path)        => request('GET',  path);
  const post = (path, body)  => request('POST', path, body);

  // ── ID_PUBS ────────────────────────────────────────────────

  async function verifyIdPubs(idPubs) {
    return post('/api/verify-id-pubs', { id_pubs: idPubs });
  }

  async function watchAdClone(userId, idPubs, auth = null) {
    const body = { user_id: userId, id_pubs: idPubs };
    if (auth) body.auth = auth;
    return post('/api/watch-ad-clone', body);
  }

  async function checkSessionClone(userId, idPubs) {
    return post('/api/check-session-clone', { user_id: userId, id_pubs: idPubs });
  }

  async function checkSession(userId) {
    return post('/api/check-session', { user_id: userId });
  }

  async function watchAd(userId, auth = null) {
    const body = { user_id: userId };
    if (auth) body.auth = auth;
    return post('/api/watch-ad', body);
  }

  // ── MASTER (ID_CODE) ───────────────────────────────────────

  async function masterLogin(idCode, auth = null) {
    const body = { id_code: idCode };
    if (auth) body.auth = auth;
    return post('/api/master/login', body);
  }

  async function masterWithdraw(idCode, amount, method, accountInfo) {
    return post('/api/master/withdraw', {
      id_code: idCode,
      amount,
      method,
      account_info: accountInfo
    });
  }

  async function masterRegenerate(idCode, auth = null) {
    const body = { id_code: idCode };
    if (auth) body.auth = auth;
    return post('/api/master/regenerate-code', body);
  }

  // ── ADMIN ──────────────────────────────────────────────────

  async function adminLogin(password) {
    return post('/api/admin/login', { password });
  }

  async function adminStats() {
    return get('/api/admin/stats');
  }

  // ── PAYMENT ───────────────────────────────────────────────

  async function createPayment(userId, auth, plan = 'monthly') {
    return post('/api/payment', { user_id: userId, auth, plan });
  }

  // ── HEALTH ────────────────────────────────────────────────

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
