/**
 * MONETAG SDK WRAPPER
 * =====================
 * Gestion des publicités interstitielles Monetag
 */

class MonetagAds {
  constructor(adId = '10518701') {
    this.adId = adId;
    this.sdkLoaded = false;
    this.checkSDKInterval = null;
    this.functionName = `show_${this.adId}`;
    
    console.log(`[Monetag] Initialisation avec ID: ${this.adId}`);
  }

  /**
   * Vérifie si le SDK Monetag est chargé
   */
  checkSDK() {
    return new Promise((resolve) => {
      if (this.sdkLoaded) {
        resolve(true);
        return;
      }

      if (typeof window[this.functionName] === 'function') {
        this.sdkLoaded = true;
        console.log('[Monetag] SDK prêt');
        resolve(true);
        return;
      }

      console.log('[Monetag] Attente du SDK...');
      let attempts = 0;
      const maxAttempts = 50;

      this.checkSDKInterval = setInterval(() => {
        attempts++;

        if (typeof window[this.functionName] === 'function') {
          this.sdkLoaded = true;
          clearInterval(this.checkSDKInterval);
          console.log('[Monetag] SDK chargé');
          resolve(true);
        } else if (attempts >= maxAttempts) {
          clearInterval(this.checkSDKInterval);
          console.warn('[Monetag] Timeout - Mode simulation');
          resolve(false);
        }
      }, 100);
    });
  }

  /**
   * Affiche la publicité
   */
  async showAd() {
    console.log('[Monetag] Lancement publicité...');

    if (!this.sdkLoaded) {
      console.warn('[Monetag] Mode simulation');
      return this.simulateAd();
    }

    return new Promise((resolve, reject) => {
      try {
        console.log(`[Monetag] Appel ${this.functionName}()`);
        const result = window[this.functionName]();

        if (result && typeof result.then === 'function') {
          result
            .then(() => {
              console.log('[Monetag] Pub terminée avec succès');
              resolve(true);
            })
            .catch(() => {
              console.error('[Monetag] Pub fermée/erreur');
              reject(false);
            });
        } else {
          setTimeout(() => resolve(true), 1000);
        }
      } catch (error) {
        console.error('[Monetag] Erreur:', error);
        reject(false);
      }
    });
  }

  /**
   * Mode simulation (développement)
   */
  simulateAd() {
    return new Promise((resolve) => {
      console.log('[Monetag] SIMULATION - Pub fictive 2s');
      setTimeout(() => {
        console.log('[Monetag] SIMULATION - Terminée');
        resolve(true);
      }, 2000);
    });
  }

  cleanup() {
    if (this.checkSDKInterval) {
      clearInterval(this.checkSDKInterval);
    }
  }
}

// Instance globale avec TON ID Monetag
const monetag = new MonetagAds('10518701');

window.addEventListener('beforeunload', () => {
  monetag.cleanup();
});
