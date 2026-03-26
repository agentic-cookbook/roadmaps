# Guidelines Index

Complete index of all rules, principles, and conventions across all guideline files.
Use `§X.Y` notation to cross-reference any rule. Search this file to find where a topic is covered.

---

## §1. General Coding Guidelines (`general.md`)

| § | Rule | Keywords |
|---|------|----------|
| §1.1 | Prefer native controls and libraries | native, platform, built-in, framework |
| §1.2 | For novel components, prefer proven open-source solutions | open-source, library, custom |
| §1.3 | Surface all design decisions | decisions, approval, LLM, consistency |
| §1.4 | No blocking the main thread | async, await, concurrency, background, UI thread |
| §1.5 | Always show progress | spinner, skeleton, shimmer, progress bar, loading |
| §1.6 | Comprehensive unit testing | tests, unit tests, edge cases, test file |
| §1.7 | Small, atomic commits | commits, git, one change |
| §1.8 | Post-generation verification | build, test, lint, accessibility audit, code review |
| §1.9 | Instrumented logging | logging, os.log, Timber, ILogger, structured |
| §1.10 | Deep linking | deep link, URL, Universal Links, App Links, protocol activation |
| §1.11 | Scriptable and automatable | AppIntents, AppActions, Shortcuts, automation |
| §1.12 | Accessibility from day one | accessibility, VoiceOver, TalkBack, Narrator, WCAG, contrast, focus |
| §1.13 | Localizability | localization, i18n, strings, .xcstrings, strings.xml, .resw |
| §1.14 | RTL layout support | RTL, right-to-left, leading, trailing, FlowDirection |
| §1.15 | Respect accessibility display options | reduced motion, high contrast, bold text, grayscale |
| §1.16 | Privacy and security by default | privacy, security, PII, TLS, consent |
| §1.16.1 | Data minimization | data minimization, on-device |
| §1.16.2 | Consent | consent, opt-in, deny |
| §1.16.3 | Secure storage | Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly |
| §1.16.4 | No PII logging | PII, logging, personally identifiable |
| §1.16.5 | TLS only | TLS, HTTPS, encryption |
| §1.16.6 | Input sanitization | sanitization, XSS, injection |
| §1.17 | Feature flags | feature flags, FeatureFlagProvider, gating |
| §1.18 | Analytics | analytics, AnalyticsProvider, tracking |
| §1.19 | A/B testing | A/B testing, ExperimentProvider, variants |
| §1.20 | Debug mode | debug panel, flag overrides, environment info |
| §1.21 | Linting from day one | linting, SwiftLint, ktlint, ESLint, Roslyn, dotnet format |

## §2. Engineering Principles (`engineering-principles.md`)

| § | Principle | Keywords |
|---|-----------|----------|
| §2.1 | Simplicity | simplicity, complexity, concerns |
| §2.2 | Make It Work, Make It Right, Make It Fast | correctness, refactor, optimize, phases |
| §2.3 | Composition over inheritance | composition, inheritance, protocols, interfaces |
| §2.4 | Dependency injection | DI, injection, constructor, service locator |
| §2.5 | Immutability by default | immutability, let, val, const, mutable |
| §2.6 | Fail fast | fail fast, assertions, preconditions, typed errors |
| §2.7 | Idempotency | idempotent, debounce, retry, duplicate |
| §2.8 | Design for deletion | deletion, disposable, maintenance, liability |
| §2.9 | YAGNI | YAGNI, speculative, premature, requirements |
| §2.10 | Explicit over implicit | explicit, implicit, hidden, magic |
| §2.11 | Small, reversible decisions | reversible, incremental, binding |
| §2.12 | Tight feedback loops | feedback, tests, deploy, iteration |
| §2.13 | Separation of concerns | separation, single responsibility, module |
| §2.14 | Principle of least astonishment | least astonishment, expectations, surprise |
| §2.15 | Manage complexity through boundaries | boundaries, ports, adapters, hexagonal |
| §2.16 | Meta-Principle: Optimize for Change | change, future, cost |

## §3. Swift / SwiftUI / AppKit (`swift.md`)

