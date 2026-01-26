/**
 * LOGIQUE PAGE PREMIUM
 * =====================
 * Gestion des devises, plans, méthodes de paiement
 */

const tg = window.Telegram?.WebApp;

// État
let currentCurrency = 'XOF';
let selectedPlan = null;
let selectedPayment = null;
let currentUser = null;

// Prix par devise (weekly, monthly, yearly)
const PRICES = {
  XOF: { weekly: 1100, monthly: 3500, yearly: 50000 },
  CDF: { weekly: 4000, monthly: 14000, yearly: 190000 },
  EUR: { weekly: 1, monthly: 3, yearly: 80 },
  USD: { weekly: 1, monthly: 4, yearly: 90 },
  CRYPTO: { weekly: 1, monthly: 4, yearly: 90 }
};

// Informations spécifiques par opérateur
const OPERATOR_INFO = {
  moov: {
    name: 'Moov Money',
    ussd: '*155#',
    countries: 'Togo, Burkina Faso, Bénin, Côte d\'Ivoire, Niger, Mali',
    phone: '+228 98 64 27 27',
    instructions: 'Transfert via Moov Money'
  },
  orange: {
    name: 'Orange Money',
    ussd: '#144#',
    countries: 'Togo, Burkina Faso, Niger, Mali, Côte d\'Ivoire, Sénégal, etc.',
    phone: '+226 06 92 16 14',
    instructions: 'Transfert via Orange Money'
  },
  mtn: {
    name: 'MTN Mobile Money',
    ussd: '*165#',
    countries: 'Togo, Benin, Ghana, Nigeria, Afrique du Sud, etc.',
    phone: 'Non Disponible pour le moment',
    instructions: 'Transfert via MTN Mobile Money'
  },
  mixx: {
    name: 'Mixx by Yas',
    ussd: '*200#',
    countries: 'Togo uniquement',
    phone: '+228 90 44 40 90', // Remplace par ton numéro Mixx
    instructions: 'Transfert via Mixx by Yas'
  }
};

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
  if (tg) {
    tg.expand();
    tg.ready();
    tg.BackButton.show();
    tg.BackButton.onClick(() => {
      window.location.href = 'index.html';
    });
    
    currentUser = tg.initDataUnsafe?.user;
  }
  
  updatePrices();
});

/**
 * Sélectionner une devise
 */
function selectCurrency(currency, btn) {
  currentCurrency = currency;
  
  // Mettre à jour UI boutons
  document.querySelectorAll('.currency-btn').forEach(b => {
    b.classList.remove('active');
  });
  btn.classList.add('active');
  
  // Mettre à jour les prix
  updatePrices();
  
  // Haptic
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('light');
  }
}

/**
 * Mettre à jour l'affichage des prix
 */
function updatePrices() {
  const prices = PRICES[currentCurrency];
  
  // Vérifier si les éléments existent avant de les mettre à jour
  const monthlyPrice = document.getElementById('price-monthly');
  const yearlyPrice = document.getElementById('price-yearly');
  const monthlyCurrency = document.getElementById('currency-monthly');
  const yearlyCurrency = document.getElementById('currency-yearly');
  
  if (monthlyPrice) monthlyPrice.textContent = prices.monthly;
  if (yearlyPrice) yearlyPrice.textContent = prices.yearly;
  
  const symbol = getCurrencySymbol(currentCurrency);
  if (monthlyCurrency) monthlyCurrency.textContent = symbol;
  if (yearlyCurrency) yearlyCurrency.textContent = symbol;
  
  // Mettre à jour le weekly si l'élément existe
  const weeklyPrice = document.getElementById('price-weekly');
  const weeklyCurrency = document.getElementById('currency-weekly');
  if (weeklyPrice) weeklyPrice.textContent = prices.weekly;
  if (weeklyCurrency) weeklyCurrency.textContent = symbol;
}

/**
 * Obtenir le symbole de la devise
 */
function getCurrencySymbol(currency) {
  const symbols = {
    XOF: 'XOF (CFA)',
    CDF: 'CDF (Franc)',
    EUR: 'EUR (€)',
    USD: 'USD ($)',
    CRYPTO: 'USD'
  };
  return symbols[currency] || currency;
}

/**
 * Sélectionner un plan
 */
function selectPlan(plan) {
  selectedPlan = plan;
  
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('medium');
  }
  
  // Scroller vers les méthodes de paiement
  const paymentSection = document.querySelector('.payment-methods');
  if (paymentSection) {
    paymentSection.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'start' 
    });
  }
  
  // Si une méthode est déjà sélectionnée, activer le bouton
  if (selectedPayment) {
    const payBtn = document.getElementById('payBtn');
    if (payBtn) payBtn.disabled = false;
  }
}

