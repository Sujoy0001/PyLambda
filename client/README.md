# PyLambda Web Client

A modern, responsive Single-Page Application (SPA) built with **HTML5**, **Tailwind CSS**, and **Vanilla JavaScript** designed to interface directly with the PyLambda backend.

---

## 🚀 Getting Started

### Option 1: Direct File Open
You can directly open [`index.html`](file:///d:/PyLambda/client/index.html) in any modern web browser:
```powershell
Start-Process "d:\PyLambda\client\index.html"
```

### Option 2: Local HTTP Server (Recommended)
Running through an HTTP server avoids potential browser restrictions on `fetch()` calls to `localhost`:

Using Python:
```powershell
cd d:\PyLambda\client
python -m http.server 3000
```
Then visit: `http://localhost:3000`

Using Node (`npx serve` or `http-server`):
```powershell
npx serve d:\PyLambda\client
```

---

## ⚙️ Backend Connection Settings

- Default API URL: `http://127.0.0.1:8000`
- To change the URL, click the **Settings (gear icon)** in the top right of the navigation bar. The setting is persisted in your browser's `localStorage`.
- The live status pill checks `GET /health` and reports connectivity and roundtrip latency.

---

## 🔑 Features Implemented

### 1. Authentication Flows
- **Sign In (`POST /v1/auth/login`)**:
  - Validates email and password.
  - Automatically stores the JWT `access_token` and triggers a 30-minute visual expiration countdown.
- **Create Account (`POST /v1/auth/signup`)**:
  - Validates username (3–50 chars), email format, and password (8–128 chars).
  - Automatically authenticates upon successful creation.
- **Forgot Password (`POST /v1/auth/forgot-password`)**:
  - Dispatches password-reset email requests.
- **Reset Password (`POST /v1/auth/reset-password`)**:
  - Takes the verification token from email and your new password.

### 2. User Dashboard (Authenticated Area)
- **Profile & Identity (`GET /v1/auth/me`)**:
  - Displays authenticated user details (username, email) and active Bearer token with one-click clipboard copy.
- **Security & Change Password (`POST /v1/auth/me/change-password`)**:
  - Safely change passwords with validation ensuring the new password differs from the current password.
- **Phone Verification (`POST /v1/auth/me/verify-phone`)**:
  - Sanitizes and sends phone numbers formatted as pure integers matching backend Pydantic schemas.

### 3. Developer Console & Diagnostics
- **Live Endpoint Tester**:
  - Test `GET /`, `GET /health`, and `GET /v1/auth/me` with real-time status code, latency (ms), and formatted JSON output.

---

## 🧩 How to Add New Modules in the Future

The application was built modularly so you can add new features as the PyLambda backend expands:

1. **Add Sidebar Tab**:
   In [`index.html`](file:///d:/PyLambda/client/index.html), add a button with `data-tab="tab-lambdas"` inside the `<aside>` navigation:
   ```html
   <button data-tab="tab-lambdas" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium text-slate-400 hover:text-white">
     <i data-lucide="cpu" class="w-4 h-4"></i>
     <span>My Functions</span>
   </button>
   ```

2. **Add Tab Content Panel**:
   Inside `<div class="max-w-4xl mx-auto space-y-6">` in `index.html`:
   ```html
   <div id="tab-content-lambdas" class="tab-pane hidden space-y-6">
     <!-- Your module UI here -->
   </div>
   ```

3. **Interact with PyLambda Backend**:
   Use the exposed `window.PyLambdaClient` or `apiRequest()` inside [`app.js`](file:///d:/PyLambda/client/app.js):
   ```javascript
   const res = await window.PyLambdaClient.api('/v1/lambdas/list', { method: 'GET' });
   console.log(res.data);
   ```