| § | Section | Keywords |
|---|---------|----------|
| §3.1 | References | Swift API Design Guidelines, SwiftUI Performance |
| §3.2 | Logging | os.log, Logger, subsystem, category |
| §3.3 | Secure Storage | Keychain, UserDefaults, secrets |
| §3.4 | Localization | String(localized:), NSLocalizedString, .xcstrings |
| §3.5 | Linting and Formatting | SwiftLint, swift-format |
| §3.6 | Shortcuts and Automation | AppIntents, Shortcuts, Siri, AppleScript |
| §3.7 | Previews | #Preview, SwiftUI, render |
| §3.8 | Dynamic Type | Dynamic Type, font sizes, text scaling |
| §3.9 | Accessibility Environment Values | reduceMotion, reduceTransparency, colorSchemeContrast |
| §3.10 | Concurrency | async/await, Task, actors, @MainActor |
| §3.11 | Privacy | App Tracking Transparency, Privacy Report, NSUsageDescription |
| §3.12 | Feature Flags | protocol, UserDefaults |
| §3.13 | Analytics | protocol, os.log |

## §4. Kotlin / Compose / Ktor (`kotlin.md`)

| § | Section | Keywords |
|---|---------|----------|
| §4.1 | References | Kotlin Conventions, Material Design 3, Architecture |
| §4.2 | Logging | Timber, android.util.Log |
| §4.3 | Concurrency | Coroutines, Dispatchers.IO, viewModelScope |
| §4.4 | Secure Storage | EncryptedSharedPreferences, Android Keystore |
| §4.5 | Localization | strings.xml, stringResource, R.string |
| §4.6 | Linting and Formatting | ktlint, .editorconfig |
| §4.7 | Shortcuts and Automation | AppActions, Google Assistant, Intent |
| §4.8 | Previews | @Preview, Compose |
| §4.9 | Font Scaling | fontScale, Configuration, 2x |
| §4.10 | Accessibility Settings | animator_duration_scale, TalkBack, Switch Access |
| §4.11 | Privacy | scoped storage, permissions, rationale |
| §4.12 | Feature Flags | interface, SharedPreferences |
| §4.13 | Analytics | interface, Timber |
| §4.14 | RTL Support | supportsRtl, start/end |
| §4.15 | Immutability | val, data class, StateFlow |

## §5. TypeScript / React / Web (`typescript.md`)

| § | Section | Keywords |
|---|---------|----------|
| §5.1 | Linting and Formatting | ESLint, Prettier, Stylelint |
| §5.2 | Accessibility References | WCAG 2.1, WAI-ARIA |
| §5.3 | Accessibility CSS Media Queries | prefers-reduced-motion, prefers-contrast, forced-colors |
| §5.4 | Security | CSP, HttpOnly, cookies, sanitization, Do Not Track |
| §5.5 | Localization | react-intl, i18next, FormatJS, message catalogs |
| §5.6 | RTL Layout Support | CSS logical properties, margin-inline-start, dir |
| §5.7 | Testing | Playwright, E2E, visual regression, Storybook |
| §5.8 | Concurrency | Promise, async/await, Web Workers |
| §5.9 | Deep Linking | URL routing, shareable URL |
| §5.10 | Debug Mode | /debug, Ctrl+Shift+D, NODE_ENV |
| §5.11 | Feature Flags | interface, localStorage |
| §5.12 | Analytics | interface, console |
| §5.13 | Immutability | const, useState |

## §6. Python (`python.md`)

| § | Section | Keywords |
|---|---------|----------|
| §6.1 | No external dependencies in core libraries | stdlib, roadmap_lib, portable |
| §6.2 | Testing | pytest, regression test, demo port 9888 |
| §6.3 | Type hints | type hints, annotations, Python 3.9 |
| §6.4 | File paths | pathlib, Path, os.path |
| §6.5 | YAML frontmatter | frontmatter, parse, roadmap_lib |
| §6.6 | Web services | Flask, REST API |
| §6.7 | Database | SQLite, WAL, sqlite3 |
| §6.8 | Use roadmap_lib | roadmap_lib, existing functions |
| §6.9 | Deterministic IDs | UUID, frontmatter, deterministic |
| §6.10 | Dashboard service is display-only | dashboard, generic, display-only |
| §6.11 | Shell scripts | main(), functions, composable |
| §6.12 | Logging | logging, getLogger, __name__ |

## §7. C# / .NET (`csharp.md`)

