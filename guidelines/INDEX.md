# Guidelines Index

Complete index of all rules, principles, and conventions across all guideline files.
Use `CG-X.Y` notation to cross-reference any rule. Search this file to find where a topic is covered.

---

## CG-1. General Coding Guidelines — [general.md](general.md)

| CG- | Rule | Keywords |
|---|------|----------|
| [CG-1.1](general.md#CG-11-prefer-native-controls-and-libraries) | Prefer native controls and libraries | native, platform, built-in, framework |
| [CG-1.2](general.md#CG-12-for-novel-components-prefer-proven-open-source-solutions) | For novel components, prefer proven open-source solutions | open-source, library, custom |
| [CG-1.3](general.md#CG-13-surface-all-design-decisions) | Surface all design decisions | decisions, approval, LLM, consistency |
| [CG-1.4](general.md#CG-14-no-blocking-the-main-thread) | No blocking the main thread | async, await, concurrency, background, UI thread |
| [CG-1.5](general.md#CG-15-always-show-progress) | Always show progress | spinner, skeleton, shimmer, progress bar, loading |
| [CG-1.6](general.md#CG-16-comprehensive-unit-testing) | Comprehensive unit testing | tests, unit tests, edge cases, test file |
| [CG-1.7](general.md#CG-17-small-atomic-commits) | Small, atomic commits | commits, git, one change |
| [CG-1.8](general.md#CG-18-post-generation-verification) | Post-generation verification | build, test, lint, accessibility audit, code review |
| [CG-1.9](general.md#CG-19-instrumented-logging) | Instrumented logging | logging, os.log, Timber, ILogger, structured |
| [CG-1.10](general.md#CG-110-deep-linking) | Deep linking | deep link, URL, Universal Links, App Links, protocol activation |
| [CG-1.11](general.md#CG-111-scriptable-and-automatable) | Scriptable and automatable | AppIntents, AppActions, Shortcuts, automation |
| [CG-1.12](general.md#CG-112-accessibility-from-day-one) | Accessibility from day one | accessibility, VoiceOver, TalkBack, Narrator, WCAG, contrast, focus |
| [CG-1.13](general.md#CG-113-localizability) | Localizability | localization, i18n, strings, .xcstrings, strings.xml, .resw |
| [CG-1.14](general.md#CG-114-rtl-layout-support) | RTL layout support | RTL, right-to-left, leading, trailing, FlowDirection |
| [CG-1.15](general.md#CG-115-respect-accessibility-display-options) | Respect accessibility display options | reduced motion, high contrast, bold text, grayscale |
| [CG-1.16](general.md#CG-116-privacy-and-security-by-default) | Privacy and security by default | privacy, security, PII, TLS, consent |
| [CG-1.16.1](general.md#CG-1161-data-minimization) | Data minimization | data minimization, on-device |
| [CG-1.16.2](general.md#CG-1162-consent) | Consent | consent, opt-in, deny |
| [CG-1.16.3](general.md#CG-1163-secure-storage) | Secure storage | Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly |
| [CG-1.16.4](general.md#CG-1164-no-pii-logging) | No PII logging | PII, logging, personally identifiable |
| [CG-1.16.5](general.md#CG-1165-tls-only) | TLS only | TLS, HTTPS, encryption |
| [CG-1.16.6](general.md#CG-1166-input-sanitization) | Input sanitization | sanitization, XSS, injection |
| [CG-1.17](general.md#CG-117-feature-flags) | Feature flags | feature flags, FeatureFlagProvider, gating |
| [CG-1.18](general.md#CG-118-analytics) | Analytics | analytics, AnalyticsProvider, tracking |
| [CG-1.19](general.md#CG-119-ab-testing) | A/B testing | A/B testing, ExperimentProvider, variants |
| [CG-1.20](general.md#CG-120-debug-mode) | Debug mode | debug panel, flag overrides, environment info |
| [CG-1.21](general.md#CG-121-linting-from-day-one) | Linting from day one | linting, SwiftLint, ktlint, ESLint, Roslyn, dotnet format |

## CG-2. Engineering Principles — [engineering-principles.md](engineering-principles.md)

| CG- | Principle | Keywords |
|---|-----------|----------|
| [CG-2.1](engineering-principles.md#CG-21-simplicity) | Simplicity | simplicity, complexity, concerns |
| [CG-2.2](engineering-principles.md#CG-22-make-it-work-make-it-right-make-it-fast) | Make It Work, Make It Right, Make It Fast | correctness, refactor, optimize, phases |
| [CG-2.3](engineering-principles.md#CG-23-composition-over-inheritance) | Composition over inheritance | composition, inheritance, protocols, interfaces |
| [CG-2.4](engineering-principles.md#CG-24-dependency-injection) | Dependency injection | DI, injection, constructor, service locator |
| [CG-2.5](engineering-principles.md#CG-25-immutability-by-default) | Immutability by default | immutability, let, val, const, mutable |
| [CG-2.6](engineering-principles.md#CG-26-fail-fast) | Fail fast | fail fast, assertions, preconditions, typed errors |
| [CG-2.7](engineering-principles.md#CG-27-idempotency) | Idempotency | idempotent, debounce, retry, duplicate |
| [CG-2.8](engineering-principles.md#CG-28-design-for-deletion) | Design for deletion | deletion, disposable, maintenance, liability |
| [CG-2.9](engineering-principles.md#CG-29-yagni) | YAGNI | YAGNI, speculative, premature, requirements |
| [CG-2.10](engineering-principles.md#CG-210-explicit-over-implicit) | Explicit over implicit | explicit, implicit, hidden, magic |
| [CG-2.11](engineering-principles.md#CG-211-small-reversible-decisions) | Small, reversible decisions | reversible, incremental, binding |
| [CG-2.12](engineering-principles.md#CG-212-tight-feedback-loops) | Tight feedback loops | feedback, tests, deploy, iteration |
| [CG-2.13](engineering-principles.md#CG-213-separation-of-concerns) | Separation of concerns | separation, single responsibility, module |
| [CG-2.14](engineering-principles.md#CG-214-principle-of-least-astonishment) | Principle of least astonishment | least astonishment, expectations, surprise |
| [CG-2.15](engineering-principles.md#CG-215-manage-complexity-through-boundaries) | Manage complexity through boundaries | boundaries, ports, adapters, hexagonal |
| [CG-2.16](engineering-principles.md#CG-216-meta-principle-optimize-for-change) | Meta-Principle: Optimize for Change | change, future, cost |

## CG-3. Swift / SwiftUI / AppKit — [swift.md](swift.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-3.1](swift.md#CG-31-references) | References | Swift API Design Guidelines, SwiftUI Performance |
| [CG-3.2](swift.md#CG-32-logging) | Logging | os.log, Logger, subsystem, category |
| [CG-3.3](swift.md#CG-33-secure-storage) | Secure Storage | Keychain, UserDefaults, secrets |
| [CG-3.4](swift.md#CG-34-localization) | Localization | String(localized:), NSLocalizedString, .xcstrings |
| [CG-3.5](swift.md#CG-35-linting-and-formatting) | Linting and Formatting | SwiftLint, swift-format |
| [CG-3.6](swift.md#CG-36-shortcuts-and-automation) | Shortcuts and Automation | AppIntents, Shortcuts, Siri, AppleScript |
| [CG-3.7](swift.md#CG-37-previews) | Previews | #Preview, SwiftUI, render |
| [CG-3.8](swift.md#CG-38-dynamic-type) | Dynamic Type | Dynamic Type, font sizes, text scaling |
| [CG-3.9](swift.md#CG-39-accessibility-environment-values) | Accessibility Environment Values | reduceMotion, reduceTransparency, colorSchemeContrast |
| [CG-3.10](swift.md#CG-310-concurrency) | Concurrency | async/await, Task, actors, @MainActor |
| [CG-3.11](swift.md#CG-311-privacy) | Privacy | App Tracking Transparency, Privacy Report, NSUsageDescription |
| [CG-3.12](swift.md#CG-312-feature-flags) | Feature Flags | protocol, UserDefaults |
| [CG-3.13](swift.md#CG-313-analytics) | Analytics | protocol, os.log |

## CG-4. Kotlin / Compose / Ktor — [kotlin.md](kotlin.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-4.1](kotlin.md#CG-41-references) | References | Kotlin Conventions, Material Design 3, Architecture |
| [CG-4.2](kotlin.md#CG-42-logging) | Logging | Timber, android.util.Log |
| [CG-4.3](kotlin.md#CG-43-concurrency) | Concurrency | Coroutines, Dispatchers.IO, viewModelScope |
| [CG-4.4](kotlin.md#CG-44-secure-storage) | Secure Storage | EncryptedSharedPreferences, Android Keystore |
| [CG-4.5](kotlin.md#CG-45-localization) | Localization | strings.xml, stringResource, R.string |
| [CG-4.6](kotlin.md#CG-46-linting-and-formatting) | Linting and Formatting | ktlint, .editorconfig |
| [CG-4.7](kotlin.md#CG-47-shortcuts-and-automation) | Shortcuts and Automation | AppActions, Google Assistant, Intent |
| [CG-4.8](kotlin.md#CG-48-previews) | Previews | @Preview, Compose |
| [CG-4.9](kotlin.md#CG-49-font-scaling) | Font Scaling | fontScale, Configuration, 2x |
| [CG-4.10](kotlin.md#CG-410-accessibility-settings) | Accessibility Settings | animator_duration_scale, TalkBack, Switch Access |
| [CG-4.11](kotlin.md#CG-411-privacy) | Privacy | scoped storage, permissions, rationale |
| [CG-4.12](kotlin.md#CG-412-feature-flags) | Feature Flags | interface, SharedPreferences |
| [CG-4.13](kotlin.md#CG-413-analytics) | Analytics | interface, Timber |
| [CG-4.14](kotlin.md#CG-414-rtl-support) | RTL Support | supportsRtl, start/end |
| [CG-4.15](kotlin.md#CG-415-immutability) | Immutability | val, data class, StateFlow |

## CG-5. TypeScript / React / Web — [typescript.md](typescript.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-5.1](typescript.md#CG-51-linting-and-formatting) | Linting and Formatting | ESLint, Prettier, Stylelint |
| [CG-5.2](typescript.md#CG-52-accessibility-references) | Accessibility References | WCAG 2.1, WAI-ARIA |
| [CG-5.3](typescript.md#CG-53-accessibility-css-media-queries) | Accessibility CSS Media Queries | prefers-reduced-motion, prefers-contrast, forced-colors |
| [CG-5.4](typescript.md#CG-54-security) | Security | CSP, HttpOnly, cookies, sanitization, Do Not Track |
| [CG-5.5](typescript.md#CG-55-localization) | Localization | react-intl, i18next, FormatJS, message catalogs |
| [CG-5.6](typescript.md#CG-56-rtl-layout-support) | RTL Layout Support | CSS logical properties, margin-inline-start, dir |
| [CG-5.7](typescript.md#CG-57-testing) | Testing | Playwright, E2E, visual regression, Storybook |
| [CG-5.8](typescript.md#CG-58-concurrency) | Concurrency | Promise, async/await, Web Workers |
| [CG-5.9](typescript.md#CG-59-deep-linking) | Deep Linking | URL routing, shareable URL |
| [CG-5.10](typescript.md#CG-510-debug-mode) | Debug Mode | /debug, Ctrl+Shift+D, NODE_ENV |
| [CG-5.11](typescript.md#CG-511-feature-flags) | Feature Flags | interface, localStorage |
| [CG-5.12](typescript.md#CG-512-analytics) | Analytics | interface, console |
| [CG-5.13](typescript.md#CG-513-immutability) | Immutability | const, useState |

## CG-6. Python — [python.md](python.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-6.1](python.md#CG-61-no-external-dependencies-in-core-libraries) | No external dependencies in core libraries | stdlib, roadmap_lib, portable |
| [CG-6.2](python.md#CG-62-testing) | Testing | pytest, regression test, demo port 9888 |
| [CG-6.3](python.md#CG-63-type-hints) | Type hints | type hints, annotations, Python 3.9 |
| [CG-6.4](python.md#CG-64-file-paths) | File paths | pathlib, Path, os.path |
| [CG-6.5](python.md#CG-65-yaml-frontmatter) | YAML frontmatter | frontmatter, parse, roadmap_lib |
| [CG-6.6](python.md#CG-66-web-services) | Web services | Flask, REST API |
| [CG-6.7](python.md#CG-67-database) | Database | SQLite, WAL, sqlite3 |
| [CG-6.8](python.md#CG-68-use-roadmap_lib) | Use roadmap_lib | roadmap_lib, existing functions |
| [CG-6.9](python.md#CG-69-deterministic-ids) | Deterministic IDs | UUID, frontmatter, deterministic |
| [CG-6.10](python.md#CG-610-dashboard-service-is-display-only) | Dashboard service is display-only | dashboard, generic, display-only |
| [CG-6.11](python.md#CG-611-shell-scripts) | Shell scripts | main(), functions, composable |
| [CG-6.12](python.md#CG-612-logging) | Logging | logging, getLogger, __name__ |

## CG-7. C# / .NET — [csharp.md](csharp.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-7.1](csharp.md#CG-71-references) | References | C# Conventions, .NET Design Guidelines, Runtime Coding Style |
| [CG-7.2](csharp.md#CG-72-naming) | Naming | PascalCase, camelCase, _camelCase, I prefix, Async suffix |
| [CG-7.3](csharp.md#CG-73-nullable-reference-types) | Nullable Reference Types | Nullable, enable, null-forgiving, required, guard clause |
| [CG-7.4](csharp.md#CG-74-immutability) | Immutability | readonly, record, ImmutableList, init, with |
| [CG-7.5](csharp.md#CG-75-concurrency) | Concurrency | async/await, ConfigureAwait, CancellationToken, ValueTask |
| [CG-7.6](csharp.md#CG-76-dependency-injection) | Dependency Injection | Microsoft.Extensions.DependencyInjection, IOptions, Transient, Singleton |
| [CG-7.7](csharp.md#CG-77-logging) | Logging | ILogger, structured, LoggerMessage, source generator |
| [CG-7.8](csharp.md#CG-78-linting-and-formatting) | Linting and Formatting | .editorconfig, Roslyn, EnforceCodeStyleInBuild, dotnet format |
| [CG-7.9](csharp.md#CG-79-testing) | Testing | xUnit, FluentAssertions, NSubstitute, Fact, Theory |
| [CG-7.10](csharp.md#CG-710-secure-storage) | Secure Storage | DPAPI, ProtectedData, User Secrets |
| [CG-7.11](csharp.md#CG-711-privacy) | Privacy | capabilities, manifest, broadFileSystemAccess, consent |
| [CG-7.12](csharp.md#CG-712-feature-flags) | Feature Flags | IFeatureManager, Microsoft.FeatureManagement |
| [CG-7.13](csharp.md#CG-713-analytics) | Analytics | ILogger, interface |

## CG-8. Windows / WinUI 3 — [windows.md](windows.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-8.1](windows.md#CG-81-references) | References | WinUI 3, Windows App SDK, Fluent 2, WinUI Gallery |
| [CG-8.2](windows.md#CG-82-architecture) | Architecture | MVVM, CommunityToolkit.Mvvm, NavigationView, Frame |
| [CG-8.3](windows.md#CG-83-fluent-design) | Fluent Design | built-in controls, Segoe UI Variable, Segoe Fluent Icons |
| [CG-8.4](windows.md#CG-84-theming) | Theming | Light, Dark, High Contrast, ThemeResource, semantic colors |
| [CG-8.5](windows.md#CG-85-accessibility) | Accessibility | UI Automation, AutomationProperties, Accessibility Insights, Narrator |
| [CG-8.6](windows.md#CG-86-localization) | Localization | MRT Core, .resw, x:Uid, ResourceLoader |
| [CG-8.7](windows.md#CG-87-deep-linking--protocol-activation) | Deep Linking / Protocol Activation | uap:Protocol, AppInstance, GetActivatedEventArgs |
| [CG-8.8](windows.md#CG-88-app-notifications) | App Notifications | AppNotificationManager, AppNotificationBuilder, toast |
| [CG-8.9](windows.md#CG-89-high-dpi--display-scaling) | High DPI / Display Scaling | effective pixels, RasterizationScale, multi-scale assets |
| [CG-8.10](windows.md#CG-810-msix-packaging) | MSIX Packaging | MSIX, single-project, capabilities, signing |
| [CG-8.11](windows.md#CG-811-concurrency) | Concurrency | DispatcherQueue, TryEnqueue, UI thread |
| [CG-8.12](windows.md#CG-812-rtl-layout-support) | RTL Layout Support | FlowDirection, RightToLeft |
| [CG-8.13](windows.md#CG-813-logging) | Logging | ILogger, ETW, EventSource, Live Visual Tree |
| [CG-8.14](windows.md#CG-814-debug-mode) | Debug Mode | #if DEBUG, settings page |
| [CG-8.15](windows.md#CG-815-design-time-data) | Design-Time Data | d:DataContext, d:DesignInstance, XAML Hot Reload |

## CG-9. UI Design — [ui.md](ui.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-9.1](ui.md#CG-91-platform-design-languages) | Platform Design Languages | HIG, Material Design, Fluent, WCAG |
| [CG-9.2](ui.md#CG-92-visual-hierarchy) | Visual Hierarchy | focal point, primary action, size, weight, proximity |
| [CG-9.3](ui.md#CG-93-spacing) | Spacing | 4px, 8px grid, spacing scale, padding, margin |
| [CG-9.4](ui.md#CG-94-typography) | Typography | system font, body text, line height, paragraph width |
| [CG-9.5](ui.md#CG-95-color) | Color | semantic tokens, palette, contrast, dark mode |
| [CG-9.6](ui.md#CG-96-layout) | Layout | single-column, content-first, responsive, scroll direction |
| [CG-9.7](ui.md#CG-97-state-design) | State Design | loading, empty state, error state, skeleton, CTA |
| [CG-9.8](ui.md#CG-98-form-design) | Form Design | forms, validation, error messages, labels |
| [CG-9.8.1](ui.md#CG-981-layout) | Layout | single-column, top-aligned labels |
| [CG-9.8.2](ui.md#CG-982-validation) | Validation | blur, keystroke, submit |
| [CG-9.8.3](ui.md#CG-983-error-messages) | Error messages | inline, below field, icon, specific |
| [CG-9.8.4](ui.md#CG-984-other-principles) | Other principles | placeholder, pre-fill, optional fields |
| [CG-9.9](ui.md#CG-99-feedback-patterns) | Feedback Patterns | toast, snackbar, dialog, confirmation, destructive |
| [CG-9.10](ui.md#CG-910-touch--click-targets) | Touch & Click Targets | 44pt, 48dp, 40epx, 24px, hit area, spacing |
| [CG-9.11](ui.md#CG-911-animation--motion) | Animation & Motion | duration, easing, reduced-motion, spring |
| [CG-9.12](ui.md#CG-912-iconography) | Iconography | SF Symbols, Material Symbols, Segoe Fluent Icons, labels |
| [CG-9.13](ui.md#CG-913-data-display) | Data Display | list, table, cards, grid, sort, filter, search |

## CG-10. Networking — [networking.md](networking.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-10.1](networking.md#CG-101-references) | References | Microsoft REST, Google API Design, Zalando, RFC 9457, RFC 9111 |
| [CG-10.2](networking.md#CG-102-api-design) | API Design | REST, URL, HTTP methods, status codes, versioning |
| [CG-10.3](networking.md#CG-103-error-responses) | Error Responses | RFC 9457, Problem Details, application/problem+json |
| [CG-10.4](networking.md#CG-104-pagination) | Pagination | cursor, offset, next_cursor, has_more, page_token |
| [CG-10.5](networking.md#CG-105-retry-and-resilience) | Retry and Resilience | exponential backoff, jitter, circuit breaker, retryable |
| [CG-10.6](networking.md#CG-106-timeouts) | Timeouts | connection timeout, read timeout, 10s, 30s |
| [CG-10.7](networking.md#CG-107-caching) | Caching | Cache-Control, ETag, If-None-Match, stale-while-revalidate |
| [CG-10.8](networking.md#CG-108-offline-and-connectivity) | Offline and Connectivity | offline-first, optimistic updates, sync, conflict resolution |
| [CG-10.9](networking.md#CG-109-rate-limiting) | Rate Limiting | 429, Retry-After, RateLimit-Remaining, throttling |
| [CG-10.10](networking.md#CG-1010-real-time-communication) | Real-Time Communication | SSE, WebSocket, polling, EventSource |

## CG-11. Security — [security.md](security.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-11.1](security.md#CG-111-references) | References | OWASP, MASVS, MASTG, Mozilla TLS |
| [CG-11.2](security.md#CG-112-authentication) | Authentication | OAuth 2.0, OIDC, PKCE, system browser, BFF |
| [CG-11.3](security.md#CG-113-token-handling) | Token Handling | access token, refresh token, JWT, storage |
| [CG-11.3.1](security.md#CG-1131-access-tokens) | Access tokens | short-lived, 5-15 min, claims |
| [CG-11.3.2](security.md#CG-1132-refresh-tokens) | Refresh tokens | rotation, revocation, token family |
| [CG-11.3.3](security.md#CG-1133-token-refresh-strategy) | Token refresh strategy | proactive, 75% TTL, queue |
| [CG-11.3.4](security.md#CG-1134-secure-storage-per-platform) | Secure storage per platform | Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly |
| [CG-11.3.5](security.md#CG-1135-never-do-these) | Never do these | localStorage, URL params, alg:none |
| [CG-11.4](security.md#CG-114-authorization) | Authorization | RBAC, scopes, least privilege, BOLA, deny by default |
| [CG-11.5](security.md#CG-115-transport-security) | Transport Security | TLS 1.2, TLS 1.3, HSTS, certificate pinning, AEAD |
| [CG-11.6](security.md#CG-116-cors) | CORS | origin allowlist, preflight, credentials, misconfigurations |
| [CG-11.7](security.md#CG-117-content-security-policy) | Content Security Policy | CSP, nonce, strict-dynamic, frame-ancestors, report-only |
| [CG-11.8](security.md#CG-118-input-validation) | Input Validation | allowlist, parameterized queries, output encoding, file uploads |
| [CG-11.9](security.md#CG-119-sensitive-data) | Sensitive Data | data minimization, PII, field-level encryption, KMS |
| [CG-11.10](security.md#CG-1110-dependency-security) | Dependency Security | lockfiles, npm audit, pin versions, SRI, supply chain |
| [CG-11.11](security.md#CG-1111-security-headers-checklist) | Security Headers Checklist | HSTS, CSP, X-Content-Type-Options, Referrer-Policy |

## CG-12. Spec Writing Format — [specs.md](specs.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-12.1](specs.md#CG-121-frontmatter) | Frontmatter | version, status, created, platforms, dependencies |
| [CG-12.2](specs.md#CG-122-rfc-2119-keywords) | RFC 2119 Keywords | MUST, SHOULD, MAY, requirements |
| [CG-12.3](specs.md#CG-123-requirement-numbering) | Requirement Numbering | REQ-NNN, sequential, test vector |
| [CG-12.4](specs.md#CG-124-template-variables) | Template Variables | {{app_name}}, {{bundle_id}}, placeholders |
| [CG-12.5](specs.md#CG-125-standard-sections) | Standard Sections | Overview, Requirements, API Contract, Accessibility, Logging |
| [CG-12.6](specs.md#CG-126-test-vector-formats) | Test Vector Formats | behavioral table, data JSON, input/expected |
| [CG-12.7](specs.md#CG-127-logging-section) | Logging Section | log messages, subsystem, category, grep |
| [CG-12.8](specs.md#CG-128-privacy-section) | Privacy Section | data collected, storage, PII handling |
| [CG-12.9](specs.md#CG-129-feature-flags-section) | Feature Flags Section | flag keys, gating |
| [CG-12.10](specs.md#CG-1210-analytics-section) | Analytics Section | event names, property schemas |

## CG-13. Best Practices References — [best-practices-references.md](best-practices-references.md)

| CG- | Section | Keywords |
|---|---------|----------|
| [CG-13.1](best-practices-references.md#CG-131-apple) | Apple | HIG, Swift API Design, Accessibility, App Store |
| [CG-13.2](best-practices-references.md#CG-132-android) | Android | Material Design 3, Architecture, Kotlin, Google Play |
| [CG-13.3](best-practices-references.md#CG-133-web) | Web | WCAG, WAI-ARIA, OWASP, MDN |
| [CG-13.4](best-practices-references.md#CG-134-windows--net) | Windows / .NET | C# Conventions, .NET Guidelines, WinUI 3, Fluent, MSIX |
| [CG-13.5](best-practices-references.md#CG-135-ui-design) | UI Design | NNGroup, Visual Hierarchy, Form Design, Empty States |
| [CG-13.6](best-practices-references.md#CG-136-networking) | Networking | Microsoft REST, Google API, Zalando, RFC 9457, RFC 9111 |
| [CG-13.7](best-practices-references.md#CG-137-security) | Security | OWASP Top 10, Mobile Top 10, Cheat Sheets, Mozilla TLS, SLSA |
| [CG-13.8](best-practices-references.md#CG-138-cross-platform) | Cross-Platform | Nielsen Norman, MASVS, MASTG |
