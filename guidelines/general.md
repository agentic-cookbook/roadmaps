# General Coding Guidelines

Universal rules that apply to all projects regardless of platform or language.

## 1. Prefer native controls and libraries

Always use the platform's built-in frameworks before custom implementations. Swift Concurrency over raw threads. Room/SwiftData over raw SQLite. Fetch API over custom HTTP.

When generating a component, explicitly note which native controls are being used and why. If there is ambiguity about whether a native control fits, ask the user before proceeding.

## 2. For novel components, prefer proven open-source solutions

When no native solution exists, research battle-tested open-source libraries and present options to the user before building a custom solution. A custom implementation can always be chosen instead, but it should be a deliberate decision, not a default.

## 3. Surface all design decisions

Any choice the LLM makes that affects behavior or structure must be explicitly noted and approved by the user. Record approved decisions in the relevant spec or document's **Design Decisions** section so all platform implementations stay consistent.

## 4. No blocking the main thread

All lengthy work must run on background threads/tasks using platform async primitives:

- **Apple**: Swift Concurrency (`async`/`await`, `Task`, actors)
- **Android**: Kotlin Coroutines (`viewModelScope`, `Dispatchers.IO`)
- **Web**: `Promise`/`async`, Web Workers
- **Python**: `asyncio`, threading for I/O

Never block the main/UI thread.

## 5. Always show progress

When the UI is waiting on an async task:

- Show **determinate progress** (progress bar with percentage) when total work is known
- Show **indeterminate progress** (spinner, skeleton, shimmer) when it is not
- Never show a frozen or unresponsive UI

## 6. Comprehensive unit testing

Prioritize unit tests over integration tests. Test state transitions, edge cases, serialization round-trips. Every implementation should include a corresponding test file. UI tests are fragile — prefer testing component logic as unit tests.

## 7. Small, atomic commits

One logical change per commit. A change may touch multiple files if they are part of the same concept. Commits should happen as work progresses — do not batch up unrelated changes.

## 8. Post-generation verification

Every generated artifact must be verified:

1. **Build**: Compile for all target platforms (`xcodebuild`, `./gradlew build`, `npm run build`)
2. **Test**: Run the full test suite — all tests must pass
3. **Lint**: Run the platform linter (see Rule 21)
4. **Log verification**: Build, run, and grep for expected log messages from the Logging section
5. **Accessibility audit**: Verify VoiceOver/TalkBack labels, tap target minimums (44pt iOS, 48dp Android), contrast ratios
6. **Code review against best practices**: Check against platform best practices references

If any step fails, fix the issue before considering the work complete.

## 9. Instrumented logging

Every component and flow must be instrumented with structured logging using the platform's best-in-class framework:

- **Apple**: `os.log` (`Logger` from `os`) — subsystem matching bundle ID, category per component
- **Android**: `Timber` (or `android.util.Log`)
- **Web**: `console` with structured prefixes, or `pino`/`winston` in Node
- **Python**: `logging` module with module-level loggers

Use `debug` level for flow instrumentation. Log state transitions, user interactions, async task start/completion/failure, and branching logic.

## 10. Deep linking

All significant feature points and views MUST be deep linkable using the platform's native URL/deep link mechanism:

- **Apple**: Universal Links + custom URL schemes. `onOpenURL` in SwiftUI, `NavigationPath` for state restoration.
- **Android**: App Links + intent filters. Navigation component deep link support.
- **Web**: URL routing. Every view should have a unique, shareable URL.

Each spec SHOULD include a **Deep Linking** section defining URL patterns.

## 11. Scriptable and automatable

Components and flows SHOULD be scriptable where the platform supports it:

- **Apple (macOS)**: `AppIntents` for Shortcuts, AppleScript via `NSScriptCommand`
- **Apple (iOS)**: `AppIntents` for Shortcuts and Siri integration
- **Android**: `AppActions` for Google Assistant, `Intent`-based automation
- **Web**: API endpoints or query parameter-driven actions

## 12. Accessibility from day one

All components MUST integrate with platform accessibility APIs from initial implementation:

1. Semantic roles and labels on all interactive elements
2. VoiceOver (Apple) / TalkBack (Android) / screen reader (Web) full support
3. Keyboard and switch control navigation
4. Dynamic Type / font scaling — layouts MUST NOT break at larger text sizes
5. WCAG AA minimum contrast (4.5:1 for text, 3:1 for large text)
6. Meaningful focus order following visual layout

## 13. Localizability

All user-facing strings MUST be localizable — no hardcoded strings:

- **Apple**: `String(localized:)` or `NSLocalizedString`. Store in `.xcstrings` or `.strings`.
- **Android**: `strings.xml` resources. Reference via `R.string.*` or `stringResource()`.
- **Web**: i18n library (`react-intl`, `i18next`). Extract to message catalogs.

## 14. RTL layout support

All layouts MUST support right-to-left languages:

1. Use **leading/trailing** (not left/right) for alignment and padding
2. Mirror icons with directional meaning (forward/back arrows)
3. Do NOT mirror non-directional icons (checkmarks, clocks)
4. Test with RTL locale enabled

Platform notes:
- **Apple**: Use `.environment(\.layoutDirection, .rightToLeft)` in previews. SwiftUI handles leading/trailing automatically.
- **Android**: Set `android:supportsRtl="true"`. Use `start`/`end` instead of `left`/`right`.
- **Web**: Use `dir="rtl"` attribute. Use CSS logical properties (`margin-inline-start` not `margin-left`).

## 15. Respect accessibility display options

Components MUST respond to platform accessibility and display settings including reduced motion, high contrast, color inversion, bold text, and grayscale. See platform-specific files for the full list of settings and environment keys.

## 16. Privacy and security by default

1. **Data minimization**: Collect only what is needed. Prefer on-device processing.
2. **Consent**: Opt-in for non-essential data collection. Honor "deny" gracefully — the app must remain functional.
3. **Secure storage**: Tokens and credentials MUST use platform secure storage (Keychain, EncryptedSharedPreferences, HttpOnly cookies).
4. **No PII logging**: Never log personally identifiable information, even at debug level.
5. **TLS only**: All network communication MUST use HTTPS.
6. **Input sanitization**: Sanitize all user input before display (prevent XSS, injection).

Each spec SHOULD include a **Privacy** section documenting data collected and how it is stored.

## 17. Feature flags

All features MUST be gated behind feature flags from initial implementation. Define a `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`), provide a local default implementation (UserDefaults/SharedPreferences/localStorage), swap in a backend implementation later via DI.

Each spec SHOULD list flag keys in a **Feature Flags** section.

## 18. Analytics

All significant user actions MUST be instrumented via an `AnalyticsProvider` interface (`track(event, properties)`). No direct coupling to any analytics backend. Provide a logging-only default; swap in a backend (Mixpanel, Amplitude, PostHog) later.

Each spec SHOULD define events in an **Analytics** section.

## 19. A/B testing

Features that may need experimentation SHOULD support variant assignment via an `ExperimentProvider` interface (`variant(key) -> String`). Local default with debug panel override.

## 20. Debug mode

Apps MUST include a debug-only configuration panel (not in release builds):

- Feature flag overrides
- Analytics event log
- A/B test variant picker
- Environment info (version, build, OS, device)

Access methods:
- **Apple (iOS)**: Shake gesture, guarded by `#if DEBUG`
- **Apple (macOS)**: Debug menu item, guarded by `#if DEBUG`
- **Android**: Shake gesture, guarded by `BuildConfig.DEBUG`
- **Web**: `/debug` route, guarded by `NODE_ENV === 'development'`

## 21. Linting from day one

All projects MUST include linting configured from initial generation:

| Platform | Linter | Formatter |
|----------|--------|-----------|
| Swift | SwiftLint | swift-format |
| Kotlin | ktlint | ktlint |
| TypeScript | ESLint | Prettier |

Linter config MUST be committed. Linting MUST run as part of the build or pre-commit process. Formatting MUST be auto-fixable.