| § | Section | Keywords |
|---|---------|----------|
| §7.1 | References | C# Conventions, .NET Design Guidelines, Runtime Coding Style |
| §7.2 | Naming | PascalCase, camelCase, _camelCase, I prefix, Async suffix |
| §7.3 | Nullable Reference Types | Nullable, enable, null-forgiving, required, guard clause |
| §7.4 | Immutability | readonly, record, ImmutableList, init, with |
| §7.5 | Concurrency | async/await, ConfigureAwait, CancellationToken, ValueTask |
| §7.6 | Dependency Injection | Microsoft.Extensions.DependencyInjection, IOptions, Transient, Singleton |
| §7.7 | Logging | ILogger, structured, LoggerMessage, source generator |
| §7.8 | Linting and Formatting | .editorconfig, Roslyn, EnforceCodeStyleInBuild, dotnet format |
| §7.9 | Testing | xUnit, FluentAssertions, NSubstitute, Fact, Theory |
| §7.10 | Secure Storage | DPAPI, ProtectedData, User Secrets |
| §7.11 | Privacy | capabilities, manifest, broadFileSystemAccess, consent |
| §7.12 | Feature Flags | IFeatureManager, Microsoft.FeatureManagement |
| §7.13 | Analytics | ILogger, interface |

## §8. Windows / WinUI 3 (`windows.md`)

| § | Section | Keywords |
|---|---------|----------|
| §8.1 | References | WinUI 3, Windows App SDK, Fluent 2, WinUI Gallery |
| §8.2 | Architecture | MVVM, CommunityToolkit.Mvvm, NavigationView, Frame |
| §8.3 | Fluent Design | built-in controls, Segoe UI Variable, Segoe Fluent Icons |
| §8.4 | Theming | Light, Dark, High Contrast, ThemeResource, semantic colors |
| §8.5 | Accessibility | UI Automation, AutomationProperties, Accessibility Insights, Narrator |
| §8.6 | Localization | MRT Core, .resw, x:Uid, ResourceLoader |
| §8.7 | Deep Linking / Protocol Activation | uap:Protocol, AppInstance, GetActivatedEventArgs |
| §8.8 | App Notifications | AppNotificationManager, AppNotificationBuilder, toast |
| §8.9 | High DPI / Display Scaling | effective pixels, RasterizationScale, multi-scale assets |
| §8.10 | MSIX Packaging | MSIX, single-project, capabilities, signing |
| §8.11 | Concurrency | DispatcherQueue, TryEnqueue, UI thread |
| §8.12 | RTL Layout Support | FlowDirection, RightToLeft |
| §8.13 | Logging | ILogger, ETW, EventSource, Live Visual Tree |
| §8.14 | Debug Mode | #if DEBUG, settings page |
| §8.15 | Design-Time Data | d:DataContext, d:DesignInstance, XAML Hot Reload |

## §9. UI Design (`ui.md`)

| § | Section | Keywords |
|---|---------|----------|
| §9.1 | Platform Design Languages | HIG, Material Design, Fluent, WCAG |
| §9.2 | Visual Hierarchy | focal point, primary action, size, weight, proximity |
| §9.3 | Spacing | 4px, 8px grid, spacing scale, padding, margin |
| §9.4 | Typography | system font, body text, line height, paragraph width |
| §9.5 | Color | semantic tokens, palette, contrast, dark mode |
| §9.6 | Layout | single-column, content-first, responsive, scroll direction |
| §9.7 | State Design | loading, empty state, error state, skeleton, CTA |
| §9.8 | Form Design | forms, validation, error messages, labels |
| §9.8.1 | Layout | single-column, top-aligned labels |
| §9.8.2 | Validation | blur, keystroke, submit |
| §9.8.3 | Error messages | inline, below field, icon, specific |
| §9.8.4 | Other principles | placeholder, pre-fill, optional fields |
| §9.9 | Feedback Patterns | toast, snackbar, dialog, confirmation, destructive |
| §9.10 | Touch & Click Targets | 44pt, 48dp, 40epx, 24px, hit area, spacing |
| §9.11 | Animation & Motion | duration, easing, reduced-motion, spring |
| §9.12 | Iconography | SF Symbols, Material Symbols, Segoe Fluent Icons, labels |
| §9.13 | Data Display | list, table, cards, grid, sort, filter, search |

## §10. Networking (`networking.md`)

