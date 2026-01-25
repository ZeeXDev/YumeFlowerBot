/**
 * APPLICATION PRINCIPALE
 * =======================
 * Logique métier complète de la Mini App Telegram
 * Gère le cycle de vie : vérification session → visionnage pub → timer countdown
 */

// Initialisation Telegram WebApp
const tg = window.Telegram?.WebApp;

// État global de l'application
let currentUser = null;
let sessionData = null;
let countdownInterval = null;

// Configuration
const CONFIG = {
  BOT_USERNAME: 'TonBotUsername', // À REMPLACER par le vrai username du bot
  SESSION_CHECK_INTERVAL: 30000, // Vérifier session toutes les 30s
  TIMER_UPDATE_INTERVAL: 1000 // Mettre à jour timer chaque seconde
};

/**
 * INITIALISATION
 * Point d'entrée principal au chargement de la page
 */
document.addEventListener('DOMContentLoaded', async () => {
  console.log('[App] Démarrage de l\'application...');
  
  // Vérifier si Telegram WebApp est disponible
  if (!tg) {
    showError('Cette application doit être ouverte via Telegram');
    return;
  }

  // Initialiser Telegram WebApp
  tg.expand();
  tg.ready();
  
  // Activer le bouton retour
  tg.BackButton.onClick(() => {
    if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
      window.location.href = 'index.html';
    } else {
      tg.close();
    }
  });

  // Récupérer les données utilisateur
  if (!tg.initDataUnsafe?.user) {
    showError('Impossible de récupérer vos informations utilisateur');
    return;
  }
  
  currentUser = tg.initDataUnsafe.user;
  console.log('[App] Utilisateur:', currentUser.id, currentUser.first_name);
  
  // Vérifier la session existante
  await checkSession();
  
  // Vérifier périodiquement la session
  setInterval(checkSession, CONFIG.SESSION_CHECK_INTERVAL);
});

/**
 * VÉRIFICATION SESSION
 * Vérifie si l'utilisateur a déjà un accès actif
 */
async function checkSession() {
  console.log('[App] Vérification de la session...');
  
  const data = await API.checkSession(currentUser.id, tg.initData);
  
  if (data.has_access) {
    console.log('[App] Session active détectée');
    sessionData = data;
    showActiveSession(data);
  } else {
    console.log('[App] Aucune session active');
    showMonetagSection();
  }
}

/**
 * AFFICHER SECTION MONETAG
 * Affiche l'interface pour regarder la pub
 */
function showMonetagSection() {
  const monetagSection = document.getElementById('monetagSection');
  const successSection = document.getElementById('successSection');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const accessType = document.getElementById('accessType');
  const expireTime = document.getElementById('expireTime');
  
  // Afficher section pub
  if (monetagSection) monetagSection.classList.remove('hidden');
  if (successSection) successSection.classList.add('hidden');
  
  // Mettre à jour status
  if (statusDot) statusDot.classList.remove('active');
  if (statusText) statusText.textContent = 'Aucun accès';
  if (accessType) accessType.textContent = 'Non connecté';
  if (expireTime) expireTime.textContent = '-';
  
  // Cacher timer et progress bar
  const timerDisplay = document.getElementById('timerDisplay');
  const progressBar = document.getElementById('progressBar');
  if (timerDisplay) timerDisplay.classList.add('hidden');
  if (progressBar) progressBar.classList.add('hidden');
  
  // Arrêter countdown si actif
  if (countdownInterval) {
    clearInterval(countdownInterval);
    countdownInterval = null;
  }
}

/**
 * AFFICHER SESSION ACTIVE
 * Affiche l'état quand l'utilisateur a déjà un accès
 */
function showActiveSession(data) {
  const monetagSection = document.getElementById('monetagSection');
  const successSection = document.getElementById('successSection');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const accessType = document.getElementById('accessType');
  const expireTime = document.getElementById('expireTime');
  
  // Cacher section pub, afficher succès
  if (monetagSection) monetagSection.classList.add('hidden');
  if (successSection) successSection.classList.remove('hidden');
  
  // Mettre à jour status
  if (statusDot) statusDot.classList.add('active');
  if (statusText) statusText.textContent = 'Session active';
  
  // Type d'accès
  const type = data.type === 'premium' ? 'Premium' : 'Gratuit (Pub)';
  if (accessType) accessType.textContent = type;
  
  // Calculer temps restant
  const remaining = API.getRemainingMinutes(data.expires_at);
  if (expireTime) expireTime.textContent = `${remaining} min`;
  
  // Démarrer le countdown
  const remainingSeconds = API.getRemainingSeconds(data.expires_at);
  startCountdown(remainingSeconds);
}

/**
 * GESTION CLIC BOUTON MONETAG
 * Déclenche le visionnage de la pub Monetag
 */