/**
 * Sélectionner une méthode de paiement
 */
function selectPayment(method, element) {
  selectedPayment = method;
  
  // Mettre à jour UI
  document.querySelectorAll('.payment-method').forEach(el => {
    el.classList.remove('selected');
  });
  element.classList.add('selected');
  
  // Activer le bouton si un plan est sélectionné
  if (selectedPlan) {
    const payBtn = document.getElementById('payBtn');
    if (payBtn) payBtn.disabled = false;
  }
  
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('light');
  }
}

/**
 * Procéder au paiement
 */
function proceedPayment() {
  if (!selectedPlan || !selectedPayment) {
    if (tg) {
      tg.showAlert('Veuillez sélectionner un plan et une méthode de paiement');
    } else {
      alert('Veuillez sélectionner un plan et une méthode de paiement');
    }
    return;
  }
  
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.notificationOccurred('success');
  }
  
  // Afficher les instructions
  showPaymentInstructions();
}

/**
 * Afficher les instructions de paiement
 */
function showPaymentInstructions() {
  const modal = document.getElementById('paymentModal');
  const title = document.getElementById('modalTitle');
  const content = document.getElementById('modalContent');
  
  if (!modal || !title || !content) {
    console.error('Modal elements not found');
    return;
  }
  
  // Déterminer le montant selon le plan
  let amount, duration;
  
  if (selectedPlan === 'weekly') {
    amount = PRICES[currentCurrency].weekly;
    duration = '7 jours';
  } else if (selectedPlan === 'monthly') {
    amount = PRICES[currentCurrency].monthly;
    duration = '30 jours';
  } else if (selectedPlan === 'yearly') {
    amount = PRICES[currentCurrency].yearly;
    duration = '1 an';
  }
  
  // Titre
  title.textContent = `Paiement ${getPaymentName(selectedPayment)}`;
  
  // Contenu selon la méthode
  content.innerHTML = generateInstructions(selectedPayment, amount, duration);
  
  // Afficher modal
  modal.classList.add('active');
}

/**
 * Fermer le modal
 */
function closeModal() {
  const modal = document.getElementById('paymentModal');
  if (modal) {
    modal.classList.remove('active');
  }
}

/**
 * Nom de la méthode de paiement
 */
function getPaymentName(method) {
  const names = {
    moov: 'Moov Money',
    orange: 'Orange Money',
    mtn: 'MTN Mobile Money',
    mixx: 'Mixx by Yas',
    ecobank: 'Carte Ecobank',
    usdt: 'USDT (Crypto)',
    ton: 'Toncoin (TON)'
  };
  return names[method] || method;
}

/**
 * Générer les instructions HTML
 */
