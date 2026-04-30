# Rate Limiting

## Overview

Filiation processes sensitive financial data and serves accounts belonging to minors. Unmitigated API abuse — whether brute-force credential stuffing, scraping, or denial-of-service — could expose private family data or degrade service availability. This document describes every rate-limiting layer in the platform, why each limit exists, and how to implement it.

---

## Table of Contents

1. [Layered Defence Model](#layered-defence-model)
2. [Edge Layer (Cloudflare / Vercel)](#edge-layer-cloudflare--vercel)
3. [Firebase App Check (Pre-function Gate)](#firebase-app-check-pre-function-gate)
4. [Cloud Function Rate Limiting (Upstash Redis)](#cloud-function-rate-limiting-upstash-redis)
5. [Limit Table by Endpoint](#limit-table-by-endpoint)
6. [Implementation Guide](#implementation-guide)
7. [Client-Side Back-off](#client-side-back-off)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Testing Rate Limits](#testing-rate-limits)

---

## Layered Defence Model

```
Internet Request
      │
      ▼
[1] Edge WAF / CDN (Cloudflare or Vercel)
      │  Block obvious abusers, DDoS, IP reputation
      ▼
[2] Firebase App Check
      │  Reject requests missing a valid device attestation token
      ▼
[3] Firebase Auth (ID Token validation)
      │  Reject unauthenticated calls to protected functions
      ▼
[4] Upstash Rate Limit (Redis sliding window)
      │  Enforce per-user and per-IP quotas on each endpoint
      ▼
[5] Cloud Function Business Logic
```

No single layer is sufficient on its own. Each layer catches attacks that bypass the previous one.

---

## Edge Layer (Cloudflare / Vercel)

When Firebase Hosting is replaced by or fronted with Cloudflare or Vercel:

| Rule | Limit | Action |
|------|-------|--------|
| IP rate limit (all traffic) | 200 req / min / IP | Block for 1 minute |
| IP rate limit (auth paths) | 20 req / min / IP | Challenge (CAPTCHA) |
| IP reputation (Cloudflare Threat Score ≥ 25) | — | Challenge |
| Known bot / scraper user-agents | — | Block |
| Country block (if business requires) | — | Block |

Configure in `vercel.json` (`ratelimit` property) or Cloudflare WAF custom rules.

---

## Firebase App Check (Pre-function Gate)

App Check tokens are validated automatically by the Firebase SDK when App Check enforcement is enabled in the Firebase console. No additional code is required in Cloud Functions beyond enabling enforcement.

- Any request without a valid App Check token is rejected **before** the function handler runs.
- This eliminates automated scripts, curl, and server-side scrapers that do not have a browser attestation.

See [SECURITY.md § Firebase App Check](../SECURITY.md#firebase-app-check) for setup instructions.

---

## Cloud Function Rate Limiting (Upstash Redis)

### Why Upstash

- **Serverless-native**: Each Cloud Function invocation is stateless; Upstash provides a globally available Redis REST API that works without a persistent connection.
- **Sliding window algorithm**: Provides smoother enforcement than fixed windows (prevents burst at boundary).
- **Low latency**: Upstash Edge Cache keeps sub-10 ms lookups for most regions.
- **Cost-effective**: Free tier supports ~10,000 requests/day — sufficient for development; paid tiers scale linearly.

### Alternatives Considered

| Option | Verdict |
|--------|---------|
| In-memory Map in Cloud Function | ❌ Stateless functions — state lost on cold start |
| Firestore counter | ❌ Too slow (50–200 ms), expensive at scale |
| Firebase Realtime Database counter | ⚠ Faster but still adds latency; no sliding window built-in |
| Upstash Rate Limit (`@upstash/ratelimit`) | ✅ Chosen |

---

## Limit Table by Endpoint

| Cloud Function | Identifier | Algorithm | Limit | Window |
|----------------|------------|-----------|-------|--------|
| `auth/signIn` | `ip + uid` | Sliding window | 5 | 15 min |
| `auth/signUp` | `ip` | Sliding window | 3 | 15 min |
| `auth/passwordReset` | `ip + email` | Sliding window | 3 | 15 min |
| `auth/setCustomClaims` | `uid` (admin only) | Fixed window | 10 | 1 hour |
| `plaid/createLinkToken` | `uid` | Sliding window | 3 | 1 hour |
| `plaid/exchangePublicToken` | `uid` | Sliding window | 3 | 1 hour |
| `plaid/fetchTransactions` | `uid` | Sliding window | 30 | 1 hour |
| `plaid/fetchBalances` | `uid` | Sliding window | 60 | 1 hour |
| `requests/createRequest` | `uid` | Sliding window | 20 | 5 min |
| `requests/updateRequestStatus` | `uid` | Sliding window | 30 | 5 min |
| `tasks/assignTask` | `uid` | Sliding window | 20 | 5 min |
| `tasks/submitPlan` | `uid` | Sliding window | 10 | 10 min |
| `tasks/reviewPlan` | `uid` | Sliding window | 30 | 5 min |
| `admin/setRole` | `uid` (admin token) | Fixed window | 5 | 1 hour |
| All other callables (default) | `uid` | Sliding window | 60 | 1 min |

---

## Implementation Guide

### 1. Install Dependencies

```bash
npm install @upstash/ratelimit @upstash/redis
```

Check for known vulnerabilities before adding:

```bash
npm audit
```

### 2. Configure Upstash

1. Create a free Redis database at [upstash.com](https://upstash.com).
2. Copy the REST URL and REST token.
3. Store them as Firebase Secret Manager secrets:

```bash
firebase functions:secrets:set UPSTASH_REDIS_REST_URL
firebase functions:secrets:set UPSTASH_REDIS_REST_TOKEN
```

4. Reference in Cloud Function deployment:

```ts
// functions/src/index.ts
export const myFunction = functions
  .runWith({ secrets: ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN'] })
  .https.onCall(handler);
```

### 3. Rate Limit Middleware

```ts
// functions/src/rateLimit/middleware.ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';
import { HttpsError } from 'firebase-functions/v2/https';

let ratelimit: Ratelimit | null = null;

function getRateLimiter(limit: number, windowSeconds: number): Ratelimit {
  // Lazily initialise to avoid cold-start penalty when not needed
  const redis = new Redis({
    url: process.env.UPSTASH_REDIS_REST_URL!,
    token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  });
  return new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(limit, `${windowSeconds}s`),
    analytics: true,
    prefix: 'filiation',
  });
}

/**
 * Enforce a sliding-window rate limit.
 * Throws HttpsError('resource-exhausted') when the limit is exceeded.
 *
 * @param identifier - Unique key for this rate limit bucket (e.g. `uid`, `ip:uid`)
 * @param limit      - Maximum allowed requests
 * @param windowSeconds - Window duration in seconds
 */
export async function enforceRateLimit(
  identifier: string,
  limit: number,
  windowSeconds: number
): Promise<void> {
  const limiter = getRateLimiter(limit, windowSeconds);
  const { success, reset, remaining } = await limiter.limit(identifier);

  if (!success) {
    const retryAfterSeconds = Math.ceil((reset - Date.now()) / 1000);
    throw new HttpsError(
      'resource-exhausted',
      `Rate limit exceeded. Retry after ${retryAfterSeconds} seconds.`,
      { retryAfter: retryAfterSeconds }
    );
  }
}
```

### 4. Use in a Cloud Function

```ts
// functions/src/plaid/createLinkToken.ts
import { onCall } from 'firebase-functions/v2/https';
import { enforceRateLimit } from '../rateLimit/middleware';

export const createLinkToken = onCall(
  { secrets: ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'PLAID_CLIENT_ID', 'PLAID_SECRET'] },
  async (request) => {
    const uid = request.auth?.uid;
    if (!uid) throw new HttpsError('unauthenticated', 'Must be signed in.');

    // 3 link token creations per hour per user
    await enforceRateLimit(`plaid:linkToken:${uid}`, 3, 3600);

    // ... Plaid link token logic
  }
);
```

### 5. Auth Brute-Force Protection

For sign-in, combine the user's UID (if known from email lookup) **and** the client IP:

```ts
const clientIp = request.rawRequest.ip ?? 'unknown';
const identifier = `auth:signIn:${clientIp}:${emailHash}`;
await enforceRateLimit(identifier, 5, 900); // 5 per 15 min
```

> **Note:** Cloud Functions receive the client IP in `request.rawRequest.ip`. When behind Cloudflare, use the `CF-Connecting-IP` header instead.

---

## Client-Side Back-off

When the client receives a `resource-exhausted` error from a Cloud Function, it **must** respect the `retryAfter` value and display a user-friendly message:

```ts
try {
  await createLinkToken();
} catch (error: any) {
  if (error.code === 'functions/resource-exhausted') {
    const seconds = error.details?.retryAfter ?? 60;
    showToast(`Too many attempts. Please wait ${seconds} seconds.`);
    // Disable the button for `seconds` seconds
    setButtonDisabled(true);
    setTimeout(() => setButtonDisabled(false), seconds * 1000);
    return;
  }
  throw error;
}
```

Do **not** silently retry — this would make client-side back-off loops that hammer the server.

---

## Monitoring & Alerting

### Upstash Analytics

Enable `analytics: true` in the `Ratelimit` constructor. The Upstash console provides:
- Request counts per identifier prefix.
- Rate limit hit rate over time.
- Latency percentiles.

### Firebase Cloud Monitoring

Create an alerting policy for:
- `cloudfunctions.googleapis.com/function/execution_count` filtered by `status = RATE_LIMITED` (custom metric).
- Spike in `functions/resource-exhausted` errors > 100 per minute → PagerDuty / email alert.

### Custom Metric (Recommended)

Log rate-limit hits to a custom Cloud Monitoring metric:

```ts
// Inside enforceRateLimit when success === false
console.warn(JSON.stringify({
  severity: 'WARNING',
  message: 'RATE_LIMIT_HIT',
  identifier,
  limit,
  windowSeconds,
}));
```

Cloud Logging automatically ingests `console.warn` output from Cloud Functions. Create a log-based metric on `RATE_LIMIT_HIT` and alert on sustained spikes.

---

## Testing Rate Limits

### Unit Tests (Jest + Firebase Emulator)

```ts
// Stub Upstash in tests
jest.mock('@upstash/ratelimit', () => ({
  Ratelimit: jest.fn().mockImplementation(() => ({
    limit: jest.fn().mockResolvedValue({ success: false, reset: Date.now() + 60000, remaining: 0 }),
  })),
}));

it('throws resource-exhausted when rate limit hit', async () => {
  await expect(createLinkToken({ auth: { uid: 'test-user' } }))
    .rejects.toMatchObject({ code: 'resource-exhausted' });
});
```

### Integration Tests

Use the Firebase Emulator Suite with a real (free-tier) Upstash Redis test database to verify that:
1. The (n)th request within the window succeeds.
2. The (n+1)th request returns `resource-exhausted`.
3. Requests after the window resets succeed again.

### Load Testing

Use `k6` or `artillery` against the Firebase Emulator to validate that limits hold under concurrent load:

```bash
k6 run --vus 20 --duration 30s scripts/load-test-auth.js
```

Expected result: All requests beyond the configured limit return HTTP 429 / gRPC `RESOURCE_EXHAUSTED`.
