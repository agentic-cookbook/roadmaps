# Guidelines Index

Complete index of all rules, principles, and conventions across all guideline files.
Use `§X.Y` notation to cross-reference any rule. Search this file to find where a topic is covered.

---

## §1. General Coding Guidelines — [general.md](general.md)

| § | Rule | Keywords |
|---|------|----------|
| [§1.1](general.md#§11-prefer-native-controls-and-libraries) | Prefer native controls and libraries | native, platform, built-in, framework |
| [§1.2](general.md#§12-for-novel-components-prefer-proven-open-source-solutions) | For novel components, prefer proven open-source solutions | open-source, library, custom |
| [§1.3](general.md#§13-surface-all-design-decisions) | Surface all design decisions | decisions, approval, LLM, consistency |
| [§1.4](general.md#§14-no-blocking-the-main-thread) | No blocking the main thread | async, await, concurrency, background, UI thread |
| [§1.5](general.md#§15-always-show-progress) | Always show progress | spinner, skeleton, shimmer, progress bar, loading |
| [§1.6](general.md#§16-comprehensive-unit-testing) | Comprehensive unit testing | tests, unit tests, edge cases, test file |
| [§1.7](general.md#§17-small-atomic-commits) | Small, atomic commits | commits, git, one change |
| [§1.8](general.md#§18-post-generation-verification) | Post-generation verification | build, test, lint, accessibility audit, code review |
| [§1.9](general.md#§19-instrumented-logging) | Instrumented logging | logging, os.log, Timber, ILogger, structured |
| [§1.10](general.md#§110-deep-linking) | Deep linking | deep link, URL, Universal Links, App Links, protocol activation |
| [§1.11](general.md#§111-scriptable-and-automatable) | Scriptable and automatable | AppIntents, AppActions, Shortcuts, automation |
| [§1.12](general.md#§112-accessibility-from-day-one) | Accessibility from day one | accessibility, VoiceOver, TalkBack, Narrator, WCAG, contrast, focus |
| [§1.13](general.md#§113-localizability) | Localizability | localization, i18n, strings, .xcstrings, strings.xml, .resw |
| [§1.14](general.md#§114-rtl-layout-support) | RTL layout support | RTL, right-to-left, leading, trailing, FlowDirection |
| [§1.15](general.md#§115-respect-accessibility-display-options) | Respect accessibility display options | reduced motion, high contrast, bold text, grayscale |
| [§1.16](general.md#§116-privacy-and-security-by-default) | Privacy and security by default | privacy, security, PII, TLS, consent |
| [§1.16.1](general.md#§1161-data-minimization) | Data minimization | data minimization, on-device |
| [§1.16.2](general.md#§1162-consent) | Consent | consent, opt-in, deny |
| [§1.16.3](general.md#§1163-secure-storage) | Secure storage | Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly |
| [§1.16.4](general.md#§1164-no-pii-logging) | No PII logging | PII, logging, personally identifiable |
| [§1.16.5](general.md#§1165-tls-only) | TLS only | TLS, HTTPS, encryption |
| [§1.16.6](general.md#§1166-input-sanitization) | Input sanitization | sanitization, XSS, injection |
| [§1.17](general.md#§117-feature-flags) | Feature flags | feature flags, FeatureFlagProvider, gating |
| [§1.18](general.md#§118-analytics) | Analytics | analytics, AnalyticsProvider, tracking |
| [§1.19](general.md#§119-ab-testing) | A/B testing | A/B testing, ExperimentProvider, variants |
| [§1.20](general.md#§120-debug-mode) | Debug mode | debug panel, flag overrides, environment info |
| [§1.21](general.md#§121-linting-from-day-one) | Linting from day one | linting, SwiftLint, ktlint, ESLint, Roslyn, dotnet format |

## §2. Engineering Principles — [engineering-principles.md](engineering-principles.md)

| § | Principle | Keywords |
|---|-----------|----------|
| [§2.1](engineering-principles.md#§21-simplicity) | Simplicity | simplicity, complexity, concerns |
| [§2.2](engineering-principles.md#§22-make-it-work-make-it-right-make-it-fast) | Make It Work, Make It Right, Make It Fast | correctness, refactor, optimize, phases |
| [§2.3](engineering-principles.md#§23-composition-over-inheritance) | Composition over inheritance | composition, inheritance, protocols, interfaces |
| [§2.4](engineering-principles.md#§24-dependency-injection) | Dependency injection | DI, injection, constructor, service locator |
| [§2.5](engineering-principles.md#§25-immutability-by-default) | Immutability by default | immutability, let, val, const, mutable |
| [§2.6](engineering-principles.md#§26-fail-fast) | Fail fast | fail fast, assertions, preconditions, typed errors |
| [§2.7](engineering-principles.md#§27-idempotency) | Idempotency | idempotent, debounce, retry, duplicate |
| [§2.8](engineering-principles.md#§28-design-for-deletion) | Design for deletion | deletion, disposable, maintenance, liability |
| [§2.9](engineering-principles.md#§29-yagni) | YAGNI | YAGNI, speculative, premature, requirements |
| [§2.10](engineering-principles.md#§210-explicit-over-implicit) | Explicit over implicit | explicit, implicit, hidden, magic |
| [§2.11](engineering-principles.md#§211-small-reversible-decisions) | Small, reversible decisions | reversible, incremental, binding |
| [§2.12](engineering-principles.md#§212-tight-feedback-loops) | Tight feedback loops | feedback, tests, deploy, iteration |
| [§2.13](engineering-principles.md#§213-separation-of-concerns) | Separation of concerns | separation, single responsibility, module |
| [§2.14](engineering-principles.md#§214-principle-of-least-astonishment) | Principle of least astonishment | least astonishment, expectations, surprise |
| [§2.15](engineering-principles.md#§215-manage-complexity-through-boundaries) | Manage complexity through boundaries | boundaries, ports, adapters, hexagonal |
| [§2.16](engineering-principles.md#§216-meta-principle-optimize-for-change) | Meta-Principle: Optimize for Change | change, future, cost |

## §3. Swift / SwiftUI / AppKit — [swift.md](swift.md)

| § | Section | Keywords |
|---|---------|----------|
| [§3.1](swift.md#§31-references) | References | Swift API Design Guidelines, SwiftUI Performance |
| [§3.2](swift.md#§32-logging) | Logging | os.log, Logger, subsystem, category |
| [§3.3](swift.md#§33-secure-storage) | Secure Storage | Keychain, UserDefaults, secrets |
| [§3.4](swift.md#§34-localization) | Localization | String(localized:), NSLocalizedString, .xcstrings |
| [§3.5](swift.md#§35-linting-and-formatting) | Linting and Formatting | SwiftLint, swift-format |
| [§3.6](swift.md#§36-shortcuts-and-automation) | Shortcuts and Automation | AppIntents, Shortcuts, Siri, AppleScript |
| [§3.7](swift.md#§37-previews) | Previews | #Preview, SwiftUI, render |
| [§3.8](swift.md#§38-dynamic-type) | Dynamic Type | Dynamic Type, font sizes, text scaling |
| [§3.9](swift.md#§39-accessibility-environment-values) | Accessibility Environment Values | reduceMotion, reduceTransparency, colorSchemeContrast |
| [§3.10](swift.md#§310-concurrency) | Concurrency | async/await, Task, actors, @MainActor |
| [§3.11](swift.md#§311-privacy) | Privacy | App Tracking Transparency, Privacy Report, NSUsageDescription |
| [§3.12](swift.md#§312-feature-flags) | Feature Flags | protocol, UserDefaults |
| [§3.13](swift.md#§313-analytics) | Analytics | protocol, os.log |

## §4. Kotlin / Compose / Ktor — [kotlin.md](kotlin.md)

| § | Section | Keywords |
|---|---------|----------|
| [§4.1](kotlin.md#§41-references) | References | Kotlin Conventions, Material Design 3, Architecture |
| [§4.2](kotlin.md#§42-logging) | Logging | Timber, android.util.Log |
| [§4.3](kotlin.md#§43-concurrency) | Concurrency | Coroutines, Dispatchers.IO, viewModelScope |
| [§4.4](kotlin.md#§44-secure-storage) | Secure Storage | EncryptedSharedPreferences, Android Keystore |
| [§4.5](kotlin.md#§45-localization) | Localization | strings.xml, stringResource, R.string |
| [§4.6](kotlin.md#§46-linting-and-formatting) | Linting and Formatting | ktlint, .editorconfig |
| [§4.7](kotlin.md#§47-shortcuts-and-automation) | Shortcuts and Automation | AppActions, Google Assistant, Intent |
| [§4.8](kotlin.md#§48-previews) | Previews | @Preview, Compose |
| [§4.9](kotlin.md#§49-font-scaling) | Font Scaling | fontScale, Configuration, 2x |
| [§4.10](kotlin.md#§410-accessibility-settings) | Accessibility Settings | animator_duration_scale, TalkBack, Switch Access |
| [§4.11](kotlin.md#§411-privacy) | Privacy | scoped storage, permissions, rationale |
| [§4.12](kotlin.md#§412-feature-flags) | Feature Flags | interface, SharedPreferences |
| [§4.13](kotlin.md#§413-analytics) | Analytics | interface, Timber |
| [§4.14](kotlin.md#§414-rtl-support) | RTL Support | supportsRtl, start/end |
| [§4.15](kotlin.md#§415-immutability) | Immutability | val, data class, StateFlow |

## §5. TypeScript / React / Web — [typescript.md](typescript.md)

| § | Section | Keywords |
|---|---------|----------|
| [§5.1](typescript.md#§51-linting-and-formatting) | Linting and Formatting | ESLint, Prettier, Stylelint |
| [§5.2](typescript.md#§52-accessibility-references) | Accessibility References | WCAG 2.1, WAI-ARIA |
| [§5.3](typescript.md#§53-accessibility-css-media-queries) | Accessibility CSS Media Queries | prefers-reduced-motion, prefers-contrast, forced-colors |
| [§5.4](typescript.md#§54-security) | Security | CSP, HttpOnly, cookies, sanitization, Do Not Track |
| [§5.5](typescript.md#§55-localization) | Localization | react-intl, i18next, FormatJS, message catalogs |
| [§5.6](typescript.md#§56-rtl-layout-support) | RTL Layout Support | CSS logical properties, margin-inline-start, dir |
| [§5.7](typescript.md#§57-testing) | Testing | Playwright, E2E, visual regression, Storybook |
| [§5.8](typescript.md#§58-concurrency) | Concurrency | Promise, async/await, Web Workers |
| [§5.9](typescript.md#§59-deep-linking) | Deep Linking | URL routing, shareable URL |
| [§5.10](typescript.md#§510-debug-mode) | Debug Mode | /debug, Ctrl+Shift+D, NODE_ENV |
| [§5.11](typescript.md#§511-feature-flags) | Feature Flags | interface, localStorage |
| [§5.12](typescript.md#§512-analytics) | Analytics | interface, console |
| [§5.13](typescript.md#§513-immutability) | Immutability | const, useState |

## §6. Python — [python.md](python.md)

| § | Section | Keywords |
|---|---------|----------|
| [§6.1](python.md#§61-no-external-dependencies-in-core-libraries) | No external dependencies in core libraries | stdlib, roadmap_lib, portable |
| [§6.2](python.md#§62-testing) | Testing | pytest, regression test, demo port 9888 |
| [§6.3](python.md#§63-type-hints) | Type hints | type hints, annotations, Python 3.9 |
| [§6.4](python.md#§64-file-paths) | File paths | pathlib, Path, os.path |
| [§6.5](python.md#§65-yaml-frontmatter) | YAML frontmatter | frontmatter, parse, roadmap_lib |
| [§6.6](python.md#§66-web-services) | Web services | Flask, REST API |
| [§6.7](python.md#§67-database) | Database | SQLite, WAL, sqlite3 |
| [§6.8](python.md#§68-use-roadmap_lib) | Use roadmap_lib | roadmap_lib, existing functions |
| [§6.9](python.md#§69-deterministic-ids) | Deterministic IDs | UUID, frontmatter, deterministic |
| [§6.10](python.md#§610-dashboard-service-is-display-only) | Dashboard service is display-only | dashboard, generic, display-only |
| [§6.11](python.md#§611-shell-scripts) | Shell scripts | main(), functions, composable |
| [§6.12](python.md#§612-logging) | Logging | logging, getLogger, __name__ |

## §7. C# / .NET — [csharp.md](csharp.md)

| § | Section | Keywords |
|---|---------|----------|
| [§7.1](csharp.md#§71-references) | References | C# Conventions, .NET Design Guidelines, Runtime Coding Style |
| [§7.2](csharp.md#§72-naming) | Naming | PascalCase, camelCase, _camelCase, I prefix, Async suffix |
| [§7.3](csharp.md#§73-nullable-reference-types) | Nullable Reference Types | Nullable, enable, null-forgiving, required, guard clause |
| [§7.4](csharp.md#§74-immutability) | Immutability | readonly, record, ImmutableList, init, with |
| [§7.5](csharp.md#§75-concurrency) | Concurrency | async/await, ConfigureAwait, CancellationToken, ValueTask |
| [§7.6](csharp.md#§76-dependency-injection) | Dependency Injection | Microsoft.Extensions.DependencyInjection, IOptions, Transient, Singleton |
| [§7.7](csharp.md#§77-logging) | Logging | ILogger, structured, LoggerMessage, source generator |
| [§7.8](csharp.md#§78-linting-and-formatting) | Linting and Formatting | .editorconfig, Roslyn, EnforceCodeStyleInBuild, dotnet format |
| [§7.9](csharp.md#§79-testing) | Testing | xUnit, FluentAssertions, NSubstitute, Fact, Theory |
| [§7.10](csharp.md#§710-secure-storage) | Secure Storage | DPAPI, ProtectedData, User Secrets |
| [§7.11](csharp.md#§711-privacy) | Privacy | capabilities, manifest, broadFileSystemAccess, consent |
| [§7.12](csharp.md#§712-feature-flags) | Feature Flags | IFeatureManager, Microsoft.FeatureManagement |
| [§7.13](csharp.md#§713-analytics) | Analytics | ILogger, interface |

## §8. Windows / WinUI 3 — [windows.md](windows.md)

| § | Section | Keywords |
|---|---------|----------|
| [§8.1](windows.md#§81-references) | References | WinUI 3, Windows App SDK, Fluent 2, WinUI Gallery |
| [§8.2](windows.md#§82-architecture) | Architecture | MVVM, CommunityToolkit.Mvvm, NavigationView, Frame |
| [§8.3](windows.md#§83-fluent-design) | Fluent Design | built-in controls, Segoe UI Variable, Segoe Fluent Icons |
| [§8.4](windows.md#§84-theming) | Theming | Light, Dark, High Contrast, ThemeResource, semantic colors |
| [§8.5](windows.md#§85-accessibility) | Accessibility | UI Automation, AutomationProperties, Accessibility Insights, Narrator |
| [§8.6](windows.md#§86-localization) | Localization | MRT Core, .resw, x:Uid, ResourceLoader |
| [§8.7](windows.md#§87-deep-linking--protocol-activation) | Deep Linking / Protocol Activation | uap:Protocol, AppInstance, GetActivatedEventArgs |
| [§8.8](windows.md#§88-app-notifications) | App Notifications | AppNotificationManager, AppNotificationBuilder, toast |
| [§8.9](windows.md#§89-high-dpi--display-scaling) | High DPI / Display Scaling | effective pixels, RasterizationScale, multi-scale assets |
| [§8.10](windows.md#§810-msix-packaging) | MSIX Packaging | MSIX, single-project, capabilities, signing |
| [§8.11](windows.md#§811-concurrency) | Concurrency | DispatcherQueue, TryEnqueue, UI thread |
| [§8.12](windows.md#§812-rtl-layout-support) | RTL Layout Support | FlowDirection, RightToLeft |
| [§8.13](windows.md#§813-logging) | Logging | ILogger, ETW, EventSource, Live Visual Tree |
| [§8.14](windows.md#§814-debug-mode) | Debug Mode | #if DEBUG, settings page |
| [§8.15](windows.md#§815-design-time-data) | Design-Time Data | d:DataContext, d:DesignInstance, XAML Hot Reload |

## §9. UI Design — [ui.md](ui.md)

| § | Section | Keywords |
|---|---------|----------|
| [§9.1](ui.md#§91-platform-design-languages) | Platform Design Languages | HIG, Material Design, Fluent, WCAG |
| [§9.2](ui.md#§92-visual-hierarchy) | Visual Hierarchy | focal point, primary action, size, weight, proximity |
| [§9.3](ui.md#§93-spacing) | Spacing | 4px, 8px grid, spacing scale, padding, margin |
| [§9.4](ui.md#§94-typography) | Typography | system font, body text, line height, paragraph width |
| [§9.5](ui.md#§95-color) | Color | semantic tokens, palette, contrast, dark mode |
| [§9.6](ui.md#§96-layout) | Layout | single-column, content-first, responsive, scroll direction |
| [§9.7](ui.md#§97-state-design) | State Design | loading, empty state, error state, skeleton, CTA |
| [§9.8](ui.md#§98-form-design) | Form Design | forms, validation, error messages, labels |
| [§9.8.1](ui.md#§981-layout) | Layout | single-column, top-aligned labels |
| [§9.8.2](ui.md#§982-validation) | Validation | blur, keystroke, submit |
| [§9.8.3](ui.md#§983-error-messages) | Error messages | inline, below field, icon, specific |
| [§9.8.4](ui.md#§984-other-principles) | Other principles | placeholder, pre-fill, optional fields |
| [§9.9](ui.md#§99-feedback-patterns) | Feedback Patterns | toast, snackbar, dialog, confirmation, destructive |
| [§9.10](ui.md#§910-touch--click-targets) | Touch & Click Targets | 44pt, 48dp, 40epx, 24px, hit area, spacing |
| [§9.11](ui.md#§911-animation--motion) | Animation & Motion | duration, easing, reduced-motion, spring |
| [§9.12](ui.md#§912-iconography) | Iconography | SF Symbols, Material Symbols, Segoe Fluent Icons, labels |
| [§9.13](ui.md#§913-data-display) | Data Display | list, table, cards, grid, sort, filter, search |

## §10. Networking — [networking.md](networking.md)

| § | Section | Keywords |
|---|---------|----------|
| [§10.1](networking.md#§101-references) | References | Microsoft REST, Google API Design, Zalando, RFC 9457, RFC 9111 |
| [§10.2](networking.md#§102-api-design) | API Design | REST, URL, HTTP methods, status codes, versioning |
| [§10.3](networking.md#§103-error-responses) | Error Responses | RFC 9457, Problem Details, application/problem+json |
| [§10.4](networking.md#§104-pagination) | Pagination | cursor, offset, next_cursor, has_more, page_token |
| [§10.5](networking.md#§105-retry-and-resilience) | Retry and Resilience | exponential backoff, jitter, circuit breaker, retryable |
| [§10.6](networking.md#§106-timeouts) | Timeouts | connection timeout, read timeout, 10s, 30s |
| [§10.7](networking.md#§107-caching) | Caching | Cache-Control, ETag, If-None-Match, stale-while-revalidate |
| [§10.8](networking.md#§108-offline-and-connectivity) | Offline and Connectivity | offline-first, optimistic updates, sync, conflict resolution |
| [§10.9](networking.md#§109-rate-limiting) | Rate Limiting | 429, Retry-After, RateLimit-Remaining, throttling |
| [§10.10](networking.md#§1010-real-time-communication) | Real-Time Communication | SSE, WebSocket, polling, EventSource |

## §11. Security — [security.md](security.md)

| § | Section | Keywords |
|---|---------|----------|
| [§11.1](security.md#§111-references) | References | OWASP, MASVS, MASTG, Mozilla TLS |
| [§11.2](security.md#§112-authentication) | Authentication | OAuth 2.0, OIDC, PKCE, system browser, BFF |
| [§11.3](security.md#§113-token-handling) | Token Handling | access token, refresh token, JWT, storage |
| [§11.3.1](security.md#§1131-access-tokens) | Access tokens | short-lived, 5-15 min, claims |
| [§11.3.2](security.md#§1132-refresh-tokens) | Refresh tokens | rotation, revocation, token family |
| [§11.3.3](security.md#§1133-token-refresh-strategy) | Token refresh strategy | proactive, 75% TTL, queue |
| [§11.3.4](security.md#§1134-secure-storage-per-platform) | Secure storage per platform | Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly |
| [§11.3.5](security.md#§1135-never-do-these) | Never do these | localStorage, URL params, alg:none |
| [§11.4](security.md#§114-authorization) | Authorization | RBAC, scopes, least privilege, BOLA, deny by default |
| [§11.5](security.md#§115-transport-security) | Transport Security | TLS 1.2, TLS 1.3, HSTS, certificate pinning, AEAD |
| [§11.6](security.md#§116-cors) | CORS | origin allowlist, preflight, credentials, misconfigurations |
| [§11.7](security.md#§117-content-security-policy) | Content Security Policy | CSP, nonce, strict-dynamic, frame-ancestors, report-only |
| [§11.8](security.md#§118-input-validation) | Input Validation | allowlist, parameterized queries, output encoding, file uploads |
| [§11.9](security.md#§119-sensitive-data) | Sensitive Data | data minimization, PII, field-level encryption, KMS |
| [§11.10](security.md#§1110-dependency-security) | Dependency Security | lockfiles, npm audit, pin versions, SRI, supply chain |
| [§11.11](security.md#§1111-security-headers-checklist) | Security Headers Checklist | HSTS, CSP, X-Content-Type-Options, Referrer-Policy |

## §12. Spec Writing Format — [specs.md](specs.md)

| § | Section | Keywords |
|---|---------|----------|
| [§12.1](specs.md#§121-frontmatter) | Frontmatter | version, status, created, platforms, dependencies |
| [§12.2](specs.md#§122-rfc-2119-keywords) | RFC 2119 Keywords | MUST, SHOULD, MAY, requirements |
| [§12.3](specs.md#§123-requirement-numbering) | Requirement Numbering | REQ-NNN, sequential, test vector |
| [§12.4](specs.md#§124-template-variables) | Template Variables | {{app_name}}, {{bundle_id}}, placeholders |
| [§12.5](specs.md#§125-standard-sections) | Standard Sections | Overview, Requirements, API Contract, Accessibility, Logging |
| [§12.6](specs.md#§126-test-vector-formats) | Test Vector Formats | behavioral table, data JSON, input/expected |
| [§12.7](specs.md#§127-logging-section) | Logging Section | log messages, subsystem, category, grep |
| [§12.8](specs.md#§128-privacy-section) | Privacy Section | data collected, storage, PII handling |
| [§12.9](specs.md#§129-feature-flags-section) | Feature Flags Section | flag keys, gating |
| [§12.10](specs.md#§1210-analytics-section) | Analytics Section | event names, property schemas |

## §13. Best Practices References — [best-practices-references.md](best-practices-references.md)

| § | Section | Keywords |
|---|---------|----------|
| [§13.1](best-practices-references.md#§131-apple) | Apple | HIG, Swift API Design, Accessibility, App Store |
| [§13.2](best-practices-references.md#§132-android) | Android | Material Design 3, Architecture, Kotlin, Google Play |
| [§13.3](best-practices-references.md#§133-web) | Web | WCAG, WAI-ARIA, OWASP, MDN |
| [§13.4](best-practices-references.md#§134-windows--net) | Windows / .NET | C# Conventions, .NET Guidelines, WinUI 3, Fluent, MSIX |
| [§13.5](best-practices-references.md#§135-ui-design) | UI Design | NNGroup, Visual Hierarchy, Form Design, Empty States |
| [§13.6](best-practices-references.md#§136-networking) | Networking | Microsoft REST, Google API, Zalando, RFC 9457, RFC 9111 |
| [§13.7](best-practices-references.md#§137-security) | Security | OWASP Top 10, Mobile Top 10, Cheat Sheets, Mozilla TLS, SLSA |
| [§13.8](best-practices-references.md#§138-cross-platform) | Cross-Platform | Nielsen Norman, MASVS, MASTG |