function generateInstructions(method, amount, duration) {
  const currency = getCurrencySymbol(currentCurrency);
  
  // Instructions communes (résumé de la commande)
  const commonSteps = `
    <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-lg); border: 1px solid var(--border);">
      <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-sm);">
        <span style="color: var(--text-secondary);">Formule :</span>
        <strong style="color: var(--text-primary);">${duration}</strong>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-sm);">
        <span style="color: var(--text-secondary);">Montant :</span>
        <strong style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 1.5rem;">${amount} ${currency}</strong>
      </div>
      <div style="display: flex; justify-content: space-between;">
        <span style="color: var(--text-secondary);">Votre ID Telegram :</span>
        <strong style="color: var(--primary); font-family: monospace;">${currentUser?.id || 'N/A'}</strong>
      </div>
    </div>
  `;
  
  // Instructions spécifiques par méthode
  let specificInstructions = '';
  
  switch(method) {
    case 'moov':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Numéro Moov Money :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; font-size: 1.1rem; color: var(--primary); border: 1px solid var(--border); text-align: center; font-weight: bold;">
            +228 98 64 27 27
          </div>
          <div style="margin-top: var(--space-sm); font-size: 0.8rem; color: var(--text-tertiary); text-align: center;">
            Pays acceptés : Togo, Burkina Faso, Bénin, Côte d'Ivoire, Niger, Mali
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Composez le <strong>${OPERATOR_INFO.moov.ussd}</strong> sur votre téléphone</li>
          <li class="instruction-item">Sélectionnez <strong>"Transfert d'argent"</strong> ou <strong>"Envoyer de l'argent"</strong></li>
          <li class="instruction-item">Choisissez <strong>"Vers un autre pays"</strong> si vous êtes hors du Togo</li>
          <li class="instruction-item">Saisissez le numéro : <strong>+228 98 64 27 27</strong></li>
          <li class="instruction-item">Entrez le montant : <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Validez avec votre code secret Moov</li>
          <li class="instruction-item"><strong>Important :</strong> Envoyez la capture d'écran de la confirmation de paiement à l'admin avec votre ID : <strong>${currentUser?.id}</strong></li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Envoyer la preuve de paiement
        </button>
      `;
      break;
      
    case 'orange':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Numéro Orange Money :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; font-size: 1.1rem; color: var(--primary); border: 1px solid var(--border); text-align: center; font-weight: bold;">
            +226 06 92 16 14
          </div>
          <div style="margin-top: var(--space-sm); font-size: 0.8rem; color: var(--text-tertiary); text-align: center;">
            Togo, Burkina Faso, Niger, Mali, Côte d\'Ivoire, Sénégal, etc.
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Composez <strong>${OPERATOR_INFO.orange.ussd}</strong> ou utilisez l'appli Orange Money</li>
          <li class="instruction-item">Sélectionnez <strong>"Transfert"</strong> puis <strong>"Transfert international"</strong> si nécessaire</li>
          <li class="instruction-item">Entrez le numéro destinataire : <strong>+226 06 92 16 14</strong></li>
          <li class="instruction-item">Saisissez le montant : <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Confirmez avec votre code PIN Orange</li>
          <li class="instruction-item">Conservez le SMS de confirmation ou faites une capture d'écran</li>
          <li class="instruction-item">Envoyez la preuve à l'admin avec votre ID Telegram : <strong>${currentUser?.id}</strong></li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Envoyer la preuve de paiement
        </button>
      `;
      break;
      
    case 'mtn':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Numéro MTN Mobile Money :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; font-size: 1.1rem; color: var(--primary); border: 1px solid var(--border); text-align: center; font-weight: bold;">
            Non Disponible pour le moment
          </div>
          <div style="margin-top: var(--space-sm); font-size: 0.8rem; color: var(--text-tertiary); text-align: center;">
            MTN Mobile Money (Togo, Ghana, Nigeria, etc.)
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Composez <strong>${OPERATOR_INFO.mtn.ussd}</strong> ou utilisez l'appli MTN MoMo</li>
          <li class="instruction-item">Choisissez <strong>"Envoyer de l'argent"</strong> ou <strong>"Transfert"</strong></li>
          <li class="instruction-item">Sélectionnez <strong>"Autre réseau"</strong> ou <strong>"International"</strong> si disponible</li>
          <li class="instruction-item">Entrez le numéro : <strong>Non Disponible pour le moment</strong></li>
          <li class="instruction-item">Tapez le montant : <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Validez avec votre code secret MTN</li>
          <li class="instruction-item">Prenez une capture de la confirmation et envoyez-la à l'admin avec votre ID : <strong>${currentUser?.id}</strong></li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Envoyer la preuve de paiement
        </button>
      `;
      break;
      
    case 'mixx':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Numéro Mixx by Yas :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; font-size: 1.1rem; color: var(--primary); border: 1px solid var(--border); text-align: center; font-weight: bold;">
            +228 90 44 40 90
          </div>
          <div style="margin-top: var(--space-sm); font-size: 0.8rem; color: var(--text-tertiary); text-align: center;">
            🇹🇬 Uniquement disponible au Togo
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Ouvrez l'application <strong>Mixx by Yas</strong> sur votre téléphone ou composer <strong>*145#</strong></li>
          <li class="instruction-item">Sélectionnez <strong>"Transfert d'argent"</strong> ou <strong>"Envoyer"</strong></li>
          <li class="instruction-item">Entrez le numéro destinataire : <strong>+228 90 44 40 90</strong></li>
          <li class="instruction-item">Saisissez le montant : <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Ajoutez la référence : <strong>PREMIUM-${currentUser?.id}</strong></li>
          <li class="instruction-item">Validez avec votre code PIN Mixx</li>
          <li class="instruction-item"><strong>Important :</strong> Envoyez la capture d'écran de la confirmation à l'admin avec votre ID : <strong>${currentUser?.id}</strong></li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Envoyer la preuve de paiement
        </button>
      `;
      break;
      
    case 'ecobank':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Compte Ecobank :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; word-break: break-all; font-size: 0.9rem; color: var(--primary); border: 1px solid var(--border);">
            N° Xpress : 141798420001<br>
            Numéro Xpress: 141798420001
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Connectez-vous à votre application Ecobank Mobile</li>
          <li class="instruction-item">Sélectionnez <strong>"Transfert"</strong> puis <strong>"Ajouter un bénéficiaire"</strong></li>
          <li class="instruction-item">Envoyer le motant à cet adresse Xpress Ecobank : <strong>141798420001</strong></li>
          <li class="instruction-item">Montant à transférer : <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Motif : <strong>PREMIUM-${currentUser?.id}</strong></li>
          <li class="instruction-item">Validez avec votre code de confirmation</li>
          <li class="instruction-item">Envoyez la capture d'écran du reçu à l'admin avec votre ID Telegram</li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Contacter le support
        </button>
      `;
      break;
      
    case 'usdt':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Adresse USDT (TRC20) :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; word-break: break-all; font-size: 0.85rem; color: var(--primary); border: 1px solid var(--border);">
            TDscYrWer2Fhv7VPjyT3qCXYqBx5D1ynKC
          </div>
          <div style="margin-top: var(--space-sm); font-size: 0.8rem; color: var(--success);">
            ⚠️ Envoyez uniquement sur le réseau TRC20 (Tron)
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Copiez l'adresse TRC20 ci-dessus</li>
          <li class="instruction-item">Envoyez exactement <strong>${amount} USDT</strong> (attention aux frais de réseau)</li>
          <li class="instruction-item">Attendez la confirmation sur la blockchain (1-3 minutes)</li>
          <li class="instruction-item">Copiez le <strong>hash de transaction</strong> (TxID)</li>
          <li class="instruction-item">Envoyez le TxID + votre ID Telegram (${currentUser?.id}) à l'admin</li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Envoyer le hash de transaction
        </button>
      `;
      break;
      
    case 'ton':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">Adresse TON :</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; word-break: break-all; font-size: 0.85rem; color: var(--primary); border: 1px solid var(--border);">
            UQBXWGv8ni_K5RdVt8pkBjdxAuq4hHSMWVocLs-JDYSbpuv6
          </div>
          <div style="margin-top: var(--space-sm); font-size: 0.8rem; color: var(--text-tertiary);">
            Réseau : The Open Network (TON)
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Ouvrez votre portefeuille (Tonkeeper, Wallet dans Telegram, etc.)</li>
          <li class="instruction-item">Envoyez <strong>${amount} TON</strong> à l'adresse ci-dessus</li>
          <li class="instruction-item">Attendez la confirmation (environ 30 secondes)</li>
          <li class="instruction-item">Votre accès sera activé automatiquement sous 5 minutes</li>
          <li class="instruction-item">En cas de problème, contactez @kingcey : ${currentUser?.id}</li>
        </ol>
        <button class="btn btn-success" style="width: 100%; margin-top: var(--space-md;" onclick="confirmTonPayment()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          J'ai effectué le paiement
        </button>
      `;
      break;
  }
  
  return commonSteps + specificInstructions;
}

/**
 * Contacter le support
 */
function contactSupport() {
  const planText = selectedPlan === 'weekly' ? '7 jours' : selectedPlan === 'monthly' ? '30 jours' : '1 an';
  const planKey = selectedPlan === 'weekly' ? 'weekly' : selectedPlan === 'monthly' ? 'monthly' : 'yearly';
  
  const message = `Bonjour, je souhaite activer mon compte Premium.\n\nMon ID Telegram : ${currentUser?.id}\nFormule : ${planText}\nMontant : ${PRICES[currentCurrency][planKey]} ${getCurrencySymbol(currentCurrency)}\nMéthode : ${getPaymentName(selectedPayment)}\n\nPreuve de paiement ci-joint.`;
  
  if (tg) {
    // IMPORTANT : Remplacer kingcey par le vrai username du bot support si différent
    tg.openTelegramLink(`https://t.me/kingcey?text=${encodeURIComponent(message)}`);
    closeModal();
  } else {
    console.log('Message support:', message);
  }
}

/**
 * Confirmer paiement TON
 */
async function confirmTonPayment() {
  if (!currentUser) {
    console.error('User not found');
    return;
  }
  
  const planKey = selectedPlan === 'weekly' ? 'weekly' : selectedPlan === 'monthly' ? 'monthly' : 'yearly';
  
  // Envoyer au backend
  const result = await API.createPremiumSession(currentUser.id, tg?.initData || '', {
    method: selectedPayment,
    amount: PRICES[currentCurrency][planKey],
    currency: currentCurrency,
    plan: selectedPlan,
    transactionId: 'pending_verification'
  });
  
  if (result.success) {
    if (tg) {
      tg.showAlert('Votre paiement est en cours de vérification. Vous recevrez une notification une fois activé.');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 2000);
    } else {
      alert('Vérification du paiement en cours...');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 2002);
    }
  } else {
    if (tg) {
      tg.showAlert('Erreur lors de la confirmation. Veuillez contacter le support.');
    } else {
      alert('Erreur lors de la confirmation. Veuillez contacter le support.');
    }
  }
  
  closeModal();
}

// Fermer modal au clic en dehors
document.getElementById('paymentModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'paymentModal') {
    closeModal();
  }
});
