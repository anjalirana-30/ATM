/**
 * ATM Banking Kiosk — Client Controller & Web Audio Synthesizer
 */

// Global Application State
const state = {
  currentUser: null,
  currentView: "welcome",
  pinBuffer: "",
  activeInputTarget: null,
  isBalanceHidden: false,
  audioEnabled: true,
  audioCtx: null,
  sampleUsers: [
    { user_id: "A111", username: "Anjali", pin: "1414" },
    { user_id: "H112", username: "Honey", pin: "2563" },
    { user_id: "H113", username: "Harsh", pin: "4785" },
    { user_id: "K114", username: "Keval", pin: "0125" }
  ]
};

// Web Audio API Synthesizer for tactile ATM sounds
function initAudio() {
  if (!state.audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      state.audioCtx = new AudioContext();
    }
  }
}

function playKeyBeep(freq = 900, duration = 0.05) {
  if (!state.audioEnabled || !state.audioCtx) return;
  try {
    const osc = state.audioCtx.createOscillator();
    const gain = state.audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, state.audioCtx.currentTime);
    gain.gain.setValueAtTime(0.08, state.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, state.audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(state.audioCtx.destination);
    osc.start();
    osc.stop(state.audioCtx.currentTime + duration);
  } catch (e) {
    // Audio context issue
  }
}

function playCashDispenseSound() {
  if (!state.audioEnabled || !state.audioCtx) return;
  try {
    // Motor hum
    const osc = state.audioCtx.createOscillator();
    const gain = state.audioCtx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(120, state.audioCtx.currentTime);
    osc.frequency.linearRampToValueAtTime(180, state.audioCtx.currentTime + 0.6);
    gain.gain.setValueAtTime(0.12, state.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, state.audioCtx.currentTime + 0.8);
    osc.connect(gain);
    gain.connect(state.audioCtx.destination);
    osc.start();
    osc.stop(state.audioCtx.currentTime + 0.8);
  } catch (e) {}
}

function playSuccessChime() {
  if (!state.audioEnabled || !state.audioCtx) return;
  try {
    [523.25, 659.25, 783.99].forEach((f, i) => {
      setTimeout(() => playKeyBeep(f, 0.12), i * 90);
    });
  } catch (e) {}
}

function playErrorBuzz() {
  if (!state.audioEnabled || !state.audioCtx) return;
  try {
    playKeyBeep(180, 0.25);
  } catch (e) {}
}

// Toast notification helper
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === "success" ? "✔" : type === "error" ? "✘" : "ℹ"}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Currency Formatter
function formatCurrency(amount) {
  const val = Number(amount) || 0;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(val);
}

// Navigation and Screen Switching
function switchView(viewName) {
  document.querySelectorAll(".view-container").forEach((el) => el.classList.remove("active"));
  const target = document.getElementById(`view-${viewName}`);
  if (target) {
    target.classList.add("active");
    state.currentView = viewName;
  }

  // Update Back button visibility
  const backBtn = document.getElementById("screen-back-btn");
  if (backBtn) {
    backBtn.style.display = (viewName === "welcome" || viewName === "dashboard") ? "none" : "block";
  }

  // Reset PIN buffer when switching to PIN screen
  if (viewName === "pin") {
    state.pinBuffer = "";
    updatePinDots();
  }
}

// PIN Screen Logic
function updatePinDots() {
  const dots = document.querySelectorAll(".pin-dot");
  dots.forEach((dot, index) => {
    if (index < state.pinBuffer.length) {
      dot.classList.add("filled");
    } else {
      dot.classList.remove("filled");
    }
  });

  // Auto-submit when 4 digits are entered
  if (state.pinBuffer.length === 4) {
    submitLogin();
  }
}

