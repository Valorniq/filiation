# Architecture

## Overview

Filiation is a **family-oriented financial-literacy SaaS platform** that introduces children to personal finance through hands-on exposure to budgeting, rent simulation, credit cards, credit scores, transactions, taxes, logistics, and vacation planning. Adults supervise and approve; children learn by doing.

This document describes the current architecture, the target production architecture, all major subsystems, data models, and the migration path toward a more scalable Next.js-based stack.

---

## Table of Contents

1. [Current State](#current-state)
2. [Target Architecture](#target-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture (Firebase)](#backend-architecture-firebase)
5. [Data Model](#data-model)
6. [Role & Permission System](#role--permission-system)
7. [Feature Flag & Conditional Visibility System](#feature-flag--conditional-visibility-system)
8. [External Integrations](#external-integrations)
9. [P2P Requests & Task Workflow Engine](#p2p-requests--task-workflow-engine)
10. [Security Architecture](#security-architecture)
11. [Notification Architecture](#notification-architecture)
12. [Next.js Migration Path](#nextjs-migration-path)
13. [Infrastructure & Deployment](#infrastructure--deployment)
14. [Testing Strategy](#testing-strategy)

---

## Current State

```
Vite + React 19 + TypeScript (SPA)
│
├── src/
│   ├── App.tsx               — Router + ProtectedRoute + PublicRoute
│   ├── contexts/
│   │   └── AuthContext.tsx   — Firebase Auth + Firestore user profile sync
│   ├── views/
│   │   ├── AuthEntrance.tsx  — Sign-in / sign-up (Google OAuth only)
│   │   ├── FinancialHub.tsx  — Placeholder financial dashboard
│   │   ├── LogisticsHub.tsx  — Placeholder logistics dashboard
│   │   ├── CalendarHub.tsx   — Placeholder calendar
│   │   ├── SyncHub.tsx       — Placeholder cloud sync status
│   │   └── ProfileSettings.tsx — Basic profile editor
│   ├── components/
│   │   └── Layout.tsx        — Shell / navigation wrapper
│   └── lib/
│       ├── firebase.ts       — Firebase SDK initialisation
│       ├── notifications.ts  — FCM stub
│       └── utils.ts          — cn() utility
│
├── firestore.rules            — Basic rules (several production gaps — see SECURITY.md)
├── firebase-blueprint.json   — Entity & Firestore path definitions
└── firebase-applet-config.json — Firebase project config (⚠ should not be committed)
```

**Status:** Pre-alpha skeleton. No Cloud Functions, no Plaid, no rate limiting, no role system, no P2P workflow, no conditional UI.

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                          │
│                                                                  │
│  React 19 SPA (Vite)  or  Next.js App Router (future)           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ AuthContext  │  │ FamilyContext │  │ FeatureFlagContext  │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Views: Home · Finance · Logistics · Calendar · Sync   │     │
│  │         Settings · P2P Requests · Task Board           │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
          │ Firebase SDK (App Check enforced)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FIREBASE PLATFORM                           │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │  Auth        │  │  Firestore DB   │  │  Cloud Storage   │   │
│  │  (+ MFA)     │  │  (strict rules) │  │  (receipts, docs)│   │
│  └──────────────┘  └─────────────────┘  └──────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Cloud Functions (Node.js 20)               │   │
│  │                                                          │   │
│  │  auth-*         Rate-limited auth helpers                │   │
│  │  plaid-*        Link token, exchange, fetch data         │   │
│  │  requests-*     P2P request CRUD + approval workflow     │   │
│  │  tasks-*        Task assignment, submission, review      │   │
│  │  admin-*        Role assignment, family management       │   │
│  │  notifications- FCM push + in-app alerts                 │   │
│  │  scheduled-*    Daily Plaid sync, credit score refresh   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────┐                         │
│  │  App Check   │  │  Firebase Hosting│                         │
│  │  (reCAPTCHA) │  │  + security hdrs │                         │
│  └──────────────┘  └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│                                                                  │
│  Plaid API ──── bank/credit transactions, balances              │
│  Plaid Investments ── stock portfolio (read-only)               │
│  Upstash Redis ── sliding-window rate limiting                   │
│  Google KMS ──── Plaid token encryption                         │
│  Gemini API ──── AI financial coach / educational hints         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### Context Providers (Planned)

| Context | Purpose |
|---------|---------|
| `AuthContext` | Current user, Firebase User object, sign-in/out |
| `FamilyContext` | Active family document, member list, family settings |
| `RoleContext` | Derived adult/child role from custom claims |
| `FeatureFlagContext` | Real-time Firestore listener on `families/{id}/settings` — drives conditional UI |
| `NotificationContext` | FCM token management, in-app notification queue |

### Route Structure

```
/                       → Home dashboard (role-aware)
/auth                   → Sign-in / sign-up / consent flow
/finance                → Financial Hub (hidden for children when disabled)
/finance/credit         → Credit card & score (adults or enabled families)
/finance/budget         → Budgeting tool
/logistics              → Logistics Hub (ride requests, transport)
/calendar               → Shared family calendar
/requests               → P2P request list (child view: submit; adult view: approve)
/tasks                  → Task board (child view: my tasks; adult view: assign/review)
/tasks/:id/plan         → Vacation or project plan submission
/sync                   → Account linking & sync status (adults only)
/settings               → Profile, family, feature toggles (adult admin only)
```

### Conditional Rendering Pattern

Every feature gated by the family `FeatureFlag` must follow this pattern:

```tsx
const { flags } = useFeatureFlags();

if (!flags.bankLinking) return null;          // Feature disabled at family level
if (role === 'child' && !flags.showChildFinance) return null;

return <FinancialDashboard />;
```

---

## Backend Architecture (Firebase)

### Cloud Functions Organisation

```
functions/
├── src/
│   ├── auth/
│   │   ├── createUserProfile.ts     — onAuthCreate trigger
│   │   └── setCustomClaims.ts       — Admin-callable role setter
│   ├── plaid/
│   │   ├── createLinkToken.ts       — HTTPS callable
│   │   ├── exchangePublicToken.ts   — HTTPS callable
│   │   ├── fetchTransactions.ts     — HTTPS callable + scheduled
│   │   ├── fetchBalances.ts         — HTTPS callable
│   │   └── webhookHandler.ts        — HTTPS endpoint (Plaid → Firebase)
│   ├── requests/
│   │   ├── createRequest.ts         — Validate + write
│   │   └── updateRequestStatus.ts   — Approve / reject with notifications
│   ├── tasks/
│   │   ├── assignTask.ts
│   │   ├── submitPlan.ts
│   │   └── reviewPlan.ts
│   ├── notifications/
│   │   └── sendFcmNotification.ts
│   ├── rateLimit/
│   │   └── middleware.ts            — Upstash Rate Limit wrapper
│   └── audit/
│       └── logAction.ts             — Append-only audit log writer
```

### Rate Limiting Middleware

Every Cloud Function that handles user-initiated actions wraps execution with the rate-limit middleware before any business logic. See [`docs/rate-limiting.md`](docs/rate-limiting.md).

---

## Data Model

### Firestore Collections

```
/users/{uid}
  uid, email, displayName, photoURL, birthday, bio,
  phoneNumber, role*, familyId, notificationsEnabled,
  fcmToken, createdAt, updatedAt
  (* role stored as custom claim, mirrored here for display only)

/users/{uid}/private/linkedAccounts
  ownerId, plaidItemId, encryptedAccessToken, institutionName,
  accountIds[], lastSynced, status

/families/{familyId}
  name, code, adminId, memberUids[], createdAt

/families/{familyId}/settings
  features: {
    bankLinking: bool, creditScore: bool, rentSimulation: bool,
    stockPortfolio: bool, p2pRequests: bool, taskBoard: bool,
    vacationPlanning: bool, educationMode: bool
  }

/families/{familyId}/members/{uid}
  uid, role (adult|child), joinedAt, parentalConsentObtained,
  parentalConsentTimestamp, consentMethod

/families/{familyId}/transactions/{txId}
  amount, description, category, requesterId, status,
  plaidTransactionId?, createdAt, settledAt

/families/{familyId}/requests/{requestId}
  type (Ride|Transfer|IOU|Vacation|Task),
  requesterId, targetUid?, familyId,
  status (pending|approved|rejected|booked|completed),
  amount?, note, attachments[],
  reviewerId?, reviewNote?, reviewedAt,
  createdAt, updatedAt

/families/{familyId}/tasks/{taskId}
  title, description, assignedTo (child uid),
  assignedBy (adult uid), dueDate, status,
  submissionDocId?, createdAt

/families/{familyId}/plans/{planId}
  taskId, submittedBy, type (Vacation|Budget|Other),
  budgetBreakdown: { transportation, lodging, food, souvenirs, contingency },
  totalBudget, narrative, status,
  adultComments[], approvedAt, rejectedAt, bookedAt

/auditLog/{logId}
  actorUid, actorRole, action, targetUid, targetCollection,
  targetDocId, timestamp, ip, metadata
```

---

## Role & Permission System

### Custom Claims (set by Cloud Function, never by client)

```json
{
  "role": "adult",        // or "child"
  "familyId": "fam_abc",
  "emailVerified": true
}
```

### Permission Matrix

| Action | adult | child |
|--------|-------|-------|
| View financial dashboard | ✅ | 🔒 (flag) |
| Link bank account via Plaid | ✅ | ❌ |
| View credit score | ✅ | ❌ |
| View rent simulation | ✅ | 🔒 (flag) |
| Submit P2P request | ✅ | ✅ |
| Approve / reject P2P request | ✅ | ❌ |
| Assign task to child | ✅ | ❌ |
| Submit vacation plan | ❌ | ✅ |
| Review / approve plan | ✅ | ❌ |
| Modify family feature flags | ✅ (admin) | ❌ |
| Read audit log | ✅ (admin) | ❌ |

🔒 = controlled by family feature flag

---

## Feature Flag & Conditional Visibility System

The `families/{familyId}/settings` document is subscribed to via a real-time Firestore listener in `FeatureFlagContext`. Any change by an adult admin immediately propagates to all connected clients, hiding or showing features without a page reload.

### Feature Flags

| Flag | Description |
|------|-------------|
| `bankLinking` | Show/hide Plaid account linking in Settings and Finance Hub |
| `creditScore` | Show/hide credit score widget |
| `rentSimulation` | Show/hide simulated rent payment flow |
| `stockPortfolio` | Show/hide investment/watchlist panel |
| `p2pRequests` | Show/hide entire P2P request system |
| `taskBoard` | Show/hide task assignment and plan submission |
| `vacationPlanning` | Show/hide vacation budget planner within tasks |
| `educationMode` | Replace real data with simulated/demo data across all views |

---

## External Integrations

### Plaid

| Step | Where |
|------|-------|
| 1. Adult initiates in Settings | Client → `plaid/createLinkToken` Cloud Function |
| 2. Link token returned to client | Client opens Plaid Link widget |
| 3. User completes Plaid OAuth flow | Plaid returns `public_token` |
| 4. Client sends `public_token` to server | `plaid/exchangePublicToken` Cloud Function |
| 5. Server exchanges for `access_token` | Plaid `/item/public_token/exchange` |
| 6. `access_token` AES-256 encrypted | Stored in `/users/{uid}/private/linkedAccounts` |
| 7. Data fetch (on-demand or scheduled) | `plaid/fetchTransactions`, `plaid/fetchBalances` |
| 8. Webhooks | Plaid → `plaid/webhookHandler` → Firestore update |

**Client never receives the `access_token`.** All Plaid API calls happen server-side via the Admin SDK.

### Gemini AI Coach

The Gemini API (`@google/genai`) is used for:
- Educational explanations of transactions.
- Budget feedback for children's vacation plans.
- Credit score improvement tips.

Calls are made client-side using a scoped API key with strict quota limits, or moved server-side for production to prevent key exposure.

---

## P2P Requests & Task Workflow Engine

### Request Types

| Type | Initiator | Target | Amount | Flow |
|------|-----------|--------|--------|------|
| `Transfer` | Child | Parent or sibling | Yes | Pending → Approved/Rejected |
| `IOU` | Child | Parent | Yes | Pending → Approved/Rejected |
| `Ride` | Child | Parent | No | Pending → Confirmed → Completed |
| `Vacation` | Child (after task) | Family | Yes | Draft → Submitted → Reviewed → Approved/Rejected → Booked |
| `TaskPlan` | Child | Assigning adult | Optional | Draft → Submitted → Reviewed → Approved/Rejected |

### Vacation Planning Flow (Educational)

```
Adult assigns "Plan Family Vacation" task
          ↓
Child builds budget breakdown in /plans/{planId}:
  - Transportation: $X
  - Lodging: $X
  - Food: $X
  - Souvenirs: $X
  - Contingency: $X (min 10%)
          ↓
Child submits plan → status: 'submitted'
          ↓
Adult reviews, adds comments → status: 'approved' or 'rejected'
          ↓
Adult marks as booked (real-world execution) → status: 'booked'
          ↓
Simulated or real transactions logged in /families/{id}/transactions
          ↓
Audit log entry created
```

---

## Security Architecture

See [SECURITY.md](SECURITY.md) for full details.

Key points:
- Firebase App Check on all services.
- Upstash Redis sliding-window rate limits on all Cloud Functions.
- AES-256-GCM encryption for Plaid tokens.
- Role-based Firestore rules with custom claims.
- Append-only audit log.
- COPPA/GDPR compliance for child accounts.

---

## Notification Architecture

| Trigger | Channel | Recipient |
|---------|---------|-----------|
| New P2P request submitted | FCM push + in-app | Target user |
| Request approved / rejected | FCM push + in-app | Requester |
| New task assigned | FCM push + in-app | Child |
| Plan submitted for review | FCM push + in-app | Adult admin |
| Plaid sync complete | In-app | Adult |
| Plaid webhook (new transactions) | In-app | Adult |
| Login from new device | Email + in-app | Account owner |

FCM tokens are stored per user in `/users/{uid}` and refreshed via `onMessage` listener in the client.

---

## Next.js Migration Path

The current Vite SPA is sufficient for MVP. The project should migrate to **Next.js App Router** when:

- Cloud Functions become numerous and hard to manage separately.
- Server-side rendering improves SEO or time-to-first-byte noticeably.
- Rate limiting at the edge (via Next.js Middleware + Vercel/Cloudflare) becomes preferable.

### Migration Steps

1. Scaffold `apps/web` with `create-next-app --typescript --app` in a monorepo (Turborepo).
2. Move Firebase client SDK usage into `'use client'` components.
3. Move Cloud Function logic into Next.js **Route Handlers** (`app/api/...`).
4. Add Next.js Middleware for edge-level rate limiting and auth token validation.
5. Keep Firebase Firestore as the database (no migration required).
6. Migrate Firebase Hosting to Vercel (simpler Next.js deployment).
7. Retain Firebase Auth + App Check — both work with Next.js.

---

## Infrastructure & Deployment

| Service | Current | Target |
|---------|---------|--------|
| Hosting | Firebase Hosting | Firebase Hosting or Vercel |
| Database | Firestore | Firestore |
| Auth | Firebase Auth | Firebase Auth |
| Functions | None | Firebase Cloud Functions (Node 20) |
| Rate Limiting | None | Upstash Redis |
| Secrets | None | Firebase Secret Manager |
| CDN / WAF | None | Cloudflare or Vercel Edge |
| CI/CD | None | GitHub Actions |
| Monitoring | None | Cloud Monitoring + Firebase Alerting |

---

## Testing Strategy

| Layer | Tool | Coverage Target |
|-------|------|----------------|
| Firestore rules | `@firebase/rules-unit-testing` | 100% of rules |
| Cloud Functions (unit) | Jest + Firebase Emulator Suite | Core business logic |
| Cloud Functions (integration) | Firebase Emulator Suite | All HTTP callables |
| React components | Vitest + React Testing Library | Critical UI paths |
| E2E | Playwright | Auth, Plaid link mock, P2P flow |
| Security regression | `npm audit` + CodeQL | Every CI run |
