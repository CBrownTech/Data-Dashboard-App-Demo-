# Validation & Business Rules

This document lists every business rule in the app and where it is enforced.

There are three enforcement layers:

| Layer | Role | Can be bypassed by? |
|-------|------|---------------------|
| **Database** | Structural integrity — rejects invalid data shapes regardless of who sent them | Nobody — not even a direct SQL insert |
| **Backend (API)** | Business rules — logic the database has no way to express | A crafted request if the API layer were removed |
| **Frontend** | UX convenience — prevents accidental bad input in the browser | Anyone using Postman or curl |

The database is the last line of defence for structural rules. The backend is the last line of defence for business rules. The frontend is not a security boundary.

---

## Account Creation (`POST /accounts`)

| Rule | Enforced by |
|------|-------------|
| Email must be unique | **Database** — `UNIQUE` constraint on `users.email`. Returns an `IntegrityError` caught as HTTP 400. |
| `accountType` must be `CHECKING` or `SAVINGS` | **Database** — `ENUM('CHECKING', 'SAVINGS') NOT NULL` column. **Backend** — checked before the insert and raises `ValueError` → HTTP 400. |
| Password is optional | **Backend** — `password_hash` is nullable. Users created without a password cannot log in but their account still exists. |

---

## Login (`POST /login`)

| Rule | Enforced by |
|------|-------------|
| Email must exist | **Backend** — `get_user_by_email` returns `None` → `"Invalid credentials"` (HTTP 401) |
| User must have a password set | **Backend** — `password_hash` being `NULL` → `"Invalid credentials"` (HTTP 401). Prevents Postman-created users without a password from logging in. |
| Password must match the stored hash | **Backend** — `check_password_hash` → `"Invalid credentials"` (HTTP 401) |
| User must not be soft-deleted | **Backend** — `is_deleted` flag check → `"Account is deactivated"` (HTTP 401) |

---

## Deposit (`POST /accounts/<id>/deposit`)

| Rule | Enforced by |
|------|-------------|
| Account must exist | **Backend** → `"Account not found"` (HTTP 400) |
| Amount must be positive | **Backend** → `"Deposit amount must be positive"` (HTTP 400) |

---

## Withdraw (`POST /accounts/<id>/withdraw`)

| Rule | Enforced by |
|------|-------------|
| Account must exist | **Backend** → `"Account not found"` (HTTP 400) |
| Amount must be positive | **Backend** → `"Withdrawal amount must be positive"` (HTTP 400) |
| Balance must cover the amount | **Backend** → `"Insufficient funds"` (HTTP 400) |

---

## Transfer (`POST /accounts/<id>/transfer`)

| Rule | Enforced by |
|------|-------------|
| Sender account must exist | **Backend** → `"Sender account not found"` (HTTP 400) |
| Recipient account must exist | **Backend** → `"Recipient account not found"` (HTTP 400) |
| Sender and recipient must be different | **Backend** → `"Cannot transfer to the same account"` (HTTP 400) |
| Amount must be positive | **Backend** → `"Transfer amount must be positive"` (HTTP 400) |
| Sender must have sufficient funds | **Backend** → `"Insufficient funds"` (HTTP 400) |
| All four writes are atomic | **Backend** — single SQLAlchemy session; full rollback if anything fails |

---

## Soft Delete (`DELETE /accounts/<id>`)

| Rule | Enforced by |
|------|-------------|
| Account must exist | **Backend** → `"Account not found"` (HTTP 404) |
| User must exist | **Backend** → `"User not found"` (HTTP 404) |
| No data is physically removed | **Backend / Design** — only `is_deleted` and `deleted_at` are updated |

---

## Known Gaps

These rules are **not currently enforced**:

| Gap | Notes |
|-----|-------|
| No minimum balance | Accounts can be withdrawn to $0.00 |
| No maximum deposit or transfer limit | No ceiling on transaction size |
| Deposit/withdraw still works on a soft-deleted user's account | Only login is blocked by soft-delete, not transactions |
| `amount` must be a number | **Backend** — `parse_amount()` in `routes.py` catches missing or non-numeric values → `"amount is required"` / `"amount must be a number"` (HTTP 400) |