// Login Process
async function submitLogin() {
  const userIdInput = document.getElementById("login-user-id");
  const userId = userIdInput.value.trim().toUpperCase();
  const pin = state.pinBuffer;

  if (!userId) {
    showToast("Please enter or select a User ID.", "error");
    switchView("welcome");
    return;
  }

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, pin })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      playSuccessChime();
      state.currentUser = data.user;
      showToast(data.message, "success");
      updateDashboardUI();
      switchView("dashboard");
    } else {
      playErrorBuzz();
      showToast(data.error || "Login failed.", "error");
      state.pinBuffer = "";
      updatePinDots();
      if (data.locked) {
        switchView("welcome");
      }
    }
  } catch (err) {
    // Fallback demo mock if server is running offline
    console.warn("API unavailable, testing demo credentials:", err);
    const demo = state.sampleUsers.find((u) => u.user_id === userId && u.pin === pin);
    if (demo) {
      state.currentUser = {
        user_id: demo.user_id,
        username: demo.username,
        acc_no: "******" + (demo.user_id === "A111" ? "452452" : "784152"),
        phone: "****1234",
        avl_bal: 10000,
        formatted_bal: "₹10,000",
        history: { withdraw_history: [], deposit_history: [] }
      };
      playSuccessChime();
      updateDashboardUI();
      switchView("dashboard");
    } else {
      playErrorBuzz();
      showToast("Invalid credentials or server connection issue.", "error");
      state.pinBuffer = "";
      updatePinDots();
    }
  }
}

// Dashboard UI Updater
function updateDashboardUI() {
  if (!state.currentUser) return;
  document.getElementById("dash-user-name").innerText = state.currentUser.username;
  document.getElementById("dash-acc-no").innerText = state.currentUser.acc_no || "******452452";
  updateBalanceDisplay();
}

function updateBalanceDisplay() {
  const balEl = document.getElementById("dash-balance-val");
  if (!state.currentUser) return;
  if (state.isBalanceHidden) {
    balEl.innerText = "₹ ••••••••";
  } else {
    balEl.innerText = formatCurrency(state.currentUser.avl_bal);
  }
}

// Cash Dispenser Animation
function triggerCashDispenseAnimation(amount, numNotes = 1) {
  playCashDispenseSound();
  const noteEl = document.getElementById("dispensed-note");
  noteEl.innerHTML = `
    <div style="font-size: 10px; opacity: 0.8;">RESERVE BANK OF INDIA</div>
    <div style="font-size: 20px;">₹500</div>
    <div style="font-size: 11px; text-align: right;">${numNotes} NOTE(S) - COLLECT CASH</div>
  `;
  noteEl.classList.add("ejected");
}

function collectCash() {
  const noteEl = document.getElementById("dispensed-note");
  noteEl.classList.remove("ejected");
  showToast("Cash collected successfully! Please take your receipt.", "success");
}

// Receipt Printer Animation
function printReceipt(txn, type = "Withdraw") {
  const receiptEl = document.getElementById("receipt-paper");
  receiptEl.innerHTML = `
    <div style="text-align: center; font-weight: bold; margin-bottom: 8px;">
      🏧 METRO BANK ATM
      <div>RECEIPT SLIP</div>
    </div>
    <div>TXN ID : ${txn.txn_id}</div>
    <div>DATE   : ${txn.date_time}</div>
    <div>TYPE   : ${type.toUpperCase()}</div>
    <div>AMOUNT : ${formatCurrency(txn.amount)}</div>
    <div>AVAIL  : ${formatCurrency(txn.balance_after)}</div>
    <div style="text-align: center; margin-top: 8px; border-top: 1px dashed #666; padding-top: 4px;">
      THANK YOU FOR BANKING WITH US
    </div>
  `;
  receiptEl.style.display = "block";
}

// Transaction: Withdraw
async function executeWithdraw(amount) {
  if (!state.currentUser) return;
  try {
    const res = await fetch("/api/withdraw", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: state.currentUser.user_id, amount })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      state.currentUser.avl_bal = data.new_balance;
      state.currentUser.history = data.history;
      updateBalanceDisplay();
      triggerCashDispenseAnimation(amount, data.notes_dispensed);
      printReceipt(data.transaction, "Withdraw");
      showToast(data.message, "success");
      switchView("dashboard");
    } else {
      playErrorBuzz();
      showToast(data.error || "Withdrawal failed.", "error");
    }
  } catch (err) {
    showToast("Network connection error.", "error");
  }
}

// Transaction: Deposit
async function executeDeposit(amount) {
  if (!state.currentUser) return;
  try {
    const res = await fetch("/api/deposit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: state.currentUser.user_id, amount })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      playSuccessChime();
      state.currentUser.avl_bal = data.new_balance;
      state.currentUser.history = data.history;
      updateBalanceDisplay();
      printReceipt(data.transaction, "Deposit");
      showToast(data.message, "success");
      switchView("dashboard");
    } else {
      playErrorBuzz();
      showToast(data.error || "Deposit failed.", "error");
    }
  } catch (err) {
    showToast("Network connection error.", "error");
  }
}