async function handleWatchAd() {
  console.log('[App] Démarrage processus pub Monetag...');
  
  const btn = document.getElementById('watchAdBtn');
  const loader = document.getElementById('loader');
  const errorMsg = document.getElementById('errorMsg');
  
  // UI Loading
  if (btn) btn.classList.add('hidden');
  if (loader) loader.classList.remove('hidden');
  if (errorMsg) errorMsg.classList.add('hidden');
  
  // Haptic feedback
  if (tg.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('light');
  }
  
  try {
    // Étape 1 : Vérifier que le SDK Monetag est prêt
    console.log('[App] Vérification SDK Monetag...');
    await monetag.checkSDK();
    
    // Étape 2 : Afficher la publicité (plein écran)
    console.log('[App] Affichage de la publicité...');
    await monetag.showAd();
    
    // Étape 3 : Publicité visionnée avec succès, créer la session
    console.log('[App] Publicité terminée, création de la session...');
    const result = await API.watchAd(currentUser.id, tg.initData);
    
    if (result.success) {
      // Succès !
      console.log('[App] Session créée avec succès');
      showSuccess(result.duration || 10);
      
      // Haptic feedback succès
      if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
      }
      
      // Alert Telegram
      tg.showAlert(`✅ Accès débloqué pour ${result.duration || 10} minutes !`);
    } else {
      throw new Error('Échec création session');
    }
    
  } catch (error) {
    // Échec : pub fermée avant la fin ou erreur technique
    console.error('[App] Erreur visionnage pub:', error);
    
    // Restaurer UI
    if (btn) btn.classList.remove('hidden');
    if (loader) loader.classList.add('hidden');
    if (errorMsg) errorMsg.classList.remove('hidden');
    
    // Haptic feedback erreur
    if (tg.HapticFeedback) {
      tg.HapticFeedback.notificationOccurred('error');
    }
  }
}

/**
 * AFFICHER SUCCÈS
 * Affiche l'interface après visionnage réussi de la pub
 */
function showSuccess(minutes) {
  const monetagSection = document.getElementById('monetagSection');
  const successSection = document.getElementById('successSection');
  const durationText = document.getElementById('durationText');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const accessType = document.getElementById('accessType');
  const expireTime = document.getElementById('expireTime');
  
  // Basculer les sections
  if (monetagSection) monetagSection.classList.add('hidden');
  if (successSection) successSection.classList.remove('hidden');
  if (durationText) durationText.textContent = `${minutes} minutes`;
  
  // Mettre à jour status card
  if (statusDot) statusDot.classList.add('active');
  if (statusText) statusText.textContent = 'Session active';
  if (accessType) accessType.textContent = 'Gratuit (Pub)';
  if (expireTime) expireTime.textContent = `${minutes} min`;
  
  // Démarrer countdown visuel
  startCountdown(minutes * 60);
}

/**
 * COUNTDOWN TIMER
 * Démarre un compte à rebours visuel de la session
 */
function startCountdown(totalSeconds) {
  const timerDisplay = document.getElementById('timerDisplay');
  const timerValue = document.getElementById('timerValue');
  const progressBar = document.getElementById('progressBar');
  const progressFill = document.getElementById('progressFill');
  
  // Afficher les éléments
  if (timerDisplay) timerDisplay.classList.remove('hidden');
  if (progressBar) progressBar.classList.remove('hidden');
  
  let remaining = totalSeconds;
  const total = totalSeconds;
  
  // Arrêter l'ancien interval si existant
  if (countdownInterval) {
    clearInterval(countdownInterval);
  }
  
  // Fonction de mise à jour
  const updateTimer = () => {
    if (remaining <= 0) {
      clearInterval(countdownInterval);
      countdownInterval = null;
      
      // Session expirée, recharger la page
      tg.showAlert('⏱️ Votre session a expiré. Regardez une nouvelle pub pour continuer.');
      setTimeout(() => location.reload(), 2000);
      return;
    }
    
    // Calculer minutes et secondes
    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;
    
    // Afficher le temps
    if (timerValue) {
      timerValue.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Mettre à jour la barre de progression
    if (progressFill) {
      const percent = (remaining / total) * 100;
      progressFill.style.width = `${percent}%`;
      
      // Changer couleur si < 1 minute
      if (remaining < 60) {
        progressFill.style.backgroundColor = 'var(--accent-red)';
      }
    }
    
    remaining--;
  };
  
  // Première mise à jour immédiate
  updateTimer();
  
  // Puis toutes les secondes
  countdownInterval = setInterval(updateTimer, CONFIG.TIMER_UPDATE_INTERVAL);
}

/**
 * NAVIGATION - Ouvrir le bot Telegram
 */
function openBot() {
  console.log('[App] Ouverture du bot...');
  
  if (tg.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('medium');
  }
  
  tg.openTelegramLink(`https://t.me/${CONFIG.BOT_USERNAME}`);
  
  // Fermer la WebApp après 500ms
  setTimeout(() => tg.close(), 500);
}

/**
 * NAVIGATION - Aller vers Premium
 */
function goPremium() {
  console.log('[App] Navigation vers Premium...');
  
  if (tg.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('light');
  }
  
  window.location.href = 'prime.html';
}

/**
 * AFFICHER ERREUR
 * Affiche un message d'erreur global
 */
function showError(message) {
  console.error('[App] Erreur:', message);
  
  // Utiliser l'alert Telegram si disponible
  if (tg && tg.showAlert) {
    tg.showAlert(`❌ ${message}`);
  } else {
    alert(message);
  }
}