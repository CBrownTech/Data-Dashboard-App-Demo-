# Bank App — Frontend

A React + TypeScript single-page application for the Cognixia bank project. The frontend is intentionally decoupled from the backend: all state is currently managed locally with mock data so the UI can be built and tested independently before API integration.

---

## Tech Stack

| Library | Version | Role |
|---------|---------|------|
| **React 19** | `^19.2` | UI rendering |
| **TypeScript** | `~5.9` | Type safety across the entire codebase |
| **Vite 8** | `^8.0` | Dev server and production bundler |
| **Tailwind CSS 4** | `^4.2` | Utility-first styling |
| **React Router DOM 7** | `^7.13` | Client-side routing and navigation guards |
| **Redux Toolkit 2** | `^2.11` | Global state management |
| **React Redux 9** | `^9.2` | React bindings for Redux |
| **Axios** | `^1.13` | HTTP client — wired in once the backend is connected |
| **React Toastify 11** | `^11.0` | Non-blocking toast notifications for success/error feedback |

---

## Project Structure

```
src/
├── assets/          # Static images and icons
├── components/      # Reusable UI pieces
│   ├── Navbar.tsx           # Top navigation bar
│   ├── ProtectedRoute.tsx   # Redirects unauthenticated users to /signin
│   ├── AdminRoute.tsx       # Restricts routes to admin role only
│   ├── TransactionDrawer.tsx # Slide-in panel for transaction history
│   └── Spinner.tsx          # Loading indicator
├── pages/           # Full-page views — one per route
│   ├── Home.tsx
│   ├── About.tsx
│   ├── SignIn.tsx
│   ├── Register.tsx
│   ├── Dashboard.tsx        # Main user view: balance, deposit, withdraw, transfer
│   └── AdminDashboard.tsx   # Admin view: all users and account summaries
├── store/           # Redux state
│   ├── index.ts             # Root store — combines all slices
│   ├── authSlice.ts         # Login/logout state and role
│   └── accountSlice.ts      # Balance and transaction history
├── theme/           # Design tokens
│   └── colors.ts            # All color values (referenced by Tailwind and CSS)
├── App.tsx          # Root component — routing tree
├── index.css        # Tailwind base + @theme color variables
└── main.tsx         # Entry point — mounts <App> inside Redux <Provider>
```

---

## Architecture

### Routing

All routes are declared in `App.tsx`. Two route guard components control access:

- **`ProtectedRoute`** — checks `auth.isAuthenticated`; redirects to `/signin` if false.
- **`AdminRoute`** — checks `auth.role === 'admin'`; redirects to `/` for non-admins.

The Navbar is hidden on `/admin` so admins get a clean, separate full-screen interface.

### State Management (Redux Toolkit)

There are two slices:

**`authSlice`** — who is logged in:
- State: `isAuthenticated`, `username`, `role`, `error`
- Actions: `login`, `logout`
- Currently uses hardcoded mock accounts; will be replaced with `createAsyncThunk` + Axios calls to a backend auth endpoint.

**`accountSlice`** — account data for the logged-in user:
- State: `balance`, `transactions[]`, `error`
- Actions: `deposit`, `withdraw`, `transfer`, `clearError`
- Currently uses local mock state; will be replaced with async thunks calling `/api/accounts/:id`.

### Redux Data Flow

```
User action (button click)
  → dispatch(actionCreator(payload))
    → Thunk middleware (if async: Axios API call to backend)
    → Reducer updates state immutably
  → useSelector triggers re-render in subscribed components
```

When the backend is integrated, the synchronous reducers will be replaced by `createAsyncThunk` functions. The `extraReducers` block handles `pending` / `fulfilled` / `rejected` to show spinners and error toasts automatically.

### Theming

All colors are defined once in `src/index.css` as Tailwind 4 `@theme` CSS variables and mirrored in `src/theme/colors.ts`. No hardcoded hex values or arbitrary Tailwind color utilities are used in the codebase. To retheme the app, update those two files only.

### Notifications

React Toastify is mounted once in `App.tsx`. Any component triggers toasts with:

```ts
import { toast } from 'react-toastify'

toast.success('Deposit successful')
toast.error('Insufficient funds')
```

---

## Running Locally

```bash
cd bank_app/frontend
npm install
npm run dev        # starts at http://localhost:5173
```

---

## Mock vs. Real

| Feature | Status |
|---------|--------|
| Login / auth | Mock — hardcoded users in `authSlice.ts` |
| Balance & transactions | Mock — local Redux state in `accountSlice.ts` |
| Register form | UI complete — backend endpoint not yet connected |
| Routing & route guards | Real |
| Toast notifications | Real |
| Theming system | Real |