| § | Section | Keywords |
|---|---------|----------|
| §10.1 | References | Microsoft REST, Google API Design, Zalando, RFC 9457, RFC 9111 |
| §10.2 | API Design | REST, URL, HTTP methods, status codes, versioning |
| §10.3 | Error Responses | RFC 9457, Problem Details, application/problem+json |
| §10.4 | Pagination | cursor, offset, next_cursor, has_more, page_token |
| §10.5 | Retry and Resilience | exponential backoff, jitter, circuit breaker, retryable |
| §10.6 | Timeouts | connection timeout, read timeout, 10s, 30s |
| §10.7 | Caching | Cache-Control, ETag, If-None-Match, stale-while-revalidate |
| §10.8 | Offline and Connectivity | offline-first, optimistic updates, sync, conflict resolution |
| §10.9 | Rate Limiting | 429, Retry-After, RateLimit-Remaining, throttling |
| §10.10 | Real-Time Communication | SSE, WebSocket, polling, EventSource |

## §11. Security (`security.md`)

| § | Section | Keywords |
|---|---------|----------|
| §11.1 | References | OWASP, MASVS, MASTG, Mozilla TLS |
| §11.2 | Authentication | OAuth 2.0, OIDC, PKCE, system browser, BFF |
| §11.3 | Token Handling | access token, refresh token, JWT, storage |
| §11.3.1 | Access tokens | short-lived, 5-15 min, claims |
| §11.3.2 | Refresh tokens | rotation, revocation, token family |
| §11.3.3 | Token refresh strategy | proactive, 75% TTL, queue |
| §11.3.4 | Secure storage per platform | Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly |
| §11.3.5 | Never do these | localStorage, URL params, alg:none |
| §11.4 | Authorization | RBAC, scopes, least privilege, BOLA, deny by default |
| §11.5 | Transport Security | TLS 1.2, TLS 1.3, HSTS, certificate pinning, AEAD |
| §11.6 | CORS | origin allowlist, preflight, credentials, misconfigurations |
| §11.7 | Content Security Policy | CSP, nonce, strict-dynamic, frame-ancestors, report-only |
| §11.8 | Input Validation | allowlist, parameterized queries, output encoding, file uploads |
| §11.9 | Sensitive Data | data minimization, PII, field-level encryption, KMS |
| §11.10 | Dependency Security | lockfiles, npm audit, pin versions, SRI, supply chain |
| §11.11 | Security Headers Checklist | HSTS, CSP, X-Content-Type-Options, Referrer-Policy |

## §12. Spec Writing Format (`specs.md`)

| § | Section | Keywords |
|---|---------|----------|
| §12.1 | Frontmatter | version, status, created, platforms, dependencies |
| §12.2 | RFC 2119 Keywords | MUST, SHOULD, MAY, requirements |
| §12.3 | Requirement Numbering | REQ-NNN, sequential, test vector |
| §12.4 | Template Variables | {{app_name}}, {{bundle_id}}, placeholders |
| §12.5 | Standard Sections | Overview, Requirements, API Contract, Accessibility, Logging |
| §12.6 | Test Vector Formats | behavioral table, data JSON, input/expected |
| §12.7 | Logging Section | log messages, subsystem, category, grep |
| §12.8 | Privacy Section | data collected, storage, PII handling |
| §12.9 | Feature Flags Section | flag keys, gating |
| §12.10 | Analytics Section | event names, property schemas |

## §13. Best Practices References (`best-practices-references.md`)

| § | Section | Keywords |
|---|---------|----------|
| §13.1 | Apple | HIG, Swift API Design, Accessibility, App Store |
| §13.2 | Android | Material Design 3, Architecture, Kotlin, Google Play |
| §13.3 | Web | WCAG, WAI-ARIA, OWASP, MDN |
| §13.4 | Windows / .NET | C# Conventions, .NET Guidelines, WinUI 3, Fluent, MSIX |
| §13.5 | UI Design | NNGroup, Visual Hierarchy, Form Design, Empty States |
| §13.6 | Networking | Microsoft REST, Google API, Zalando, RFC 9457, RFC 9111 |
| §13.7 | Security | OWASP Top 10, Mobile Top 10, Cheat Sheets, Mozilla TLS, SLSA |
| §13.8 | Cross-Platform | Nielsen Norman, MASVS, MASTG |
