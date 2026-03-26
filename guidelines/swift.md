# Swift / SwiftUI / AppKit Conventions

Platform-specific guidance for Apple development with Swift.

## §3.1. References

1. Follow the [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/) for all naming and API surface decisions.
2. Follow the [SwiftUI Performance guide](https://developer.apple.com/documentation/Xcode/understanding-and-improving-swiftui-performance) when building views.

## §3.2. Logging

Use `os.log` via `Logger` from the `os` module:

```swift
import os

private let logger = Logger(
    subsystem: "{{bundle_id}}",
    category: "ComponentName"
)

logger.debug("PrimaryButton: tapped, starting async action")
```

- Subsystem MUST match the bundle ID
- Category MUST be one per component or flow
- Use `debug` level for UI flow instrumentation

## §3.3. Secure Storage

Use Keychain Services for tokens, credentials, and any sensitive data. Never store secrets in UserDefaults or plists.

## §3.4. Localization

Use `String(localized:)` (Swift 5.7+) or `NSLocalizedString`. Store strings in `.xcstrings` (Xcode 15+) or `.strings` files. No hardcoded user-facing strings.

## §3.5. Linting and Formatting

1. [SwiftLint](https://github.com/realm/SwiftLint) with `.swiftlint.yml` at project root. Enable `strict` mode. Add as SPM plugin or Xcode build phase.
2. [swift-format](https://github.com/swiftlang/swift-format) for auto-formatting.

## §3.6. Shortcuts and Automation

Use the `AppIntents` framework for Shortcuts and Siri integration. On macOS, support AppleScript via `NSScriptCommand` where appropriate.

## §3.7. Previews

All SwiftUI views MUST include `#Preview` blocks. Verification includes confirming previews render without crashes.

## §3.8. Dynamic Type

Layouts MUST NOT break at larger text sizes. Use Dynamic Type throughout — avoid fixed font sizes. Custom fonts must respond to the bold text accessibility setting.

## §3.9. Accessibility Environment Values

Components MUST respond to these SwiftUI environment values:

| Setting | Environment Key | Action |
|---------|----------------|--------|
| Reduce Motion | `\.accessibilityReduceMotion` | Replace animations with crossfades or instant transitions |
| Reduce Transparency | `\.accessibilityReduceTransparency` | Use opaque backgrounds instead of blurs/vibrancy |
| Differentiate Without Color | `\.accessibilityDifferentiateWithoutColor` | Add icons/shapes/patterns alongside color indicators |
| Increase Contrast | `\.colorSchemeContrast` | Use higher-contrast color pairs |
| Invert Colors | `isInvertColorsEnabled` | Mark images/video with `accessibilityIgnoresInvertColors` |
| Cross-Fade Transitions | `prefersCrossFadeTransitions` | Use cross-fade instead of slide/zoom transitions |

## §3.10. Concurrency

Use Swift Concurrency (`async`/`await`, `Task`, actors) for all async work. Never block the main thread. Use `@MainActor` for UI updates.

## §3.11. Privacy

Support App Tracking Transparency, App Privacy Report, and Private Relay compatibility. Include `NS*UsageDescription` keys with human-readable explanations for all permission prompts.

## §3.12. Feature Flags

Protocol + `UserDefaults`-backed implementation as the default.

## §3.13. Analytics

Protocol + `os.log`-backed implementation as the default.
