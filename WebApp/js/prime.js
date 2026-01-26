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
    duration = '1 Semaine';
  } else if (selectedPlan === 'monthly') {
    amount = PRICES[currentCurrency].monthly;
    duration = '1 Mois';
  } else if (selectedPlan === 'yearly') {
    amount = PRICES[currentCurrency].yearly;
    duration = '1 An';
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
  
  // Instructions communes
  const commonSteps = `
    <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-lg); border: 1px solid var(--border);">
      <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-sm);">
        <span style="color: var(--text-secondary);">Plan :</span>
        <strong style="color: var(--text-primary);">${duration}</strong>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-sm);">
        <span style="color: var(--text-secondary);">Amount :</span>
        <strong style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 1.5rem;">${amount} ${currency}</strong>
      </div>
      <div style="display: flex; justify-content: space-between;">
        <span style="color: var(--text-secondary);">Your ID :</span>
        <strong style="color: var(--primary); font-family: monospace;">${currentUser?.id || 'N/A'}</strong>
      </div>
    </div>
  `;
  
  // Instructions spécifiques par méthode
  let specificInstructions = '';
  
  switch(method) {
    case 'moov':
    case 'orange':
    case 'mtn':
      const code = method === 'moov' ? '*155#' : method === 'orange' ? '#144#' : '*165#';
      specificInstructions = `
        <ol class="instructions-list">
          <li class="instruction-item">Pays accepté:  <strong>Togo | Burkina-F | Benin | Côte d'ivoire | Niger | Mali</strong></li>
          <li class="instruction-item">Selectionner le moyen et le pays de transfert (Togo ou Burkina)</li>
          <li class="instruction-item">Envoyer le motant à ce numéro: <strong>+228 98 64 27 27</strong></li>
          <li class="instruction-item">Motant: <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Confirmé la transaction</li>
          <li class="instruction-item">Envoyer la capture d'écran de paiement à l'admin.  Votre Telegram ID: <strong>${currentUser?.id}</strong></li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Envoyer la capture d'écran
        </button>
      `;
      break;
      
    case 'ecobank':
      specificInstructions = `
        <ol class="instructions-list">
          <li class="instruction-item">Go to your Ecobank online portal</li>
          <li class="instruction-item">Select "Transfer"</li>
          <li class="instruction-item">IBAN: <strong>XX00 0000 0000 0000 0000</strong></li>
          <li class="instruction-item">Amount: <strong>${amount} ${currency}</strong></li>
          <li class="instruction-item">Reference: <strong>PREMIUM-${currentUser?.id}</strong></li>
          <li class="instruction-item">Send payment proof to support</li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Contact Support
        </button>
      `;
      break;
      
    case 'usdt':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">USDT Address (TRC20):</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; word-break: break-all; font-size: 0.85rem; color: var(--primary); border: 1px solid var(--border);">
            TXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Copy the address above</li>
          <li class="instruction-item">Send <strong>${amount} USDT</strong> via TRC20 network</li>
          <li class="instruction-item">Wait for confirmation (1-3 minutes)</li>
          <li class="instruction-item">Send transaction hash + your ID to support: <strong>${currentUser?.id}</strong></li>
        </ol>
        <button class="btn btn-primary" style="width: 100%; margin-top: var(--space-md);" onclick="contactSupport()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          Confirm Payment
        </button>
      `;
      break;
      
    case 'ton':
      specificInstructions = `
        <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-md); border: 1px solid var(--border);">
          <div style="margin-bottom: var(--space-sm); color: var(--text-secondary); font-size: 0.875rem;">TON Address:</div>
          <div style="background: var(--bg-primary); padding: var(--space-md); border-radius: var(--radius-sm); font-family: monospace; word-break: break-all; font-size: 0.85rem; color: var(--primary); border: 1px solid var(--border);">
            UQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          </div>
        </div>
        <ol class="instructions-list">
          <li class="instruction-item">Open your Tonkeeper or Telegram Wallet</li>
          <li class="instruction-item">Send <strong>${amount} TON</strong> to the address above</li>
          <li class="instruction-item">Wait for confirmation</li>
          <li class="instruction-item">Your access will be activated automatically within 5 minutes</li>
        </ol>
        <button class="btn btn-success" style="width: 100%; margin-top: var(--space-md);" onclick="confirmTonPayment()">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          I Have Sent Payment
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
  const planText = selectedPlan === 'weekly' ? '1 Week' : selectedPlan === 'monthly' ? '1 Month' : '1 Year';
  const planKey = selectedPlan === 'weekly' ? 'weekly' : selectedPlan === 'monthly' ? 'monthly' : 'yearly';
  
  const message = `Hello, I want to activate my Premium account.\n\nMy ID: ${currentUser?.id}\nPlan: ${planText}\nAmount: ${PRICES[currentCurrency][planKey]} ${getCurrencySymbol(currentCurrency)}\nMethod: ${getPaymentName(selectedPayment)}`;
  
  if (tg) {
    // IMPORTANT : Remplacer VotreSupportBot par le vrai username du bot support
    tg.openTelegramLink(`https://t.me/kingcey?text=${encodeURIComponent(message)}`);
    closeModal();
  } else {
    console.log('Support message:', message);
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
      tg.showAlert('Your payment is being verified. You will receive a notification once activated.');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 2000);
    } else {
      alert('Payment verification in progress...');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 2000);
    }
  } else {
    if (tg) {
      tg.showAlert('Error confirming payment. Please contact support.');
    } else {
      alert('Error confirming payment. Please contact support.');
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