/**
 * PyLambda Web Client
 * Modular Single Page Application (SPA) for PyLambda Auth & Services
 * Built with Vanilla JavaScript, Tailwind CSS, and Lucide Icons
 */

// ============================================================================
// 1. APPLICATION STATE & STORAGE
// ============================================================================

const STORAGE_KEYS = {
  BASE_URL: 'pylambda_base_url',
  TOKEN: 'pylambda_token',
  TOKEN_EXP: 'pylambda_token_exp',
  USER: 'pylambda_user',
};

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';

const AppState = {
  baseUrl: localStorage.getItem(STORAGE_KEYS.BASE_URL) || DEFAULT_BASE_URL,
  token: localStorage.getItem(STORAGE_KEYS.TOKEN) || null,
  tokenExp: parseInt(localStorage.getItem(STORAGE_KEYS.TOKEN_EXP) || '0', 10),
  user: null,
  timerInterval: null,

  setToken(token, expiresInSeconds = 1800) {
    this.token = token;
    const expTime = Date.now() + expiresInSeconds * 1000;
    this.tokenExp = expTime;
    localStorage.setItem(STORAGE_KEYS.TOKEN, token);
    localStorage.setItem(STORAGE_KEYS.TOKEN_EXP, expTime.toString());
    startTokenExpiryTimer();
  },

  clearAuth() {
    this.token = null;
    this.tokenExp = 0;
    this.user = null;
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TOKEN_EXP);
    localStorage.removeItem(STORAGE_KEYS.USER);
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  },

  setBaseUrl(url) {
    let cleanUrl = (url || DEFAULT_BASE_URL).trim();
    if (cleanUrl.endsWith('/')) {
      cleanUrl = cleanUrl.slice(0, -1);
    }
    this.baseUrl = cleanUrl;
    localStorage.setItem(STORAGE_KEYS.BASE_URL, cleanUrl);
  },

  setUser(user) {
    this.user = user;
    if (user) {
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    } else {
      localStorage.removeItem(STORAGE_KEYS.USER);
    }
  }
};

