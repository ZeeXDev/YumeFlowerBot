/* ============================================================
   APP.JS — Logique principale, Toast, Monetag, Navigation
   YumeFlower WebApp
   ============================================================ */

// ── MONETAG CONFIG ─────────────────────────────────────────
// Remplace par ton vrai Zone ID Monetag
const MONETAG_ZONE_ID = '10518701';

// ── TOAST ─────────────────────────────────────────────────
const Toast = (() => {
  let _timer = null;

  function show(message, type = 'info', duration = 3000) {
    const el = document.getElementById('toast');
    if (!el) return;

    el.textContent = message;
    el.className = `show ${type}`;

    clearTimeout(_timer);
    _timer = setTimeout(() => {
      el.classList.remove('show');
    }, duration);
  }

  return {
    success: (msg, d) => show(msg, 'success', d),
    error:   (msg, d) => show(msg, 'error',   d),
    info:    (msg, d) => show(msg, 'info',     d),
  };
})();

// ── MONETAG AD ─────────────────────────────────────────────
const MonetAd = (() => {

  let _onComplete = null;
  let _onError    = null;

  /**
   * Lance une pub Monetag Interstitial/OnClick
   * Appelle onComplete() quand la pub est terminée (ou simulée en dev)
   */
  function show(onComplete, onError) {
    _onComplete = onComplete;
    _onError    = onError || (() => {});

    if (!TG.isInTelegram() && window.location.hostname === 'localhost') {
      // ── MODE DEV : simuler pub de 3 secondes ──
      console.log('[AD] Mode dev — simulation pub 3s');
      _showDevOverlay();
      return;
    }

    // ── MODE PROD : Monetag ──
    try {
      if (typeof window.show_9403709 === 'function') {
        // API Monetag Onclick/Interstitial
        window.show_9403709()
          .then(() => {
            console.log('[AD] Pub Monetag terminée');
            if (_onComplete) _onComplete();
          })
          .catch(err => {
            console.error('[AD] Erreur Monetag:', err);
            // On valide quand même pour ne pas bloquer l'utilisateur
            if (_onComplete) _onComplete();
          });
      } else {
        // SDK pas encore chargé → simuler
        console.warn('[AD] Monetag SDK non disponible, simulation');
        setTimeout(() => { if (_onComplete) _onComplete(); }, 2000);
      }
    } catch (err) {
      console.error('[AD] Erreur lancement pub:', err);
      setTimeout(() => { if (_onComplete) _onComplete(); }, 2000);
    }
  }

  // Overlay de simulation en dev
  function _showDevOverlay() {
    let overlay = document.getElementById('dev-ad-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'dev-ad-overlay';
      overlay.style.cssText = `
        position: fixed; inset: 0; z-index: 9000;
        background: rgba(0,0,0,0.95);
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        gap: 16px; font-family: 'DM Sans', sans-serif;
        color: #fff;
      `;
      overlay.innerHTML = `
        <div style="width:80px;height:80px;background:#1A1A1A;border:1px solid #333;
          border-radius:12px;display:flex;align-items:center;justify-content:center;">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FF1A1A" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </div>
        <div style="font-size:14px;color:#777;">Publicité (simulation dev)</div>
        <div id="dev-ad-count" style="font-family:'Bebas Neue',sans-serif;font-size:48px;color:#FF1A1A;">3</div>
        <div style="font-size:12px;color:#555;">Patientez...</div>
      `;
      document.body.appendChild(overlay);
    }

    overlay.style.display = 'flex';
    let count = 3;

    const countEl = document.getElementById('dev-ad-count');
    const iv = setInterval(() => {
      count--;
      if (countEl) countEl.textContent = count;
      if (count <= 0) {
        clearInterval(iv);
        overlay.style.display = 'none';
        if (_onComplete) _onComplete();
      }
    }, 1000);
  }

  return { show };

})();

// ── STORAGE LOCAL ─────────────────────────────────────────
const Store = {
  get(key)        { try { return JSON.parse(localStorage.getItem(key)); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch {} },
  remove(key)     { try { localStorage.removeItem(key); } catch {} }
};

// ── UI HELPERS ────────────────────────────────────────────
function show(id)  {
  const el = document.getElementById(id);
  if (el) el.style.display = '';
}

function hide(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setHTML(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

function setLoading(btnId, loading, originalText = null) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.innerHTML = '<span class="btn-spinner"></span>';
    btn.classList.add('loading');
    btn.disabled = true;
  } else {
    btn.innerHTML = originalText || btn.dataset.originalText || btn.textContent;
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

// ── COPY TO CLIPBOARD ────────────────────────────────────
async function copyToClipboard(text, successMsg = 'Copié !') {
  const ok = await TG.copyText(text);
  if (ok) {
    Toast.success(successMsg);
    TG.hapticLight();
  } else {
    Toast.error('Impossible de copier');
  }
}

// ── ANIMATE IN ────────────────────────────────────────────
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
  const els = document.querySelectorAll(selector);
  els.forEach((el, i) => animateIn(el, baseDelay + i * step));
}

// ── SVG ICONS (inline) ────────────────────────────────────
const Icons = {
  lock:    `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
  check:   `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  play:    `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`,
  star:    `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  copy:    `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`,
  refresh: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`,
  arrow:   `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`,
};

// ── EXPORT GLOBAL ────────────────────────────────────────
window.App = {
  Toast,
  MonetAd,
  Store,
  Icons,
  show, hide, setText, setHTML,
  setLoading, copyToClipboard,
  animateIn, staggerIn,
};

// Compatibilité raccourcie
window.toast   = Toast;
window.showToast = (msg, type) => Toast[type] ? Toast[type](msg) : Toast.info(msg);
