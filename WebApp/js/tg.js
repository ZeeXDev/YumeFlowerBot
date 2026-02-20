/* ============================================================
   TG.JS — Telegram WebApp init, user data, auth
   YumeFlower WebApp
   ============================================================ */

const TG = (() => {

  // ── INIT ───────────────────────────────────────────────────
  let _tg = null;
  let _user = null;
  let _initData = null;
  let _ready = false;

  function init() {
    try {
      _tg = window.Telegram?.WebApp;

      if (_tg) {
        _tg.ready();
        _tg.expand();
        _tg.enableClosingConfirmation();

        // Thème — forcer dark
        _tg.setHeaderColor('#000000');
        _tg.setBackgroundColor('#000000');

        _user = _tg.initDataUnsafe?.user || null;
        _initData = _tg.initData || null;
        _ready = true;

        console.log('[TG] WebApp initialized. User:', _user?.id);
      } else {
        // Mode debug hors Telegram (navigateur direct)
        console.warn('[TG] Not in Telegram WebApp. Using mock user for dev.');
        _user = {
          id: 123456789,
          first_name: 'Test',
          last_name: 'User',
          username: 'testuser',
          language_code: 'fr'
        };
        _ready = true;
      }
    } catch (err) {
      console.error('[TG] Init error:', err);
      _ready = true;
    }
  }

  // ── GETTERS ────────────────────────────────────────────────

  function isReady() { return _ready; }

  function isInTelegram() { return !!_tg; }

  function getUser() { return _user; }

  function getUserId() { return _user?.id || null; }

  function getFirstName() { return _user?.first_name || 'Utilisateur'; }

  function getUsername() { return _user?.username || null; }

  function getInitData() { return _initData; }

  /**
   * Retourne les données d'auth à passer à l'API
   * sous forme de query string (format Telegram)
   */
  function getAuth() {
    return _initData || null;
  }

  // ── START PARAM ────────────────────────────────────────────
  /**
   * Récupère le paramètre start_param (ex: depuis ?start=ID_PUBS)
   * Utile si le lien du bot contient l'id_pubs en paramètre
   */
  function getStartParam() {
    try {
      if (_tg?.initDataUnsafe?.start_param) {
        return _tg.initDataUnsafe.start_param;
      }
      // fallback URL param
      const params = new URLSearchParams(window.location.search);
      return params.get('id_pubs') || params.get('start') || null;
    } catch {
      return null;
    }
  }

  // ── HAPTIC ────────────────────────────────────────────────
  function haptic(type = 'impact', style = 'medium') {
    try {
      if (!_tg?.HapticFeedback) return;
      if (type === 'impact')       _tg.HapticFeedback.impactOccurred(style);
      if (type === 'notification') _tg.HapticFeedback.notificationOccurred(style);
      if (type === 'selection')    _tg.HapticFeedback.selectionChanged();
    } catch {}
  }

  function hapticSuccess()  { haptic('notification', 'success'); }
  function hapticError()    { haptic('notification', 'error'); }
  function hapticWarning()  { haptic('notification', 'warning'); }
  function hapticLight()    { haptic('impact', 'light'); }
  function hapticMedium()   { haptic('impact', 'medium'); }
  function hapticHeavy()    { haptic('impact', 'heavy'); }

  // ── NAVIGATION ────────────────────────────────────────────
  function close() { _tg?.close(); }

  function openLink(url) {
    if (_tg) {
      _tg.openLink(url);
    } else {
      window.open(url, '_blank');
    }
  }

  function openTelegramLink(url) {
    if (_tg) {
      _tg.openTelegramLink(url);
    } else {
      window.open(url, '_blank');
    }
  }

  // ── BACK BUTTON ───────────────────────────────────────────
  function showBack(callback) {
    if (!_tg) return;
    _tg.BackButton.show();
    _tg.BackButton.onClick(callback);
  }

  function hideBack() {
    if (!_tg) return;
    _tg.BackButton.hide();
    _tg.BackButton.offClick();
  }

  // ── MAIN BUTTON ───────────────────────────────────────────
  function showMainBtn(text, callback, color = '#FF1A1A') {
    if (!_tg) return;
    _tg.MainButton.setText(text);
    _tg.MainButton.setParams({ color, text_color: '#FFFFFF' });
    _tg.MainButton.onClick(callback);
    _tg.MainButton.show();
  }

  function hideMainBtn() {
    if (!_tg) return;
    _tg.MainButton.hide();
    _tg.MainButton.offClick();
  }

  function mainBtnLoading(active) {
    if (!_tg) return;
    if (active) _tg.MainButton.showProgress();
    else        _tg.MainButton.hideProgress();
  }

  // ── CLIPBOARD ─────────────────────────────────────────────
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // fallback
      const el = document.createElement('textarea');
      el.value = text;
      el.style.position = 'fixed';
      el.style.opacity = '0';
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      return true;
    }
  }

  // ── PUBLIC ────────────────────────────────────────────────
  return {
    init,
    isReady,
    isInTelegram,
    getUser,
    getUserId,
    getFirstName,
    getUsername,
    getInitData,
    getAuth,
    getStartParam,
    haptic, hapticSuccess, hapticError, hapticWarning,
    hapticLight, hapticMedium, hapticHeavy,
    close, openLink, openTelegramLink,
    showBack, hideBack,
    showMainBtn, hideMainBtn, mainBtnLoading,
    copyText
  };

})();

// Init immédiat dès le chargement
document.addEventListener('DOMContentLoaded', () => TG.init());
