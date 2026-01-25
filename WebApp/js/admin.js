/**
 * LOGIQUE PAGE ADMIN
 * ===================
 * Authentification, dashboard, configuration
 */

const tg = window.Telegram?.WebApp;

// État
let isAuthenticated = false;
let statsInterval = null;

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
  if (tg) {
    tg.expand();
    tg.ready();
    tg.BackButton.show();
    tg.BackButton.onClick(() => {
      if (isAuthenticated) {
        logout();
      } else {
        window.location.href = 'index.html';
      }
    });
  }
  
  // Focus sur input password
  document.getElementById('passwordInput')?.focus();
});

/**
 * AUTHENTIFICATION
 * Gérer la soumission du formulaire de login
 */
async function handleLogin(event) {
  event.preventDefault();
  
  const password = document.getElementById('passwordInput').value;
  const errorMsg = document.getElementById('loginError');
  
  if (!password) {
    errorMsg.classList.remove('hidden');
    return;
  }
  
  // Appel API
  const result = await API.adminLogin(password);
  
  if (result.success) {
    // Succès - afficher dashboard
    isAuthenticated = true;
    errorMsg.classList.add('hidden');
    
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('dashboardScreen').classList.add('active');
    document.getElementById('bottomNav').style.display = 'flex';
    
    if (tg?.HapticFeedback) {
      tg.HapticFeedback.notificationOccurred('success');
    }
    
    // Charger les données
    await loadDashboard();
    
    // Rafraîchir les stats toutes les 30 secondes
    statsInterval = setInterval(loadStats, 30000);
    
  } else {
    // Échec - afficher erreur
    errorMsg.classList.remove('hidden');
    document.getElementById('passwordInput').value = '';
    document.getElementById('passwordInput').focus();
    
    if (tg?.HapticFeedback) {
      tg.HapticFeedback.notificationOccurred('error');
    }
  }
}

/**
 * CHARGER DASHBOARD
 * Charger les statistiques et la configuration
 */
async function loadDashboard() {
  await loadStats();
  await loadConfig();
}

/**
 * CHARGER STATISTIQUES
 */
async function loadStats() {
  const stats = await API.getAdminStats();
  
  if (stats.success !== false) {
    // Animer les compteurs
    animateValue('totalUsers', 0, stats.total_users || 0, 1000);
    animateValue('activeSessions', 0, stats.active_sessions || 0, 1000);
    animateValue('adsWatched', 0, stats.ads_watched || 0, 1000);
    animateValue('premiumUsers', 0, stats.premium_users || 0, 1000);
  }
}

/**
 * CHARGER CONFIGURATION
 */
async function loadConfig() {
  // Normalement récupéré du backend
  // Pour l'instant valeurs par défaut
  document.getElementById('freeDuration').value = 10;
  document.getElementById('monthlyDuration').value = 30;
  document.getElementById('yearlyDuration').value = 365;
}

/**
 * SAUVEGARDER CONFIGURATION
 */
async function saveConfig() {
  const config = {
    free_duration: parseInt(document.getElementById('freeDuration').value),
    monthly_duration: parseInt(document.getElementById('monthlyDuration').value),
    yearly_duration: parseInt(document.getElementById('yearlyDuration').value)
  };
  
  // Validation
  if (config.free_duration < 1 || config.free_duration > 60) {
    if (tg) {
      tg.showAlert('La durée gratuite doit être entre 1 et 60 minutes');
    }
    return;
  }
  
  if (config.monthly_duration < 1 || config.monthly_duration > 365) {
    if (tg) {
      tg.showAlert('La durée mensuelle doit être entre 1 et 365 jours');
    }
    return;
  }
  
  if (config.yearly_duration < 1 || config.yearly_duration > 730) {
    if (tg) {
      tg.showAlert('La durée annuelle doit être entre 1 et 730 jours');
    }
    return;
  }
  
  // Envoyer au backend
  const result = await API.updateConfig(config);
  
  if (result.success) {
    if (tg) {
      tg.showAlert('✅ Configuration sauvegardée avec succès');
      tg.HapticFeedback?.notificationOccurred('success');
    }
  } else {
    if (tg) {
      tg.showAlert('❌ Erreur lors de la sauvegarde');
      tg.HapticFeedback?.notificationOccurred('error');
    }
  }
}

/**
 * DÉCONNEXION
 */
function logout() {
  // Confirmer
  if (tg) {
    tg.showConfirm('Êtes-vous sûr de vouloir vous déconnecter ?', (confirmed) => {
      if (confirmed) {
        performLogout();
      }
    });
  } else {
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
      performLogout();
    }
  }
}

/**
 * EXÉCUTER DÉCONNEXION
 */
function performLogout() {
  isAuthenticated = false;
  window.adminToken = null;
  
  // Arrêter le rafraîchissement des stats
  if (statsInterval) {
    clearInterval(statsInterval);
    statsInterval = null;
  }
  
  // Retour à l'écran login
  document.getElementById('dashboardScreen').classList.remove('active');
  document.getElementById('loginScreen').style.display = 'flex';
  document.getElementById('bottomNav').style.display = 'none';
  
  // Reset formulaire
  document.getElementById('passwordInput').value = '';
  document.getElementById('loginError').classList.add('hidden');
  
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('medium');
  }
}

/**
 * ANIMER COMPTEUR
 * Animation progressive d'un nombre
 */
function animateValue(elementId, start, end, duration) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  const range = end - start;
  const increment = range / (duration / 16); // 60 FPS
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    
    if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
      current = end;
      clearInterval(timer);
    }
    
    element.textContent = Math.floor(current).toLocaleString('fr-FR');
  }, 16);
}

/**
 * FORMATER NOMBRE
 */
function formatNumber(num) {
  return new Intl.NumberFormat('fr-FR').format(num);
}

/**
 * FORMATER DATE
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}