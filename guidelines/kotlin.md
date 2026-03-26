# Kotlin / Compose / Ktor Conventions

Platform-specific guidance for Android development with Kotlin.

## References

1. Follow the [Kotlin Coding Conventions](https://kotlinlang.org/docs/coding-conventions.html) for all naming and style decisions.
2. Follow [Material Design 3](https://m3.material.io/) for UI components and theming.
3. Follow [Android Architecture Recommendations](https://developer.android.com/topic/architecture/recommendations) for app structure.

## Logging

Use [Timber](https://github.com/JakeWharton/timber) for structured logging:

```kotlin
Timber.d("PrimaryButton: tapped, starting async action")
Timber.d("PrimaryButton: async action completed (success, ${duration}ms)")
```

If no dependency is desired, use `android.util.Log` with consistent tags.

## Concurrency

Use Kotlin Coroutines for all async work. Run I/O on `Dispatchers.IO`. Use `viewModelScope` for ViewModel-scoped coroutines. Never block the main thread.

```kotlin
viewModelScope.launch(Dispatchers.IO) {
    val result = repository.fetch()
    withContext(Dispatchers.Main) { updateUi(result) }
}
```

## Secure Storage

Use `EncryptedSharedPreferences` or the Android Keystore for tokens, credentials, and sensitive data. Never store secrets in plain SharedPreferences.

## Localization

Use `strings.xml` resource files. Reference via `R.string.*` in code or `stringResource()` in Compose. No hardcoded user-facing strings.

## Linting and Formatting

Use [ktlint](https://pinterest.github.io/ktlint/) for both linting and formatting. Configure via `.editorconfig` at project root. Add as a Gradle plugin (`org.jlleitschuh.gradle.ktlint`).

## Shortcuts and Automation

Use `AppActions` for Google Assistant integration. Support `Intent`-based automation.

## Previews

All Compose components MUST include `@Preview` functions. Verification includes confirming preview functions compile.

## Font Scaling

Layouts MUST NOT break at 2x font size. Check `Configuration.fontScale` and test with large font settings enabled.

## Accessibility Settings

Components MUST respond to these Android accessibility settings:

| Setting | API | Action |
|---------|-----|--------|
| Remove Animations | `animator_duration_scale == 0` | Disable all custom animations |
| Font Scale | `Configuration.fontScale` | Ensure layouts handle 2x font size |
| High Contrast Text | System setting | Ensure text meets WCAG AA contrast ratios |
| Color Inversion | `ACCESSIBILITY_DISPLAY_INVERSION_ENABLED` | Mark media with `importantForAccessibility` |
| TalkBack | `AccessibilityManager` | All elements have `contentDescription` and proper roles |
| Switch Access | `AccessibilityManager` | All interactive elements are focusable and reachable |
| Dark Theme | `Configuration.uiMode` | Full dark theme support |
| Display Size | `displayMetrics.density` | Layouts must not break at larger display sizes |

## Privacy

Respect scoped storage, support per-app language preferences, and honor permission denials gracefully. Show rationale dialogs before runtime permission requests.

## Feature Flags

Interface + `SharedPreferences`-backed implementation as the default.

## Analytics

Interface + `Timber`-backed implementation as the default.

## RTL Support

Set `android:supportsRtl="true"` in the manifest. Use `start`/`end` instead of `left`/`right` in layouts. Force RTL in developer options for testing.

## Immutability

Use `val` by default. Use `data class` for value types. Introduce `var` only when mutation is required, and contain mutable state behind `StateFlow`.
