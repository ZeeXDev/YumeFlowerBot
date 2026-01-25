/**
 * MONETAG SDK WRAPPER
 * =====================
 * Classe pour gérer les publicités interstitielles Monetag
 * 
 * Fonctionnement :
 * 1. Le SDK Monetag charge une fonction globale show_XXXXX() où XXXXX est l'ID de l'unité pub
 * 2. Cette classe détecte automatiquement quand le SDK est prêt
 * 3. showAd() retourne une Promise qui resolve si la pub est visionnée, reject sinon
 * 
 * Usage :
 * const monetag = new MonetagAds('8699778');
 * await monetag.showAd(); // Lance la pub plein écran
 */

class MonetagAds {
  /**
   * @param {string} adId - ID de l'unité publicitaire Monetag (ex: '8699778')
   */
  constructor(adId = '8699778') {
    this.adId = adId;
    this.sdkLoaded = false;
    this.checkSDKInterval = null;
    this.functionName = `show_${this.adId}`;
    
    console.log(`[Monetag] Initialisation avec ID: ${this.adId}`);
    
    // Ne pas démarrer la vérification automatiquement
    // On attend l'appel explicite à checkSDK()
  }

  /**
   * Vérifie si le SDK Monetag est chargé et prêt
   * @returns {Promise<boolean>} - Résout quand le SDK est prêt ou après timeout
   */
  checkSDK() {
    return new Promise((resolve, reject) => {
      // Si déjà chargé, résoudre immédiatement
      if (this.sdkLoaded) {
        resolve(true);
        return;
      }

      // Vérifier si la fonction existe déjà
      if (typeof window[this.functionName] === 'function') {
        this.sdkLoaded = true;
        console.log('[Monetag] SDK déjà prêt');
        resolve(true);
        return;
      }

      console.log('[Monetag] Attente du SDK...');
      let attempts = 0;
      const maxAttempts = 50; // 5 secondes max (50 * 100ms)

      // Vérifier toutes les 100ms
      this.checkSDKInterval = setInterval(() => {
        attempts++;

        if (typeof window[this.functionName] === 'function') {
          this.sdkLoaded = true;
          clearInterval(this.checkSDKInterval);
          console.log('[Monetag] SDK chargé avec succès');
          resolve(true);
        } else if (attempts >= maxAttempts) {
          // Timeout après 5 secondes
          clearInterval(this.checkSDKInterval);
          console.warn('[Monetag] Timeout - SDK non chargé, mode simulation activé');
          // On ne rejette pas, on résout en mode simulation
          resolve(false);
        }
      }, 100);
    });
  }

  /**
   * Affiche la publicité Monetag (interstitielle plein écran)
   * @returns {Promise<boolean>} - Résout si pub visionnée, rejette si fermée prématurément
   */
  async showAd() {
    console.log('[Monetag] Tentative d\'affichage de la publicité...');

    // Si SDK pas chargé, mode simulation pour développement
    if (!this.sdkLoaded) {
      console.warn('[Monetag] Mode simulation - Pub fictive de 2 secondes');
      return this.simulateAd();
    }

    // Appel réel au SDK Monetag
    return new Promise((resolve, reject) => {
      try {
        console.log(`[Monetag] Appel de ${this.functionName}()`);
        
        // La fonction Monetag retourne elle-même une Promise
        const adPromise = window[this.functionName]();

        if (adPromise && typeof adPromise.then === 'function') {
          adPromise
            .then(() => {
              console.log('[Monetag] Publicité complétée avec succès');
              resolve(true);
            })
            .catch((error) => {
              console.error('[Monetag] Publicité fermée ou erreur:', error);
              reject(false);
            });
        } else {
          // Si la fonction ne retourne pas une Promise (cas rare)
          console.warn('[Monetag] Fonction appelée mais pas de Promise retournée');
          // On suppose que ça a marché
          setTimeout(() => resolve(true), 1000);
        }
      } catch (error) {
        console.error('[Monetag] Erreur lors de l\'appel:', error);
        reject(false);
      }
    });
  }

  /**
   * Simule une publicité en mode développement (quand SDK pas disponible)
   * @returns {Promise<boolean>}
   */
  simulateAd() {
    return new Promise((resolve) => {
      console.log('[Monetag] SIMULATION - Début publicité fictive');
      
      // Simuler un délai de 2 secondes
      setTimeout(() => {
        console.log('[Monetag] SIMULATION - Publicité terminée');
        resolve(true);
      }, 2000);
    });
  }

  /**
   * Nettoie les intervalles en cours
   */
  cleanup() {
    if (this.checkSDKInterval) {
      clearInterval(this.checkSDKInterval);
      this.checkSDKInterval = null;
    }
  }
}

// Instance globale avec l'ID par défaut
// IMPORTANT : Remplacer '8699778' par votre vrai ID Monetag
const monetag = new MonetagAds('8699778');

// Nettoyage à la fermeture de la page
window.addEventListener('beforeunload', () => {
  monetag.cleanup();
});