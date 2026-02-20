/* ============================================================
   TIMER.JS — Countdown, Progress Ring, Session Timer
   YumeFlower WebApp
   ============================================================ */

const Timer = (() => {

  let _interval = null;
  let _totalSeconds = 0;
  let _remainingSeconds = 0;
  let _onTick = null;
  let _onEnd = null;

  // Circonférence du cercle SVG (r=47 → 2πr ≈ 295.31 pour 110px viewBox)
  const CIRCUMFERENCE = 2 * Math.PI * 47;

  // ── START ─────────────────────────────────────────────────
  /**
   * Lance le timer
   * @param {number} seconds - Durée totale en secondes
   * @param {Function} onTick - Appelé à chaque seconde avec { remaining, total, pct }
   * @param {Function} onEnd  - Appelé quand le timer arrive à 0
   */
  function start(seconds, onTick = null, onEnd = null) {
    stop(); // Reset si déjà en cours

    _totalSeconds     = seconds;
    _remainingSeconds = seconds;
    _onTick           = onTick;
    _onEnd            = onEnd;

    // Premier tick immédiat
    _tick();

    _interval = setInterval(() => {
      _remainingSeconds--;

      if (_remainingSeconds <= 0) {
        _remainingSeconds = 0;
        _tick();
        stop();
        if (_onEnd) _onEnd();
        return;
      }

      _tick();
    }, 1000);
  }

  function _tick() {
    const pct = _totalSeconds > 0 ? _remainingSeconds / _totalSeconds : 0;
    if (_onTick) _onTick({
      remaining: _remainingSeconds,
      total: _totalSeconds,
      pct
    });
  }

  // ── STOP ──────────────────────────────────────────────────
  function stop() {
    if (_interval) {
      clearInterval(_interval);
      _interval = null;
    }
  }

  // ── FORMAT ────────────────────────────────────────────────
  /**
   * Formate les secondes en mm:ss
   */
  function format(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  /**
   * Formate les secondes en texte lisible (1h 2m 3s)
   */
  function formatReadable(seconds) {
    if (seconds <= 0) return '0s';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    let out = '';
    if (h > 0) out += `${h}h `;
    if (m > 0) out += `${m}m `;
    if (s > 0 || out === '') out += `${s}s`;
    return out.trim();
  }

  // ── RING SVG ──────────────────────────────────────────────
  /**
   * Met à jour l'anneau SVG en fonction du pourcentage
   * @param {SVGCircleElement} circleEl - L'élément <circle> de progression
   * @param {number} pct - 0 à 1 (1 = plein, 0 = vide)
   */
  function updateRing(circleEl, pct) {
    if (!circleEl) return;
    const offset = CIRCUMFERENCE * (1 - pct);
    circleEl.style.strokeDasharray  = CIRCUMFERENCE;
    circleEl.style.strokeDashoffset = offset;
  }

  /**
   * Crée le gradient SVG pour l'anneau
   * À injecter dans le <defs> du SVG
   */
  function getRingGradientDefs(id = 'timerGrad') {
    return `<defs>
      <linearGradient id="${id}" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#FF1A1A"/>
        <stop offset="100%" stop-color="#1E90FF"/>
      </linearGradient>
    </defs>`;
  }

  // ── PROGRESS BAR ─────────────────────────────────────────
  /**
   * Met à jour une barre de progression simple
   * @param {HTMLElement} fillEl - L'élément .progress-fill
   * @param {number} pct - 0 à 1
   */
  function updateBar(fillEl, pct) {
    if (!fillEl) return;
    fillEl.style.width = `${Math.max(0, Math.min(100, pct * 100))}%`;
  }

  // ── RING CONTROLLER ───────────────────────────────────────
  /**
   * Helper complet : démarre un timer et met à jour automatiquement
   * l'anneau + la barre + le texte
   *
   * @param {object} opts
   *   seconds   {number}          - Durée totale
   *   circle    {SVGCircleElement} - Cercle SVG de progression
   *   bar       {HTMLElement}      - Barre de progression (optionnel)
   *   display   {HTMLElement}      - Élément texte mm:ss (optionnel)
   *   pctEl     {HTMLElement}      - Élément texte % (optionnel)
   *   onEnd     {Function}         - Callback fin
   */
  function startWithRing({ seconds, circle, bar, display, pctEl, onEnd }) {
    start(
      seconds,
      ({ remaining, pct }) => {
        if (circle)  updateRing(circle, pct);
        if (bar)     updateBar(bar, pct);
        if (display) display.textContent = format(remaining);
        if (pctEl)   pctEl.textContent = `${Math.round(pct * 100)}%`;
      },
      () => {
        if (circle)  updateRing(circle, 0);
        if (bar)     updateBar(bar, 0);
        if (display) display.textContent = '00:00';
        if (pctEl)   pctEl.textContent = '0%';
        if (onEnd)   onEnd();
      }
    );
  }

  // ── TIME LEFT FROM EXPIRES_AT ─────────────────────────────
  /**
   * Calcule les secondes restantes à partir d'une date ISO expires_at
   * @param {string} expiresAt - ISO string
   * @returns {number} secondes restantes (min 0)
   */
  function secondsFromExpiry(expiresAt) {
    if (!expiresAt) return 0;
    const exp = new Date(expiresAt).getTime();
    const now = Date.now();
    return Math.max(0, Math.floor((exp - now) / 1000));
  }

  // ── PUBLIC ────────────────────────────────────────────────
  return {
    start,
    stop,
    format,
    formatReadable,
    updateRing,
    updateBar,
    startWithRing,
    secondsFromExpiry,
    getRingGradientDefs,
    CIRCUMFERENCE
  };

})();
