# Design: C# and Windows Coding Guidelines

## Summary

Add two new guideline files (`csharp.md` and `windows.md`) to `~/.claude/guidelines/` and update three existing files (`general.md`, `best-practices-references.md`, `CLAUDE.md`) for consistency.

## Scope

- **In scope:** C# language conventions (.NET 9 / C# 13), Windows desktop via WinUI 3 / Windows App SDK, updates to existing cross-platform references
- **Out of scope:** ASP.NET Core / server-side, WPF, .NET MAUI, Entity Framework

## Decisions

- Two files (language + platform) rather than one combined file
- WinUI 3 as the sole UI framework (WPF/MAUI deferred)
- .NET 9 / C# 13 baseline (not LTS .NET 8)
- Client-only — no server-side coverage

---

## File 1: `guidelines/csharp.md` — C# / .NET Conventions

### Header

```
# C# / .NET Conventions

Platform-specific guidance for C# development targeting .NET 9+.
```

### Sections

#### 1. References
Links to canonical Microsoft documentation:
- [C# Coding Conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [.NET Framework Design Guidelines](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/)
- [.NET Runtime Coding Style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)

#### 2. Naming
- `PascalCase` for types, methods, properties, public fields, constants, namespaces
- `camelCase` for parameters and local variables
- `_camelCase` (underscore prefix) for private instance fields
- `I` prefix for interfaces (e.g., `IDisposable`)
- `Async` suffix for async methods
- Constants use `PascalCase`, not `SCREAMING_SNAKE_CASE`

#### 3. Nullable Reference Types
- Enable `<Nullable>enable</Nullable>` in all projects
- Treat warnings as design signals: `string` means non-null, `string?` means nullable
- Avoid null-forgiving operator (`!`) — prefer `?? throw` or guard clauses
- Use `required` properties and constructor parameters for non-null initialization
- Use `[NotNull]`, `[MaybeNull]`, `[NotNullWhen]` from `System.Diagnostics.CodeAnalysis` for contracts

#### 4. Immutability
- Use `readonly` fields and `readonly struct` by default. Introduce mutability only when required.
- Prefer `System.Collections.Immutable` (`ImmutableList<T>`, `ImmutableDictionary<K,V>`) for shared collections
- Use `record` for DTOs, API responses, domain events, value objects
- Use `record struct` / `readonly record struct` for small immutable value types
- Prefer positional records for simple data carriers
- Use `init` setters and `required` keyword for mandatory properties
- Use `with` expressions for non-destructive mutation
- Contain mutable state behind `ObservableObject` (UI) or thread-safe wrappers
- Reserve `class` with mutable state for entities with identity semantics

#### 5. Concurrency
- `async`/`await` for all async work
- `ConfigureAwait(false)` in library code to avoid capturing sync context
- Never use `.Result` or `.Wait()` — causes deadlocks
- Never use `async void` except for event handlers
- Accept `CancellationToken` in all async APIs
- Use `ValueTask<T>` only when method frequently completes synchronously
- Use `Task.Run` for CPU-bound work, never on the UI thread

#### 6. Dependency Injection
- Constructor injection via `Microsoft.Extensions.DependencyInjection`
- Use interface types for dependencies, not concrete types
- `Transient` for lightweight stateless, `Scoped` for per-request, `Singleton` for thread-safe shared
- Never inject scoped into singleton (captive dependency)
- Use `IOptions<T>` / `IOptionsSnapshot<T>` for configuration binding
- Keep registrations in `Add*()` extension methods for modularity

#### 7. Logging
- Inject `ILogger<T>` via constructor (category = consuming class)
- Use structured message templates: `logger.LogInformation("Processing {OrderId}", orderId)`
- Never use string interpolation (`$"..."`) in log calls — bypasses structured logging
- Use `[LoggerMessage]` source generator attribute for high-performance hot paths
- Configure levels via `appsettings.json` per category

#### 8. Linting and Formatting
- `.editorconfig` at repo root for all code style rules
- Enable `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` in `.csproj`
- Enable `<AnalysisLevel>latest-recommended</AnalysisLevel>` for Roslyn analyzers
- Use `dotnet format` CLI for auto-fixing
- Supplement with [Roslynator](https://github.com/dotnet/roslynator) or [Meziantou.Analyzer](https://github.com/meziantou/Meziantou.Analyzer) for additional rules

#### 9. Testing
- [xUnit](https://xunit.net/) with `[Fact]` and `[Theory]`/`[InlineData]` for parameterized tests
- [FluentAssertions](https://fluentassertions.com/) for readable assertions
- [NSubstitute](https://nsubstitute.github.io/) for mocking
- Every change needs tests. Every bug fix needs a regression test.
- Prioritize unit tests over integration tests.

#### 10. Secure Storage
- Use [DPAPI](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata) (`ProtectedData.Protect`/`Unprotect` with `DataProtectionScope.CurrentUser`) for Windows-only local secrets
- Use [User Secrets](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) (`Microsoft.Extensions.Configuration.UserSecrets`) for development-time secrets only (plaintext JSON — not for production)
- Never store tokens or credentials in plaintext config files or app settings

#### 11. Feature Flags
- `IFeatureManager` interface + local JSON config as default
- Use `Microsoft.FeatureManagement` NuGet package
- Swap in Azure App Configuration for server-side flag evaluation later

#### 12. Privacy
- Declare only required capabilities in `Package.appxmanifest` — avoid `broadFileSystemAccess` unless essential
- Use DPAPI for local secret storage (see Secure Storage above)
- No PII in logs, even at debug level
- Respect user consent: app must remain functional if optional data collection is denied

#### 13. Analytics
- Interface + `ILogger`-backed implementation as the default
- Same pattern as other platforms: no direct coupling to any analytics backend

---

## File 2: `guidelines/windows.md` — Windows / WinUI 3 Conventions

### Header

```
# Windows / WinUI 3 Conventions

Platform-specific guidance for Windows desktop development with WinUI 3 and the Windows App SDK.
```

### Sections

#### 1. References
- [WinUI 3 / Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/)
- [Fluent 2 Design System](https://fluent2.microsoft.design/)
- [Windows App SDK (GitHub)](https://github.com/microsoft/WindowsAppSDK)
- [WinUI Gallery (GitHub)](https://github.com/microsoft/WinUI-Gallery)
- [Windows Design Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/)

#### 2. Architecture
- MVVM with [CommunityToolkit.Mvvm](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/) — source-generated `ObservableObject`, `RelayCommand`, messaging
- NavigationView + Frame for page-level navigation
- Navigation service abstraction in ViewModel layer — never manipulate Frame from code-behind
- Use [Template Studio](https://github.com/microsoft/TemplateStudio) for project scaffolding

#### 3. Fluent Design
- Use built-in WinUI 3 controls — they implement Fluent 2 natively
- Never custom-draw what a standard control can do
- Typography: Segoe UI Variable. Icons: Segoe Fluent Icons.
- Follow [Windows design guidance](https://learn.microsoft.com/en-us/windows/apps/design/) for layout, spacing, and navigation patterns

#### 4. Theming
- Tri-state theming: Light, Dark, High Contrast
- Set app-level via `Application.RequestedTheme`, override per-element with `FrameworkElement.RequestedTheme`
- Always use `ThemeResource` (not `StaticResource`) for colors/brushes — enables runtime theme switching
- Use semantic color resources (`TextFillColorPrimary`, `CardBackgroundFillColorDefault`) not hex values
- Define custom theme-aware colors in `ResourceDictionary` with `Default`/`Light`/`Dark` theme dictionaries

#### 5. Accessibility
- WinUI 3 controls expose UI Automation patterns automatically
- Set `AutomationProperties.Name` on interactive elements without visible text labels
- Use `AutomationProperties.LabeledBy` for form fields and `AutomationProperties.LiveSetting` for dynamic content
- High contrast support is automatic when using `ThemeResource` — never hard-code colors
- Test with [Accessibility Insights for Windows](https://accessibilityinsights.io/)
- Keyboard navigation: all interactive elements must be reachable via Tab, actionable via Enter/Space

Components MUST respond to these Windows accessibility settings:

| Setting | API / Detection | Action |
|---------|----------------|--------|
| High Contrast | `AccessibilitySettings.HighContrast` | Automatic via ThemeResource — verify custom visuals adapt |
| Animations Disabled | `UISettings.AnimationsEnabled` | Disable all custom animations and transitions |
| Text Scaling | `UISettings.TextScaleFactor` | Layouts must not break up to 225% text scale |
| Color Filters | System setting | Ensure UI is usable with color vision deficiency filters |
| Narrator | UI Automation tree | All elements have Name, Role, and appropriate patterns |
| Keyboard Navigation | Focus management | All interactive elements reachable via Tab, actionable via Enter/Space |
| Dark Theme | `Application.RequestedTheme` | Full dark theme support via ThemeResource |
| Caret Browsing | System setting | Non-interactive text should be navigable |

#### 6. Localization
- MRT Core with `.resw` resource files
- `x:Uid` directive in XAML for multi-property localization (e.g., `x:Uid="SaveButton"` maps to `SaveButton.Content`, `SaveButton.AutomationProperties.Name`)
- Folder structure: `Strings/<language-tag>/Resources.resw`
- Code-behind access via `Microsoft.Windows.ApplicationModel.Resources.ResourceLoader`
- No hardcoded user-facing strings

#### 7. Deep Linking / Protocol Activation
- Declare `<uap:Protocol Name="myapp"/>` in `Package.appxmanifest`
- Handle via `AppInstance.GetActivatedEventArgs()` in `App.OnLaunched`
- Parse URI to determine target page/state, navigate accordingly
- Use `AppInstance.FindOrRegisterForKey()` for single-instancing (recommended for deep links)

#### 8. App Notifications
- Use `AppNotificationManager` + `AppNotificationBuilder` fluent API
- Support text, images, buttons, progress bars, scheduled delivery
- Handle notification activation alongside protocol activation
- MSIX-packaged apps get notification identity automatically

#### 9. High DPI / Display Scaling
- XAML layout uses effective pixels (epx) — scaling is automatic
- Provide bitmap assets at multiple scales: `.scale-100`, `.scale-125`, `.scale-150`, `.scale-200`, `.scale-400`
- For custom rendering (Win2D, Direct3D), query `XamlRoot.RasterizationScale` and listen for `RasterizationScaleChanged`
- Never hard-code pixel sizes in code-behind

#### 10. MSIX Packaging
- Use single-project MSIX packaging model
- Declare capabilities minimally in `Package.appxmanifest`
- Sign packages with trusted certificate for sideloading
- Version numbering: `Major.Minor.Build.Revision`, monotonically increasing

#### 11. Logging
- `ILogger<T>` (same conventions as `csharp.md`)
- Use ETW tracing (`EventSource`) for system-level diagnostics and startup timing
- Use XAML Live Visual Tree for debugging visual tree issues

#### 12. Debug Mode
- Dev-only settings page guarded by `#if DEBUG`
- Include: feature flag overrides, analytics event log, environment info (version, OS, device)
- Access via navigation menu item visible only in debug builds

#### 13. Concurrency
- Use `DispatcherQueue.TryEnqueue` to marshal work back to the UI thread from background tasks
- Never access UI elements from non-UI threads
- See `csharp.md` for general async/await conventions

```csharp
DispatcherQueue.TryEnqueue(() =>
{
    StatusText.Text = "Updated from background";
});
```

#### 14. RTL Layout Support
- Set `FlowDirection="RightToLeft"` on the root element for RTL locales
- WinUI 3 XAML layout handles leading/trailing automatically when FlowDirection is set
- Mirror icons with directional meaning (forward/back arrows)
- Test with RTL language packs installed

#### 15. Design-Time Data
- Use `d:DataContext` and `d:DesignInstance` for XAML designer preview data
- Use XAML Hot Reload for live iteration during development

---

## File 3: Updates to `guidelines/general.md`

Add Windows/C# entries to existing platform-specific bullet lists:

| Rule | Addition |
|------|----------|
| 4 (No blocking main thread) | `**Windows/.NET**: async/await, Task.Run for CPU-bound, DispatcherQueue for UI updates` |
| 8 (Post-generation verification) | Add `dotnet build` / `dotnet test` to build/test command list |
| 9 (Logging) | `**Windows/.NET**: ILogger<T> from Microsoft.Extensions.Logging` |
| 10 (Deep linking) | `**Windows**: Protocol activation via uap:Protocol, AppInstance rich activation` |
| 11 (Scriptable) | `**Windows**: Protocol activation, command-line activation, AppInstance APIs` |
| 12 (Accessibility from day one) | `**Windows**: UI Automation patterns, Narrator testing, Accessibility Insights, 44epx minimum touch targets` |
| 13 (Localizability) | `**Windows**: .resw resource files with x:Uid in XAML, MRT Core ResourceLoader` |
| 14 (RTL) | `**Windows**: FlowDirection property. WinUI 3 handles leading/trailing automatically.` |
| 16.3 (Secure storage) | Add DPAPI to the list: `Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly cookies` |
| 20 (Debug mode) | `**Windows**: Debug-only settings page, guarded by #if DEBUG` |
| 21 (Linting) | Add row: `C# / .NET | Roslyn Analyzers + .editorconfig | dotnet format` |

---

## File 4: Updates to `guidelines/best-practices-references.md`

Add new section between "Web" and "Cross-Platform":

```markdown
## Windows / .NET

- [C# Coding Conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [.NET Framework Design Guidelines](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/)
- [WinUI 3 / Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/)
- [Fluent 2 Design System](https://fluent2.microsoft.design/)
- [Windows Accessibility](https://learn.microsoft.com/en-us/windows/apps/develop/accessibility)
- [MSIX Packaging](https://learn.microsoft.com/en-us/windows/msix/)
- [WinUI Gallery (GitHub)](https://github.com/microsoft/WinUI-Gallery)
```

---

## File 5: Updates to `~/.claude/CLAUDE.md`

Add to the guidelines listing:

```markdown
- `~/.claude/guidelines/csharp.md` — C# / .NET
- `~/.claude/guidelines/windows.md` — Windows / WinUI 3
```

---

## Implementation Order

1. Create `guidelines/csharp.md`
2. Create `guidelines/windows.md`
3. Update `guidelines/general.md` — add Windows entries to platform lists
4. Update `guidelines/best-practices-references.md` — add Windows/.NET section
5. Update `~/.claude/CLAUDE.md` — add guideline file listing
6. Run `install.sh` to symlink new files
7. Verify symlinks exist in `~/.claude/guidelines/`