// ============================================================================
// 2. TOAST NOTIFICATION SYSTEM
// ============================================================================

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'pointer-events-auto flex items-start gap-3 p-4 rounded-xl border shadow-xl backdrop-blur-md transition-all duration-300 transform translate-y-2 opacity-0';

  let borderColor = 'border-slate-700 bg-slate-900/95 text-slate-100';
  let iconName = 'info';
  let iconColor = 'text-indigo-400';

  if (type === 'success') {
    borderColor = 'border-emerald-800/80 bg-slate-900/95 text-emerald-100';
    iconName = 'check-circle-2';
    iconColor = 'text-emerald-400';
  } else if (type === 'error') {
    borderColor = 'border-red-800/80 bg-slate-900/95 text-red-100';
    iconName = 'alert-octagon';
    iconColor = 'text-red-400';
  } else if (type === 'warning') {
    borderColor = 'border-amber-800/80 bg-slate-900/95 text-amber-100';
    iconName = 'alert-triangle';
    iconColor = 'text-amber-400';
  }

  toast.className += ` ${borderColor}`;

  toast.innerHTML = `
    <i data-lucide="${iconName}" class="w-5 h-5 ${iconColor} shrink-0 mt-0.5"></i>
    <div class="flex-1 text-xs font-medium leading-relaxed">${escapeHtml(message)}</div>
    <button class="text-slate-400 hover:text-slate-200 transition shrink-0" onclick="this.parentElement.remove()">
      <i data-lucide="x" class="w-4 h-4"></i>
    </button>
  `;

  container.appendChild(toast);
  lucide.createIcons({ root: toast });

  // Trigger entrance animation
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');
  });

  // Auto remove
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-x-2');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function escapeHtml(str) {
  if (typeof str !== 'string') return String(str);
  return str.replace(/[&<>"']/g, match => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[match]));
}

// ============================================================================
// 3. API CLIENT (WRAPS FETCH WITH AUTH & FASTAPI ERROR PARSING)
// ============================================================================

async function apiRequest(endpoint, options = {}) {
  const url = `${AppState.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (AppState.token) {
    headers['Authorization'] = `Bearer ${AppState.token}`;
  }

  const startTime = performance.now();
  let status = null;

  try {
    const response = await fetch(url, {
      ...options,
      headers
    });

    const latency = Math.round(performance.now() - startTime);
    status = response.status;

    let responseData = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    if (!response.ok) {
      // Parse FastAPI standard errors
      let errorMessage = `HTTP ${response.status} Error`;

      if (responseData && responseData.detail) {
        if (typeof responseData.detail === 'string') {
          errorMessage = responseData.detail;
        } else if (Array.isArray(responseData.detail)) {
          // Pydantic 422 validation errors
          errorMessage = responseData.detail.map(err => {
            const field = err.loc ? err.loc.slice(1).join('.') : 'field';
            return `${field}: ${err.msg}`;
          }).join(', ');
        }
      }

      // Handle token expiration/invalidation
      if (response.status === 401 && AppState.token) {
        showToast('Your session has expired or is invalid. Please sign in again.', 'warning');
        handleLogout();
      }

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = responseData;
      error.latency = latency;
      throw error;
    }

    return { data: responseData, status, latency };
  } catch (err) {
    const latency = Math.round(performance.now() - startTime);
    if (!err.latency) err.latency = latency;
    if (!err.status && status) err.status = status;
    throw err;
  }
}

// ============================================================================
// 4. AUTH & USER SERVICES
// ============================================================================

const AuthService = {
  // POST /v1/auth/signup
  async signup(username, useremail, password) {
    return await apiRequest('/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ username, useremail, password })
    });
  },

  // POST /v1/auth/login
  async login(useremail, password) {
    const res = await apiRequest('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ useremail, password })
    });
    const { access_token, expires_in } = res.data;
    AppState.setToken(access_token, expires_in || 1800);
    return res.data;
  },

  // GET /v1/auth/me
  async getMe() {
    const res = await apiRequest('/v1/auth/me', {
      method: 'GET'
    });
    AppState.setUser(res.data);
    return res.data;
  },

  // POST /v1/auth/me/change-password
  async changePassword(current_password, new_password) {
    return await apiRequest('/v1/auth/me/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password })
    });
  },

  // POST /v1/auth/forgot-password
  async forgotPassword(useremail) {
    return await apiRequest('/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ useremail })
    });
  },

  // POST /v1/auth/reset-password
  async resetPassword(token, new_password) {
    return await apiRequest('/v1/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password })
    });
  },

  // POST /v1/auth/me/verify-phone
  async verifyPhone(phone_number) {
    // phone_number must be an integer
    const parsedNumber = parseInt(phone_number.toString().replace(/\D/g, ''), 10);
    if (isNaN(parsedNumber)) {
      throw new Error('Please enter a valid phone number containing digits.');
    }
    return await apiRequest('/v1/auth/me/verify-phone', {
      method: 'POST',
      body: JSON.stringify({ phone_number: parsedNumber })
    });
  },

  // GET /health
  async checkHealth() {
    return await apiRequest('/health', { method: 'GET' });
  },

  // GET /
  async checkRoot() {
    return await apiRequest('/', { method: 'GET' });
  }
};

// ============================================================================
// 5. UI VIEW & TAB CONTROLLER
// ============================================================================

function updateUIState() {
  const viewAuth = document.getElementById('view-auth');
  const viewDashboard = document.getElementById('view-dashboard');
  const navUserArea = document.getElementById('nav-user-area');

  if (AppState.token) {
    // Authenticated state
    viewAuth.classList.add('hidden');
    viewDashboard.classList.remove('hidden');
    navUserArea.classList.remove('hidden');
    navUserArea.classList.add('flex');

    // Update Profile details in UI
    renderProfileView();
  } else {
    // Logged out state
    viewAuth.classList.remove('hidden');
    viewDashboard.classList.add('hidden');
    navUserArea.classList.add('hidden');
    navUserArea.classList.remove('flex');
  }

  lucide.createIcons();
}

function switchAuthSubPanel(panelName) {
  const panels = ['login', 'signup', 'forgot', 'reset'];
  panels.forEach(p => {
    const el = document.getElementById(`panel-${p}`);
    if (el) el.classList.add('hidden');
  });

  const target = document.getElementById(`panel-${panelName}`);
  if (target) target.classList.remove('hidden');

  // Update tabs if in login/signup mode
  const tabLogin = document.getElementById('tab-btn-login');
  const tabSignup = document.getElementById('tab-btn-signup');
  const tabBar = document.getElementById('auth-tab-bar');

  if (panelName === 'login') {
    tabBar.classList.remove('hidden');
    tabLogin.className = 'flex-1 py-2 text-center rounded-lg text-white bg-indigo-600/90 shadow transition';
    tabSignup.className = 'flex-1 py-2 text-center rounded-lg hover:text-slate-200 transition';
  } else if (panelName === 'signup') {
    tabBar.classList.remove('hidden');
    tabLogin.className = 'flex-1 py-2 text-center rounded-lg hover:text-slate-200 transition';
    tabSignup.className = 'flex-1 py-2 text-center rounded-lg text-white bg-indigo-600/90 shadow transition';
  } else {
    tabBar.classList.add('hidden');
  }

  lucide.createIcons();
}

function switchDashboardTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.remove('active', 'text-white', 'bg-indigo-600/20', 'border', 'border-indigo-500/30');
    btn.classList.add('text-slate-400');
  });

  const targetTab = document.getElementById(`tab-content-${tabId.replace('tab-', '')}`);
  if (targetTab) {
    targetTab.classList.remove('hidden');
  }

  const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
  if (activeBtn) {
    activeBtn.classList.add('active', 'text-white', 'bg-indigo-600/20', 'border', 'border-indigo-500/30');
    activeBtn.classList.remove('text-slate-400');
  }

  lucide.createIcons();
}

function renderProfileView() {
  const user = AppState.user;
  const usernameEl = document.getElementById('profile-card-username');
  const emailEl = document.getElementById('profile-card-email');
  const tokenPreviewEl = document.getElementById('profile-token-preview');
  const navUserName = document.getElementById('user-display-name');
  const navUserInitials = document.getElementById('user-avatar-initials');

  if (user) {
    usernameEl.textContent = user.username || 'Unknown';
    emailEl.textContent = user.useremail || 'No email';
    navUserName.textContent = user.username || 'User';
    navUserInitials.textContent = (user.username ? user.username.charAt(0) : 'U').toUpperCase();
  }

  if (AppState.token) {
    tokenPreviewEl.textContent = AppState.token;
  } else {
    tokenPreviewEl.textContent = 'No active token';
  }
}

// Token Expiry Progress & Countdown
function startTokenExpiryTimer() {
  if (AppState.timerInterval) {
    clearInterval(AppState.timerInterval);
  }

  function updateTimer() {
    const timerLabel = document.getElementById('token-timer-label');
    const timerProgress = document.getElementById('token-timer-progress');
    if (!timerLabel || !timerProgress) return;

    if (!AppState.tokenExp) {
      timerLabel.textContent = '--:--';
      timerProgress.style.width = '0%';
      return;
    }

    const remainingMs = AppState.tokenExp - Date.now();
    if (remainingMs <= 0) {
      timerLabel.textContent = 'Expired';
      timerProgress.style.width = '0%';
      showToast('Your session token has expired. Please sign in again.', 'warning');
      handleLogout();
      return;
    }

    const remainingSec = Math.floor(remainingMs / 1000);
    const mins = Math.floor(remainingSec / 60);
    const secs = remainingSec % 60;
    timerLabel.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

    // 1800s total duration
    const percent = Math.min(100, Math.max(0, (remainingSec / 1800) * 100));
    timerProgress.style.width = `${percent}%`;

    if (percent < 15) {
      timerProgress.className = 'bg-red-500 h-full w-full transition-all duration-1000';
    } else if (percent < 30) {
      timerProgress.className = 'bg-amber-500 h-full w-full transition-all duration-1000';
    } else {
      timerProgress.className = 'bg-indigo-500 h-full w-full transition-all duration-1000';
    }
  }

  updateTimer();
  AppState.timerInterval = setInterval(updateTimer, 1000);
}

function handleLogout() {
  AppState.clearAuth();
  updateUIState();
  switchAuthSubPanel('login');
  showToast('You have been logged out.', 'info');
}

// ============================================================================
// 6. HEALTH CHECK & CONNECTIVITY
// ============================================================================

async function verifyBackendHealth() {
  const dot = document.getElementById('health-dot');
  const label = document.getElementById('health-label');

  dot.className = 'w-2 h-2 rounded-full bg-amber-400 animate-pulse';
  label.textContent = 'Pinging...';

  try {
    const res = await AuthService.checkHealth();
    dot.className = 'w-2 h-2 rounded-full bg-emerald-400';
    label.textContent = `Online (${res.latency}ms)`;
  } catch (err) {
    dot.className = 'w-2 h-2 rounded-full bg-red-500';
    label.textContent = 'Offline';
  }
}

// ============================================================================
// 7. EVENT LISTENERS & SETUP
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // Setup saved base URL in settings modal
  const baseUrlInput = document.getElementById('settings-base-url');
  if (baseUrlInput) baseUrlInput.value = AppState.baseUrl;

  // Restore cached user profile if available
  const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
  if (cachedUser) {
    try {
      AppState.user = JSON.parse(cachedUser);
    } catch (_) {}
  }

  // Initial UI Render
  updateUIState();
  if (AppState.token) {
    startTokenExpiryTimer();
    // Refresh user profile from backend
    try {
      await AuthService.getMe();
      renderProfileView();
    } catch (_) {
      // If token expired, getMe() handles logout
    }
  }

  // Ping backend health
  verifyBackendHealth();

  // --- Auth Navigation Switches ---
  document.getElementById('tab-btn-login')?.addEventListener('click', () => switchAuthSubPanel('login'));
  document.getElementById('tab-btn-signup')?.addEventListener('click', () => switchAuthSubPanel('signup'));
  document.getElementById('link-forgot-password')?.addEventListener('click', () => switchAuthSubPanel('forgot'));
  document.getElementById('back-to-login-from-forgot')?.addEventListener('click', () => switchAuthSubPanel('login'));
  document.getElementById('back-to-login-from-reset')?.addEventListener('click', () => switchAuthSubPanel('login'));
  document.getElementById('link-has-reset-token')?.addEventListener('click', () => switchAuthSubPanel('reset'));

  // --- Dashboard Tab Switches ---
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tabId = e.currentTarget.getAttribute('data-tab');
      if (tabId) switchDashboardTab(tabId);
    });
  });

  // --- Password visibility toggles ---
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-toggle-password');
      const input = document.getElementById(targetId);
      if (!input) return;
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      btn.innerHTML = isPassword ? '<i data-lucide="eye-off" class="w-4 h-4"></i>' : '<i data-lucide="eye" class="w-4 h-4"></i>';
      lucide.createIcons({ root: btn });
    });
  });

  // --- Form: Login ---
  const formLogin = document.getElementById('form-login');
  formLogin?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const submitBtn = document.getElementById('btn-login-submit');

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Signing in...</span>';
      lucide.createIcons({ root: submitBtn });

      await AuthService.login(email, password);
      showToast('Signed in successfully!', 'success');

      // Fetch user profile
      await AuthService.getMe();
      updateUIState();
      switchDashboardTab('tab-profile');
    } catch (err) {
      showToast(err.message || 'Login failed. Please check your credentials.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>Sign In</span><i data-lucide="arrow-right" class="w-4 h-4"></i>';
      lucide.createIcons({ root: submitBtn });
    }
  });

  // --- Form: Signup ---
  const formSignup = document.getElementById('form-signup');
  formSignup?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('signup-username').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const submitBtn = document.getElementById('btn-signup-submit');

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Creating account...</span>';
      lucide.createIcons({ root: submitBtn });

      await AuthService.signup(username, email, password);
      showToast('Account created successfully! Signing in...', 'success');

      // Auto login after signup
      await AuthService.login(email, password);
      await AuthService.getMe();
      updateUIState();
      switchDashboardTab('tab-profile');
    } catch (err) {
      showToast(err.message || 'Registration failed.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>Create Account</span><i data-lucide="user-plus" class="w-4 h-4"></i>';
      lucide.createIcons({ root: submitBtn });
    }
  });

  // --- Form: Forgot Password ---
  const formForgot = document.getElementById('form-forgot');
  formForgot?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value.trim();
    const submitBtn = document.getElementById('btn-forgot-submit');

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Sending request...</span>';
      lucide.createIcons({ root: submitBtn });

      const res = await AuthService.forgotPassword(email);
      showToast(res.data?.message || 'If the account exists, a reset link was sent.', 'success', 6000);
      switchAuthSubPanel('reset');
    } catch (err) {
      showToast(err.message || 'Unable to process reset request.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>Send Reset Link</span><i data-lucide="send" class="w-4 h-4"></i>';
      lucide.createIcons({ root: submitBtn });
    }
  });

  // --- Form: Reset Password ---
  const formReset = document.getElementById('form-reset');
  formReset?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const token = document.getElementById('reset-token').value.trim();
    const newPassword = document.getElementById('reset-new-password').value;
    const submitBtn = document.getElementById('btn-reset-submit');

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Resetting password...</span>';
      lucide.createIcons({ root: submitBtn });

      const res = await AuthService.resetPassword(token, newPassword);
      showToast(res.data?.message || 'Password reset successfully! Please sign in.', 'success');
      formReset.reset();
      switchAuthSubPanel('login');
    } catch (err) {
      showToast(err.message || 'Password reset failed. Token may be invalid or expired.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>Update Password</span><i data-lucide="check" class="w-4 h-4"></i>';
      lucide.createIcons({ root: submitBtn });
    }
  });

  // --- Form: Change Password (Authenticated) ---
  const formChangePassword = document.getElementById('form-change-password');
  formChangePassword?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const currPassword = document.getElementById('change-curr-password').value;
    const newPassword = document.getElementById('change-new-password').value;
    const submitBtn = document.getElementById('btn-change-password-submit');

    if (currPassword === newPassword) {
      showToast('New password must differ from your current password.', 'warning');
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Updating...</span>';
      lucide.createIcons({ root: submitBtn });

      const res = await AuthService.changePassword(currPassword, newPassword);
      showToast(res.data?.message || 'Password changed successfully.', 'success');
      formChangePassword.reset();
    } catch (err) {
      showToast(err.message || 'Failed to update password.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i><span>Update Password</span>';
      lucide.createIcons({ root: submitBtn });
    }
  });

  // --- Form: Phone Verification (Authenticated) ---
  const formVerifyPhone = document.getElementById('form-verify-phone');
  const phoneResultEl = document.getElementById('phone-verification-result');
  formVerifyPhone?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const phoneInput = document.getElementById('phone-number-input').value.trim();
    const submitBtn = document.getElementById('btn-verify-phone-submit');

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Verifying...</span>';
      lucide.createIcons({ root: submitBtn });
      phoneResultEl.classList.add('hidden');

      const res = await AuthService.verifyPhone(phoneInput);
      showToast(res.data?.message || 'Phone number verified successfully!', 'success');

      phoneResultEl.className = 'rounded-xl p-4 text-xs font-mono bg-emerald-950/40 border border-emerald-800/60 text-emerald-300';
      phoneResultEl.textContent = JSON.stringify(res.data, null, 2);
      phoneResultEl.classList.remove('hidden');
    } catch (err) {
      showToast(err.message || 'Phone verification failed.', 'error');
      phoneResultEl.className = 'rounded-xl p-4 text-xs font-mono bg-red-950/40 border border-red-800/60 text-red-300';
      phoneResultEl.textContent = JSON.stringify({ error: err.message, details: err.data }, null, 2);
      phoneResultEl.classList.remove('hidden');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="check-circle-2" class="w-4 h-4"></i><span>Verify Phone</span>';
      lucide.createIcons({ root: submitBtn });
    }
  });

  // --- Copy Token Button ---
  document.getElementById('btn-copy-token')?.addEventListener('click', () => {
    if (AppState.token) {
      navigator.clipboard.writeText(AppState.token)
        .then(() => showToast('Bearer token copied to clipboard!', 'info', 2000))
        .catch(() => showToast('Failed to copy token to clipboard', 'warning'));
    }
  });

  // --- Refresh Profile Button ---
  document.getElementById('btn-refresh-profile')?.addEventListener('click', async () => {
    try {
      await AuthService.getMe();
      renderProfileView();
      showToast('Profile refreshed from backend.', 'success', 2000);
    } catch (err) {
      showToast(err.message || 'Failed to refresh profile.', 'error');
    }
  });

  // --- Logout Action ---
  document.getElementById('btn-logout')?.addEventListener('click', handleLogout);

  // --- Health Check Button ---
  document.getElementById('btn-check-health')?.addEventListener('click', () => {
    verifyBackendHealth();
  });

  // --- API Settings Modal Controls ---
  const modalSettings = document.getElementById('modal-settings');
  document.getElementById('btn-open-settings')?.addEventListener('click', () => {
    baseUrlInput.value = AppState.baseUrl;
    modalSettings.classList.remove('hidden');
  });
  document.getElementById('btn-close-settings')?.addEventListener('click', () => {
    modalSettings.classList.add('hidden');
  });
  modalSettings?.addEventListener('click', (e) => {
    if (e.target === modalSettings) modalSettings.classList.add('hidden');
  });
  document.getElementById('btn-reset-settings')?.addEventListener('click', () => {
    baseUrlInput.value = DEFAULT_BASE_URL;
  });
  document.getElementById('btn-save-settings')?.addEventListener('click', () => {
    AppState.setBaseUrl(baseUrlInput.value);
    modalSettings.classList.add('hidden');
    showToast(`API Base URL updated to: ${AppState.baseUrl}`, 'info');
    verifyBackendHealth();
  });

  // --- Developer Tools: Quick API Tests ---
  const consoleOutput = document.getElementById('explorer-output');
  const consoleStatus = document.getElementById('explorer-status');
  const consoleLatency = document.getElementById('explorer-latency');

  async function runQuickTest(endpoint, method = 'GET') {
    consoleOutput.textContent = `Dispatching ${method} ${endpoint} ...`;
    consoleStatus.textContent = 'Executing...';
    consoleLatency.textContent = '...';

    try {
      const res = await apiRequest(endpoint, { method });
      consoleStatus.textContent = `${res.status} OK`;
      consoleStatus.className = 'text-emerald-400 font-bold';
      consoleLatency.textContent = `${res.latency}ms`;
      consoleOutput.className = 'font-mono text-xs text-emerald-400 whitespace-pre-wrap overflow-x-auto max-h-96 min-h-[160px]';
      consoleOutput.textContent = JSON.stringify(res.data, null, 2);
    } catch (err) {
      consoleStatus.textContent = err.status ? `${err.status} Error` : 'Network Error';
      consoleStatus.className = 'text-red-400 font-bold';
      consoleLatency.textContent = err.latency ? `${err.latency}ms` : '-';
      consoleOutput.className = 'font-mono text-xs text-red-400 whitespace-pre-wrap overflow-x-auto max-h-96 min-h-[160px]';
      consoleOutput.textContent = JSON.stringify({
        error: err.message,
        details: err.data || null
      }, null, 2);
    }
  }

  document.getElementById('quick-test-root')?.addEventListener('click', () => runQuickTest('/'));
  document.getElementById('quick-test-health')?.addEventListener('click', () => runQuickTest('/health'));
  document.getElementById('quick-test-me')?.addEventListener('click', () => runQuickTest('/v1/auth/me'));
});

// ============================================================================
// 8. EXTENSIBILITY HELPER (FOR ADDING FUTURE MODULES EASILY)
// ============================================================================
/**
 * To add a new module (e.g. Lambda Functions, Storage, Analytics):
 * 1. Add a navigation button in index.html with data-tab="tab-lambdas"
 * 2. Add a corresponding <div id="tab-content-lambdas" class="tab-pane hidden"></div>
 * 3. Use AppState.token & apiRequest('/v1/your-endpoint') to communicate with PyLambda!
 */
window.PyLambdaClient = {
  state: AppState,
  api: apiRequest,
  auth: AuthService,
  toast: showToast,
  switchTab: switchDashboardTab
};
 