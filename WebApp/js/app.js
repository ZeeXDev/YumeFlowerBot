/* ============================================================
   APP.JS — Logique principale, Toast, Monetag, Navigation
   YumeFlower WebApp
   ============================================================ */

// ── MONETAG CONFIG ─────────────────────────────────────────
// ⚠️  Remplace par ton vrai Zone ID Monetag
const MONETAG_ZONE_ID = '10518701';

// ── TOAST ──────────────────────────────────────────────────
const Toast = (() => {
  let _timer = null;
  function show(message, type = 'info', duration = 3000) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.className = `show ${type}`;
    clearTimeout(_timer);
    _timer = setTimeout(() => el.classList.remove('show'), duration);
  }
  return {
    success: (msg, d) => show(msg, 'success', d),
    error:   (msg, d) => show(msg, 'error',   d),
    info:    (msg, d) => show(msg, 'info',     d),
  };
})();

// ── MONETAG AD ─────────────────────────────────────────────
const MonetAd = (() => {
  function show(onComplete, onError) {
    onError = onError || (() => {});

    // Mode dev uniquement si pas dans Telegram
    if (!TG.isInTelegram()) {
      _showDevOverlay(onComplete);
      return;
    }

    try {
      const fnName = `show_${MONETAG_ZONE_ID}`;
      if (typeof window[fnName] === 'function') {
        window[fnName]()
          .then(() => { if (onComplete) onComplete(); })
          .catch(() => { if (onComplete) onComplete(); });
      } else {
        // SDK pas encore chargé, attendre 3s et retenter
        setTimeout(() => {
          if (typeof window[fnName] === 'function') {
            window[fnName]()
              .then(() => { if (onComplete) onComplete(); })
              .catch(() => { if (onComplete) onComplete(); });
          } else {
            if (onError) onError();
          }
        }, 3000);
      }
    } catch (err) {
      if (onError) onError();
    }
  }

  function _showDevOverlay(onComplete) {
    let overlay = document.getElementById('dev-ad-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'dev-ad-overlay';
      overlay.style.cssText = 'position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,0.97);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;font-family:DM Sans,sans-serif;color:#fff;';
      overlay.innerHTML = '<div style="width:80px;height:80px;background:#1A1A1A;border:1px solid #333;border-radius:12px;display:flex;align-items:center;justify-content:center;"><svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FF1A1A" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg></div><div style="font-size:14px;color:#777;letter-spacing:1px;">PUBLICITE EN COURS</div><div id="dev-ad-count" style="font-family:Bebas Neue,sans-serif;font-size:64px;color:#FF1A1A;line-height:1;">5</div><div style="font-size:12px;color:#555;">Ne fermez pas cette fenetre...</div>';
      document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
    let count = 5;
    const countEl = document.getElementById('dev-ad-count');
    const iv = setInterval(() => {
      count--;
      if (countEl) countEl.textContent = count;
      if (count <= 0) {
        clearInterval(iv);
        overlay.style.display = 'none';
        if (onComplete) onComplete();
      }
    }, 1000);
  }

  return { show };
})();

// ── STORE — isolé par user_id Telegram ───────────────────
// Chaque compte Telegram a son propre espace de stockage
const Store = (() => {
  function _key(key) {
    // getUserId() peut ne pas être encore dispo → on essaie
    let uid = 'anon';
    try { uid = TG.getUserId() || 'anon'; } catch {}
    return `yf_${uid}_${key}`;
  }

  function get(key)        { try { return JSON.parse(localStorage.getItem(_key(key))); } catch { return null; } }
  function set(key, value) { try { localStorage.setItem(_key(key), JSON.stringify(value)); } catch {} }
  function remove(key)     { try { localStorage.removeItem(_key(key)); } catch {} }

  return { get, set, remove };
})();

// ── UI HELPERS ────────────────────────────────────────────
function show(id)  { const e = document.getElementById(id); if (e) e.style.display = ''; }
function hide(id)  { const e = document.getElementById(id); if (e) e.style.display = 'none'; }
function setText(id, t) { const e = document.getElementById(id); if (e) e.textContent = t; }
function setHTML(id, h) { const e = document.getElementById(id); if (e) e.innerHTML = h; }

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (loading) {
    btn.dataset.originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="btn-spinner"></span>';
    btn.classList.add('loading');
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalHTML || btn.innerHTML;
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

async function copyToClipboard(text, successMsg = 'Copie !') {
  const ok = await TG.copyText(text);
  if (ok) Toast.success(successMsg);
  else Toast.error('Impossible de copier');
}

function animateIn(el, delay = 0) {
  if (!el) return;
  el.style.opacity = '0';
  el.style.transform = 'translateY(14px)';
  setTimeout(() => {
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  }, delay);
}

function staggerIn(selector, baseDelay = 0, step = 80) {
  document.querySelectorAll(selector).forEach((el, i) => animateIn(el, baseDelay + i * step));
}

// ── EXPORT GLOBAL ────────────────────────────────────────
window.App = { Toast, MonetAd, Store, show, hide, setText, setHTML, setLoading, copyToClipboard, animateIn, staggerIn };
window.toast = Toast;
window.showToast = (msg, type) => Toast[type] ? Toast[type](msg) : Toast.info(msg);
