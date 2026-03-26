# Security Guidelines

Cross-platform security conventions for client-server applications. Covers authentication,
authorization, transport security, input validation, data protection, and dependency security.

These guidelines supplement general.md rule 16 (Privacy and Security by Default). See
platform-specific files for secure storage implementation details per platform.

## References

1. [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
2. [OWASP Mobile Top 10 (2024)](https://owasp.org/www-project-mobile-top-10/)
3. [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
4. [OWASP MASVS](https://mas.owasp.org/MASVS/) / [MASTG](https://mas.owasp.org/MASTG/)
5. [Mozilla Server Side TLS](https://wiki.mozilla.org/Security/Server_Side_TLS)

## Authentication

Use OAuth 2.0 / OpenID Connect with PKCE for all public clients. The Implicit flow is
deprecated — OAuth 2.1 removes it entirely.

**Per-platform auth flow:**
- **Native apps (iOS/Android/Windows):** Authorization Code + PKCE via the system browser
  (`ASWebAuthenticationSession`, Custom Tabs, `WebAuthenticationBroker`). Never embed a
  WebView for auth — the app can intercept credentials.
- **SPAs:** Authorization Code + PKCE. Consider a Backend-for-Frontend (BFF) pattern where
  the SPA never handles tokens directly — the BFF holds tokens server-side in HttpOnly cookies.
- **Server-to-server:** Client Credentials flow.

**Session management:**
- Short-lived access tokens (5-15 minutes)
- Refresh token rotation — each use issues a new refresh token and invalidates the old one.
  Detect reuse of a revoked refresh token and invalidate the entire token family.
- Absolute session timeouts server-side

References:
- [RFC 7636: PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 8252: OAuth for Native Apps](https://datatracker.ietf.org/doc/html/rfc8252)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)

## Token Handling

**Access tokens:** Short-lived (5-15 min). Include only necessary claims — no PII in JWTs
that transit untrusted parties.

**Refresh tokens:** Longer-lived but bound to client. Use rotation (see Authentication above).
Store server-side when possible.

**Token refresh strategy:**
- Proactive refresh before expiry (e.g., at 75% of TTL)
- Queue concurrent requests during refresh to avoid race conditions
- Retry with backoff on refresh failure

**Secure storage per platform** (see also general.md rule 16.3):
- **Apple:** Keychain Services
- **Android:** EncryptedSharedPreferences / Android Keystore
- **Windows:** DPAPI (`ProtectedData`)
- **Web:** HttpOnly Secure SameSite cookies (never localStorage)

**Never do these:**
- Store tokens in `localStorage` or `sessionStorage` (XSS-accessible)
- Put tokens in URL query parameters (logged in server logs, browser history, referrer headers)
- Use `alg: none` in JWTs — always validate the `alg` header server-side against an allowlist
- Trust client-supplied JWT claims for authorization without server-side verification

References:
- [RFC 6750: Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [RFC 7519: JSON Web Tokens](https://datatracker.ietf.org/doc/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

## Authorization

**Server-side authorization is the only real authorization.** Client-side checks (hiding
buttons, disabling fields) are UX conveniences — never security controls.

- **Deny by default** — if no explicit permission grants access, deny. Every new endpoint
  starts locked down.
- **Least privilege** — request minimum scopes. Each endpoint enforces its own permission check.
- **RBAC** — define roles with minimal permissions. Prefer fine-grained permissions composed
  into roles over monolithic role checks.
- **Broken Object Level Authorization (BOLA)** — the #1 API security risk (OWASP API Top 10).
  Always verify the authenticated user has access to the specific resource ID requested.
  Never assume "if they know the ID, they have access."

References:
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)

## Transport Security

**TLS 1.2 minimum**, prefer TLS 1.3. Disable TLS 1.0 and 1.1 entirely.

**HSTS:** Enable on all production domains:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
Submit to the [HSTS preload list](https://hstspreload.org/).

**Certificate pinning — use with caution:**
- Pin to the intermediate CA, not the leaf (leaf certificates rotate)
- Acceptable for mobile apps; generally avoid for web (HPKP is deprecated)
- Always include backup pins and have a recovery plan
- Consider Certificate Transparency monitoring as an alternative

**Cipher suites:** Use Mozilla's "Intermediate" or "Modern" TLS configuration. Prefer AEAD
ciphers (AES-GCM, ChaCha20-Poly1305).

References:
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html)
- [Mozilla Server Side TLS](https://wiki.mozilla.org/Security/Server_Side_TLS)
- [RFC 8446: TLS 1.3](https://datatracker.ietf.org/doc/html/rfc8446)

## CORS

Cross-Origin Resource Sharing — get it right or don't enable it.

- **Never reflect the Origin header** back as `Access-Control-Allow-Origin`. Maintain an
  explicit allowlist of origins.
- **Never use `*` with credentials** — browsers block this, and attempting it reveals a
  design misunderstanding.
- **Preflight caching:** Set `Access-Control-Max-Age: 86400` to reduce preflight overhead.
- **Minimize exposed headers:** Only what the client actually needs.

**Common misconfigurations:**
- Wildcard origin with credentials
- Regex matching without anchoring (`evil-example.com` matching `example.com`)
- Allowing `null` origin (exploitable via sandboxed iframes)
- Overly broad allowed methods and headers

References:
- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP: CORS Testing](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing)

## Content Security Policy

Prevent XSS and injection with a strict CSP. Web apps only.

- **Start strict:** `default-src 'none'` then add only what is needed
- **Nonce-based scripts:** `script-src 'nonce-{random}' 'strict-dynamic'` — more secure than
  domain allowlisting (bypassable via JSONP/CDN scripts)
- **Never use** `'unsafe-inline'` or `'unsafe-eval'` for script-src
- **`frame-ancestors 'self'`** to prevent clickjacking (replaces X-Frame-Options)
- **Deploy in report-only mode first** (`Content-Security-Policy-Report-Only`) to find
  violations before enforcing

References:
- [MDN: CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [Google CSP Evaluator](https://csp-evaluator.withgoogle.com/)

## Input Validation

**Never trust client input.** Client-side validation is a UX feature, not a security control.
All validation must be duplicated server-side.

- **Allowlists over denylists** — define what is valid, not what is invalid. Denylists have gaps.
- **Validate, sanitize, escape** — in that order. Validation rejects. Sanitization cleans.
  Escaping is context-specific output encoding (HTML, URL, SQL, JS).
- **Parameterized queries** — the only reliable defense against SQL injection. Never concatenate
  user input into queries.
- **Output encoding** — context-dependent: HTML-encode for HTML, URL-encode for URLs. Use
  framework auto-escaping (React JSX, Django templates) and understand when it does NOT apply
  (e.g., raw HTML insertion APIs — always sanitize with a library like DOMPurify first).
- **File uploads** — validate MIME type server-side (not just extension). Limit size. Store
  outside web root. Never serve with original filename or from the same origin.

References:
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)

## Sensitive Data

Minimize what you collect, encrypt what you keep, never log what you shouldn't.

- **Data minimization** — APIs return only fields the client needs. Use explicit response DTOs,
  never dump database models directly.
- **PII classification** — classify data by sensitivity (public, internal, PII, sensitive PII).
  Apply controls proportional to tier.
- **Field-level encryption** — encrypt highly sensitive fields (SSN, payment info) at the
  application level with a KMS (AWS KMS, Azure Key Vault, GCP KMS). Separate from database-level
  encryption.
- **No PII in logs** — never log tokens, passwords, credit card numbers, or PII. Mask/redact
  in all log outputs, including debug level. See general.md rule 16.4.
- **No internals in API responses** — never expose internal IDs, stack traces, or database
  error messages in production. Return generic errors with correlation IDs.
- **Cache-Control: no-store** on responses containing sensitive data.

References:
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST SP 800-122: PII Guide](https://csrc.nist.gov/publications/detail/sp/800-122/final)

## Dependency Security

Your dependencies are your attack surface. Manage them actively.

- **Lockfiles are mandatory** — `package-lock.json`, `Podfile.lock`, `gradle.lockfile`,
  `poetry.lock`, `Cargo.lock`, `packages.lock.json`. Commit them. Use `--frozen-lockfile` /
  `npm ci` / `dotnet restore --locked-mode` in CI.
- **Automated scanning** — run `npm audit`, `pip-audit`, Dependabot, Snyk, or `dotnet list
  package --vulnerable` in CI. Fail the build on critical/high vulnerabilities.
- **Pin dependencies** — exact versions or narrow ranges. No `*` or overly broad semver.
- **Subresource Integrity (SRI)** — for any CDN-hosted scripts/styles, use `integrity`
  attributes with SHA-384/SHA-512 hashes.
- **Watch for supply chain attacks** — typosquatting, maintainer compromise, malicious
  post-install scripts, dependency confusion (internal/public name collisions).

References:
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [SLSA Framework](https://slsa.dev/)
- [Sigstore](https://www.sigstore.dev/)

## Security Headers Checklist

Every web application should set these response headers:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'none'; script-src 'nonce-{random}' 'strict-dynamic'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store  (for sensitive responses)
```