// Mini Statement Renderer
function renderMiniStatement() {
  if (!state.currentUser) return;
  const tbody = document.getElementById("statement-tbody");
  tbody.innerHTML = "";

  const history = state.currentUser.history || {};
  const wList = (history.withdraw_history || []).map((t) => ({ ...t, type: "Withdraw" }));
  const dList = (history.deposit_history || []).map((t) => ({ ...t, type: "Deposit" }));
  const combined = [...wList, ...dList];

  combined.sort((a, b) => new Date(b.date_time) - new Date(a.date_time));

  if (combined.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #94a3b8; padding: 20px;">No transaction records found.</td></tr>`;
    return;
  }

  combined.slice(0, 10).forEach((t) => {
    const isW = t.type.toLowerCase() === "withdraw";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${t.date_time || "N/A"}</td>
      <td><span class="badge ${isW ? "badge-withdraw" : "badge-deposit"}">${t.type}</span></td>
      <td style="font-weight: 700; color: ${isW ? "#ef4444" : "#00e599"};">${formatCurrency(t.amount)}</td>
      <td>${formatCurrency(t.balance_after)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Hardware Keypad Listener
function handleKeypadInput(key) {
  initAudio();
  playKeyBeep();

  if (key === "CANCEL") {
    if (state.currentView === "welcome" || state.currentView === "pin") {
      state.pinBuffer = "";
      updatePinDots();
      switchView("welcome");
    } else {
      switchView("dashboard");
    }
    return;
  }

  if (key === "CLEAR") {
    if (state.currentView === "pin") {
      state.pinBuffer = "";
      updatePinDots();
    } else if (state.activeInputTarget) {
      state.activeInputTarget.value = "";
    }
    return;
  }

  if (key === "ENTER") {
    if (state.currentView === "welcome") {
      proceedToPin();
    } else if (state.currentView === "pin") {
      submitLogin();
    } else if (state.currentView === "withdraw") {
      const amt = parseInt(document.getElementById("custom-withdraw-amt").value, 10);
      if (amt) executeWithdraw(amt);
    } else if (state.currentView === "deposit") {
      const amt = parseInt(document.getElementById("deposit-amt-input").value, 10);
      if (amt) executeDeposit(amt);
    }
    return;
  }

  // Numeric digit pressed (0-9)
  if (state.currentView === "pin") {
    if (state.pinBuffer.length < 4) {
      state.pinBuffer += key;
      updatePinDots();
    }
  } else if (state.activeInputTarget) {
    state.activeInputTarget.value += key;
  }
}

function proceedToPin() {
  const userId = document.getElementById("login-user-id").value.trim();
  if (!userId) {
    showToast("Please enter or select a User ID.", "error");
    return;
  }
  switchView("pin");
}

// Event Listeners Setup
document.addEventListener("DOMContentLoaded", () => {
  // Update live clock
  setInterval(() => {
    const now = new Date();
    const clockEl = document.getElementById("live-clock");
    if (clockEl) {
      clockEl.innerText = now.toLocaleTimeString("en-GB", { hour12: false });
    }
  }, 1000);

  // Focus tracking for numeric inputs
  document.querySelectorAll("input").forEach((inp) => {
    inp.addEventListener("focus", () => {
      state.activeInputTarget = inp;
    });
  });

  // Hardware keypad buttons
  document.querySelectorAll(".key-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-key");
      handleKeypadInput(key);
    });
  });

  // Demo user pill buttons
  document.querySelectorAll(".user-pill-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      initAudio();
      playKeyBeep(1100);
      const uid = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const cardNum = btn.getAttribute("data-card");
      document.getElementById("login-user-id").value = uid;
      document.getElementById("card-preview-holder").innerText = name;
      document.getElementById("card-preview-num").innerText = "4524 •••• •••• " + cardNum.slice(-4);
      switchView("pin");
    });
  });

  // Audio Toggle Button
  const audioBtn = document.getElementById("audio-toggle");
  if (audioBtn) {
    audioBtn.addEventListener("click", () => {
      state.audioEnabled = !state.audioEnabled;
      audioBtn.innerText = state.audioEnabled ? "🔊 Sound On" : "🔇 Sound Off";
    });
  }

  // Eye Toggle Button for Balance
  const eyeBtn = document.getElementById("eye-toggle-btn");
  if (eyeBtn) {
    eyeBtn.addEventListener("click", () => {
      state.isBalanceHidden = !state.isBalanceHidden;
      eyeBtn.innerText = state.isBalanceHidden ? "👁‍🗨" : "👁";
      updateBalanceDisplay();
    });
  }

  // Dashboard Action Navigation
  document.querySelectorAll(".action-card").forEach((card) => {
    card.addEventListener("click", () => {
      initAudio();
      playKeyBeep(1000);
      const action = card.getAttribute("data-action");
      if (action === "withdraw") switchView("withdraw");
      else if (action === "deposit") switchView("deposit");
      else if (action === "quick-cash") switchView("quick-withdraw");
      else if (action === "statement") {
        renderMiniStatement();
        switchView("statement");
      } else if (action === "details") {
        renderAccountDetails();
        switchView("details");
      } else if (action === "change-pin") switchView("change-pin");
      else if (action === "register") switchView("register");
      else if (action === "logout") logout();
    });
  });

  // Quick Cash preset buttons
  document.querySelectorAll(".quick-cash-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      initAudio();
      playKeyBeep();
      const amt = parseInt(btn.getAttribute("data-amt"), 10);
      executeWithdraw(amt);
    });
  });

  // Custom Withdraw submit
  document.getElementById("btn-custom-withdraw").addEventListener("click", () => {
    const amt = parseInt(document.getElementById("custom-withdraw-amt").value, 10);
    if (!amt) {
      showToast("Please enter an amount.", "error");
      return;
    }
    executeWithdraw(amt);
  });

  // Deposit submit
  document.getElementById("btn-submit-deposit").addEventListener("click", () => {
    const amt = parseInt(document.getElementById("deposit-amt-input").value, 10);
    if (!amt) {
      showToast("Please enter deposit amount.", "error");
      return;
    }
    executeDeposit(amt);
  });

  // Change PIN submit
  document.getElementById("btn-submit-pin-change").addEventListener("click", async () => {
    const curPin = document.getElementById("pin-change-current").value.trim();
    const newPin = document.getElementById("pin-change-new").value.trim();
    const confPin = document.getElementById("pin-change-confirm").value.trim();

    try {
      const res = await fetch("/api/change-pin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: state.currentUser.user_id,
          current_pin: curPin,
          new_pin: newPin,
          confirm_pin: confPin
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        playSuccessChime();
        showToast("PIN successfully updated!", "success");
        document.getElementById("pin-change-current").value = "";
        document.getElementById("pin-change-new").value = "";
        document.getElementById("pin-change-confirm").value = "";
        switchView("dashboard");
      } else {
        playErrorBuzz();
        showToast(data.error || "PIN change failed.", "error");
      }
    } catch (e) {
      showToast("Connection error.", "error");
    }
  });

  // Register New User submit
  document.getElementById("btn-submit-register").addEventListener("click", async () => {
    const username = document.getElementById("reg-name").value.trim();
    const phone = document.getElementById("reg-phone").value.trim();
    const accNo = document.getElementById("reg-acc").value.trim();
    const pin = document.getElementById("reg-pin").value.trim();
    const userId = document.getElementById("reg-id").value.trim();
    const initBal = parseFloat(document.getElementById("reg-bal").value);

    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          phone,
          acc_no: accNo,
          pin,
          user_id: userId,
          initial_balance: initBal
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        playSuccessChime();
        showToast(data.message, "success");
        switchView("welcome");
      } else {
        playErrorBuzz();
        showToast(data.error || "Registration failed.", "error");
      }
    } catch (e) {
      showToast("Connection error.", "error");
    }
  });

  // Cash collection click
  document.getElementById("dispensed-note").addEventListener("click", collectCash);

  // Screen back button
  document.getElementById("screen-back-btn").addEventListener("click", () => {
    initAudio();
    playKeyBeep();
    if (state.currentView === "pin") {
      switchView("welcome");
    } else {
      switchView("dashboard");
    }
  });
});

function renderAccountDetails() {
  if (!state.currentUser) return;
  document.getElementById("details-name").innerText = state.currentUser.username;
  document.getElementById("details-user-id").innerText = state.currentUser.user_id;
  document.getElementById("details-phone").innerText = state.currentUser.phone;
  document.getElementById("details-acc-no").innerText = state.currentUser.acc_no;
  document.getElementById("details-balance").innerText = formatCurrency(state.currentUser.avl_bal);
}

function logout() {
  playKeyBeep(600);
  state.currentUser = null;
  state.pinBuffer = "";
  showToast("Logged out successfully. Thank you for banking with us!", "info");
  switchView("welcome");
}
