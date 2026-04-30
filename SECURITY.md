# Security Policy

## Overview

Filiation is a family-oriented SaaS platform that handles **financial data and accounts belonging to minors**. Security is a first-class concern. This document describes the security architecture, controls, and responsible-disclosure policy for this project.

---

## Table of Contents

1. [Threat Model](#threat-model)
2. [Firebase App Check](#firebase-app-check)
3. [Authentication & Session Security](#authentication--session-security)
4. [Rate Limiting](#rate-limiting)
5. [Input Validation & Sanitization](#input-validation--sanitization)
6. [HTTP Security Headers](#http-security-headers)
7. [Firestore Security Rules](#firestore-security-rules)
8. [Role-Based Access Control](#role-based-access-control)
9. [Encrypted Storage for Linked Accounts](#encrypted-storage-for-linked-accounts)
10. [Audit Logging](#audit-logging)
11. [COPPA & GDPR Compliance](#coppa--gdpr-compliance)
12. [Dependency & Supply-Chain Security](#dependency--supply-chain-security)
13. [Incident Response](#incident-response)
14. [Responsible Disclosure](#responsible-disclosure)

---

## Threat Model

| Actor | Risk | Mitigation |
|-------|------|------------|
| Unauthenticated public internet | Scraping, brute-force, abuse of Cloud Functions | App Check, rate limiting, auth guards |
| Authenticated attacker (non-family member) | Cross-family data access | Strict Firestore family-membership checks |
| Compromised child account | Accessing adult-only financial data | Role-based rules + custom claims |
| Malicious linked-account input | Stored XSS, injection | Input sanitization, CSP |
| Compromised Plaid access token | Unauthorized bank access | AES-256 encryption at rest, server-only access |
| Internal developer error | Accidental data exposure | Principle of least privilege, audit log |

---

## Firebase App Check

All Firebase services (Firestore, Cloud Functions, Storage) **must** be protected by App Check before production launch.

### Implementation Steps

1. Enable App Check in the Firebase console (`Project Settings → App Check`).
2. Register the web app using **reCAPTCHA Enterprise** (preferred for production) or **reCAPTCHA v3** (acceptable for MVP).
3. Initialise App Check in `src/lib/firebase.ts` before any other Firebase service call:

```ts
import { initializeAppCheck, ReCaptchaEnterpriseProvider } from 'firebase/app-check';

const appCheck = initializeAppCheck(app, {
  provider: new ReCaptchaEnterpriseProvider(import.meta.env.VITE_RECAPTCHA_SITE_KEY),
  isTokenAutoRefreshEnabled: true,
});
```

4. Enforce App Check in `firebase.json` / Firebase console for **all** services.
5. Store `VITE_RECAPTCHA_SITE_KEY` in `.env.local` — **never commit this file**.
6. For CI/CD pipelines, set `FIREBASE_APPCHECK_DEBUG_TOKEN` as a secret environment variable and use the `self.FIREBASE_APPCHECK_DEBUG_TOKEN` debug provider only in non-production builds.

### What App Check Prevents

- Direct API calls from curl, Postman, or non-app clients without a valid attestation token.
- Automated abuse of auth endpoints and Cloud Functions.

---

## Authentication & Session Security

### Rules

| Rule | Detail |
|------|--------|
| Brute-force lockout | Maximum **5 failed login attempts per 15-minute window** per IP address and per user UID (enforced via rate limiter on the sign-in Cloud Function wrapper). |
| Email verification | Require verified email before granting access to financial features. The `isEmailVerified()` Firestore helper must remove its `true` fallback before production. |
| Session token rotation | Firebase automatically rotates refresh tokens; ensure `signOut()` is called on suspected compromise. |
| MFA | Offer Firebase phone-based MFA for adult (admin) accounts — required before linking a bank account via Plaid. |
| OAuth scopes | Google Sign-In requests only `email` and `profile` — never `https://www.googleapis.com/auth/contacts` or broader scopes. |

---

## Rate Limiting

See [`docs/rate-limiting.md`](docs/rate-limiting.md) for full implementation details.

### Summary

| Layer | Tool | Limit |
|-------|------|-------|
| Authentication (sign-in, sign-up, password reset) | Upstash Rate Limit (Redis sliding window) | 5 req / 15 min / IP+UID |
| General Cloud Functions | Upstash Rate Limit | 60 req / min / UID |
| Plaid link token creation | Upstash Rate Limit | 3 req / hour / UID |
| Edge (CDN / WAF) | Cloudflare or Vercel Edge Config | 200 req / min / IP |

---

## Input Validation & Sanitization

### Client-Side

- All form inputs validated with a schema library (Zod recommended) before submission.
- No `dangerouslySetInnerHTML` usage without explicit DOMPurify sanitization.
- Currency and numeric inputs clamped to expected ranges.

### Server-Side (Cloud Functions)

- Re-validate every field received from the client — **never trust client data**.
- Use Zod or a similar runtime-schema validator on every Cloud Function entry point.
- Sanitize all string inputs that will be stored and later rendered (strip HTML, limit length).
- Validate Plaid `item_id` and `access_token` format before use.

### Firestore

- Document validation enforced in security rules (field types, sizes, allowed values).
- `isValidRequest()`, `isValidUser()` helper functions extended to cover all collections.

---

## HTTP Security Headers

The following headers must be set on every response. If hosted on Firebase Hosting, configure them in `firebase.json`:

```json
"headers": [
  {
    "source": "**",
    "headers": [
      { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" },
      { "key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self' https://www.gstatic.com https://www.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://*.firebaseio.com https://*.googleapis.com https://api.plaid.com; frame-ancestors 'none';" },
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "X-Frame-Options", "value": "DENY" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
      { "key": "Permissions-Policy", "value": "geolocation=(), microphone=(), camera=()" }
    ]
  }
]
```

> **Note:** Adjust the CSP `connect-src` directive to include your deployed Cloud Functions domain when known.

---

## Firestore Security Rules

### Current Gaps (must be fixed before production)

1. `isEmailVerified()` contains `|| true` fallback — **remove it**.
2. `families/{familyId}` `allow get` is open to **any** signed-in user — restrict to family members only.
3. `requests/{requestId}` `allow read` is open to **any** signed-in user — restrict to family members.
4. `linkedAccounts/{accountId}` uses `resource == null` which allows any authenticated user to create — validate `ownerId == request.auth.uid` on write.
5. Sub-collection wildcard `/{allSubcollections=**}` is overly broad — enumerate explicit sub-collections.

### Role Enforcement

Custom claims must be set by a trusted Cloud Function (not the client) and checked in rules:

```
function isAdult() {
  return isSignedIn() && request.auth.token.role == 'adult';
}
function isChild() {
  return isSignedIn() && request.auth.token.role == 'child';
}
```

- Financial details, Plaid tokens, credit score data → adults only.
- Children may read their own allowance, task assignments, and approved budget proposals.

---

## Role-Based Access Control

| Role | Firebase Custom Claim | Capabilities |
|------|-----------------------|--------------|
| `adult` | `role: "adult"` | Full family admin, link accounts, approve/reject requests, view all financial data |
| `child` | `role: "child"` | View own allowance, submit ride/transfer/vacation requests, complete tasks |

Custom claims are set exclusively by a privileged Cloud Function after email verification and optional MFA. Children under 13 require **verifiable parental consent** before account creation (see [COPPA section](#coppa--gdpr-compliance)).

---

## Encrypted Storage for Linked Accounts

Plaid `access_token` values and any other third-party credentials **must never be stored in plaintext**.

- Encrypt using **AES-256-GCM** via the `@google-cloud/kms` Cloud KMS service or a Cloud Functions environment variable wrapping a symmetric key.
- Store the encrypted blob in `/users/{userId}/private/linkedAccounts` (a sub-collection only readable server-side via the Admin SDK — **no client-side read rules**).
- The decrypted token is used only within Cloud Function execution context and is never returned to the client.

---

## Audit Logging

Every sensitive action must be recorded in a tamper-evident `auditLog` collection:

```
/auditLog/{logId}
  - actorUid: string
  - actorRole: string
  - action: string          // e.g. 'PLAID_LINK', 'APPROVE_REQUEST', 'ROLE_CHANGE'
  - targetUid: string | null
  - targetCollection: string
  - targetDocId: string
  - timestamp: Timestamp
  - ip: string              // populated server-side only
  - metadata: object        // action-specific detail
```

| Action | Logged |
|--------|--------|
| Sign-in / sign-out | ✅ |
| Failed sign-in attempt | ✅ |
| Plaid account linked / unlinked | ✅ |
| Financial request approved / rejected | ✅ |
| Role assignment changed | ✅ |
| Family member added / removed | ✅ |
| Child consent recorded | ✅ |
| Admin-level settings changed | ✅ |

Audit logs are write-only from the client (append-only Cloud Function) and readable only by adult admins of the same family.

---

## COPPA & GDPR Compliance

### COPPA (Children's Online Privacy Protection Act)

- Children under 13 **cannot** self-register. An adult must create a child account on their behalf.
- **Verifiable parental consent** (VPC) must be obtained and stored (e.g. signed consent form, credit card micro-verification) before the child's account is activated.
- Collect the **minimum required data** for children: display name, birthday (year only for UI), family membership — nothing else without explicit purpose.
- Provide a clear mechanism for parents to review and delete their child's data on request.
- No third-party advertising or behavioural tracking for child accounts.

### GDPR (General Data Protection Regulation)

- Provide a **Privacy Policy** and **Terms of Service** linked from the sign-up flow.
- Implement a data export endpoint (`/api/export-my-data`) for right-of-access requests.
- Implement a data deletion endpoint (`/api/delete-my-data`) for right-to-erasure requests.
- Store only the data required for the stated purpose (data minimisation).
- Document all data processors (Firebase, Plaid, Gemini API) in the Privacy Policy.
- Obtain explicit consent for each data category before collection.

---

## Dependency & Supply-Chain Security

- Run `npm audit` as part of every CI pipeline; fail the build on high/critical vulnerabilities.
- Pin major dependency versions and review `package-lock.json` diffs in PRs.
- Enable GitHub Dependabot or Renovate for automated security updates.
- Use the `@firebase/eslint-plugin-security-rules` (already present) in the linter pipeline.
- Never commit `.env`, `.env.local`, `firebase-applet-config.json` or any file containing secrets — add them to `.gitignore`.

---

## Incident Response

1. **Detect** — Cloud Function error rates, Firestore rule denials, and failed App Check tokens trigger alerts via Firebase Alerting or Cloud Monitoring.
2. **Contain** — Disable the affected Cloud Function via the Firebase console; revoke Plaid access tokens via the Plaid API.
3. **Notify** — Notify affected families within 72 hours of confirmed breach (GDPR requirement).
4. **Remediate** — Patch, rotate secrets, re-deploy.
5. **Post-mortem** — Document root cause and preventative measures.

---

## Responsible Disclosure

If you discover a security vulnerability in Filiation, please **do not** open a public GitHub issue.

Instead, email **security@[your-domain].com** with:

- A description of the vulnerability.
- Steps to reproduce.
- Potential impact assessment.
- Any suggested mitigation.

We will acknowledge receipt within **48 hours** and aim to release a fix within **30 days** for critical issues. We follow a coordinated disclosure policy and will credit researchers who report valid issues (unless they prefer anonymity).
