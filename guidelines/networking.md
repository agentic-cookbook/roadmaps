# Networking Guidelines

Cross-platform conventions for client-server communication. Covers API design, resilience,
caching, offline support, and real-time patterns.

## §10.1. References

1. [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
2. [Google API Design Guide](https://cloud.google.com/apis/design)
3. [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/)
4. [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
5. [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)

## §10.2. API Design

Use REST with consistent conventions. Follow the platform API guidelines (Microsoft, Google,
Zalando) for details — the essentials below are consensus across all three.

**URL conventions:**
- Lowercase with hyphens: `/order-items` not `/orderItems`
- Plural nouns for collections: `/users`, `/orders`
- Shallow nesting (max 2 levels): `/users/{id}/orders`
- No verbs in URLs — the HTTP method is the verb
- No trailing slashes
- Query params for filtering/sorting: `/users?status=active&sort=-created_at`

**HTTP methods:**

| Method | Semantics | Idempotent | Success Code |
|--------|-----------|------------|-------------|
| GET | Read | Yes | 200 |
| POST | Create | No | 201 + Location |
| PUT | Full replace | Yes | 200 |
| PATCH | Partial update | No | 200 |
| DELETE | Remove | Yes | 204 (no body) |

**Status codes — use the right one:**
- **200** OK — **201** Created — **204** No Content — **202** Accepted (async)
- **400** Bad Request — **401** Unauthorized — **403** Forbidden — **404** Not Found
- **409** Conflict — **422** Unprocessable Entity — **429** Too Many Requests
- **500** Internal Server Error — **503** Service Unavailable

**Versioning:** URL path versioning (`/v1/users`). Simple, explicit, industry consensus. Bump
major version only for breaking changes.

## §10.3. Error Responses

Use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457) format with
`Content-Type: application/problem+json`:

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request body contains 2 validation errors.",
  "instance": "/orders/abc-123",
  "errors": [
    { "field": "email", "message": "Must be a valid email address" },
    { "field": "age", "message": "Must be >= 0" }
  ]
}
```

- **type** (URI) — machine-readable error identifier
- **title** — short human-readable summary (stable across occurrences)
- **status** — HTTP status code (mirrors response)
- **detail** — explanation specific to this occurrence
- **instance** — identifies the specific request
- Add extension fields (`errors`, `trace_id`) as needed

## §10.4. Pagination

Prefer **cursor pagination** for most APIs — stable under concurrent mutations, consistent
performance at any depth. Use offset pagination only when users need page numbers or data
is relatively static.

**Cursor response:**
```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true
  }
}
```

**Offset response:**
```json
{
  "data": [ ... ],
  "pagination": {
    "offset": 20,
    "limit": 10,
    "total": 142
  }
}
```

References:
- [Google AIP-158: Pagination](https://google.aip.dev/158)
- [Zalando: Pagination](https://opensource.zalando.com/restful-api-guidelines/#pagination)

## §10.5. Retry and Resilience

Not every failure is permanent. Retry transient failures with exponential backoff and jitter.

**Exponential backoff with full jitter:**
```
delay = random(0, min(max_delay, base * 2^attempt))
```

| Parameter | Default |
|-----------|---------|
| Base delay | 1 second |
| Max delay cap | 30 seconds |
| Max retries | 3-5 (idempotent), 0 (non-idempotent unless safe) |

**Retryable status codes:** 408, 429, 500 (idempotent only), 502, 503, 504.
Always respect `Retry-After` header on 429 and 503.

**Never retry:** 400, 401, 403, 404, 409, 422 — these are deterministic failures.

**Circuit breaker** for cascading failure prevention:
- Track failure rate over a sliding window (e.g., 10 requests)
- Open circuit when failure rate exceeds threshold (e.g., 50%)
- Stay open for a cooldown period (e.g., 30 seconds)
- Half-open: allow 1 probe request to test recovery

References:
- [AWS: Exponential Backoff and Jitter](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- [Microsoft: Transient Fault Handling](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults)
- [Microsoft: Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

## §10.6. Timeouts

Always set both connection and read timeouts. Never use infinite timeouts.

| Timeout | Purpose | Default |
|---------|---------|---------|
| Connection | TCP + TLS handshake | 10 seconds |
| Read / Response | Time to first byte | 30 seconds |
| Total / Request | Entire lifecycle including retries | 60-120 seconds |

For long-running operations, use **202 Accepted** + polling pattern instead of extending
timeouts.

## §10.7. Caching

Use HTTP caching headers. The server controls cache policy; the client honors it.

**Immutable assets** (versioned JS/CSS/images):
```
Cache-Control: public, max-age=31536000, immutable
```

**Dynamic but cacheable** (API responses):
```
Cache-Control: private, max-age=60
```

**Never cache** (sensitive data, mutations):
```
Cache-Control: no-store
```

**Conditional requests** — use ETags to avoid re-downloading unchanged data:
1. Server sends `ETag: "abc123"`
2. Client revalidates with `If-None-Match: "abc123"`
3. Server responds 304 Not Modified (no body) or 200 with new data

**Client-side invalidation:**
- After mutations (POST/PUT/DELETE), invalidate related cache entries
- Stale-while-revalidate: serve cached data immediately, refresh in background
- Framework support: React Query, SWR, Apollo Client all handle this natively

References:
- [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)
- [web.dev: HTTP Cache](https://web.dev/articles/http-cache)
- [MDN: Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)

## §10.8. Offline and Connectivity

For apps that must work offline, design for local-first with background sync.

**Patterns (in order of complexity):**
1. **Optimistic updates** — apply changes to local UI immediately, sync in background. Roll
   back on server failure. Sufficient for most apps.
2. **Queue-based sync** — mutations go into an outbox queue, drained when connectivity returns.
   Failed items stay in queue for retry.
3. **Conflict resolution** — use ETags or version numbers to detect conflicts. Return 409 with
   both versions. Simple apps use server-wins; collaborative apps need merge UI or CRDTs.

**Practical defaults:**
- Track `last_synced_at` per entity for delta sync
- Show clear connectivity status to the user
- Queue mutations locally; never silently discard user work
- Test offline scenarios — airplane mode, flaky connections, long offline periods

References:
- [web.dev: Offline Cookbook](https://web.dev/articles/offline-cookbook)
- [CRDTs](https://crdt.tech/)

## §10.9. Rate Limiting

Respect server rate limits. Handle 429 responses gracefully.

- Always honor the `Retry-After` header (seconds or HTTP-date)
- If no `Retry-After`, use exponential backoff (see Retry section)
- Track `RateLimit-Remaining` headers proactively — slow down before hitting 429
- Queue and batch requests at the allowed rate rather than fire-and-retry

References:
- [RFC 6585: 429 Too Many Requests](https://www.rfc-editor.org/rfc/rfc6585)

## §10.10. Real-Time Communication

Choose the simplest technique that meets your needs.

| Technique | Direction | Use When |
|-----------|-----------|----------|
| Polling | Client-pull | Low frequency (<1/min), simplicity paramount |
| SSE | Server-push | Notifications, live feeds, dashboards, progress |
| WebSocket | Bidirectional | Chat, multiplayer, collaborative editing |

**Start with SSE** for server-push — it has built-in reconnection, works over standard HTTP,
and is sufficient for 80%+ of "real-time" needs. Only move to WebSocket if you need
bidirectional streaming. Use polling as a fallback for very low frequency updates.

References:
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [MDN: WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [RFC 6455: WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455)
