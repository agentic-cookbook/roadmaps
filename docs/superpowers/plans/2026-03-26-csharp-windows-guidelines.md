# C# and Windows Coding Guidelines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add C# / .NET and Windows / WinUI 3 coding guidelines, and update existing files (general.md, best-practices-references.md, CLAUDE.md) for cross-platform consistency.

**Architecture:** Two new markdown guideline files following the established pattern of existing platform files (swift.md, kotlin.md, typescript.md). Updates to three existing files to add Windows/C# entries to platform-specific bullet lists and reference sections.

**Tech Stack:** Markdown guidelines, shell (install.sh for symlinks)

**Spec:** `docs/superpowers/specs/2026-03-26-csharp-windows-guidelines-design.md`

---

### Task 1: Create `guidelines/csharp.md`

**Files:**
- Create: `guidelines/csharp.md`

- [ ] **Step 1: Create the file with full content**

```markdown
# C# / .NET Conventions

Platform-specific guidance for C# development targeting .NET 9+.

## References

1. Follow the [C# Coding Conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions) for all naming and style decisions.
2. Follow the [.NET Framework Design Guidelines](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/) for public API surface design.
3. Follow the [.NET Runtime Coding Style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md) as the canonical style reference.

## Naming

- `PascalCase` for types, methods, properties, public fields, constants, namespaces
- `camelCase` for parameters and local variables
- `_camelCase` (underscore prefix) for private instance fields
- `I` prefix for interfaces (e.g., `IDisposable`)
- `Async` suffix for async methods (e.g., `SaveAsync`)
- Constants use `PascalCase`, not `SCREAMING_SNAKE_CASE`
- Use `var` when the type is apparent from the right side of the assignment

## Nullable Reference Types

Enable `<Nullable>enable</Nullable>` in all projects. Treat warnings as design signals — `string` means non-null, `string?` means nullable.

- Avoid the null-forgiving operator (`!`) — prefer `?? throw` or guard clauses
- Use `required` properties and constructor parameters for non-null initialization
- Use `[NotNull]`, `[MaybeNull]`, `[NotNullWhen]` from `System.Diagnostics.CodeAnalysis` for contracts the compiler cannot infer

```csharp
// Good: required + guard clause
public required string Name { get; init; }

public void Process(string? input)
{
    ArgumentNullException.ThrowIfNull(input);
    // input is now non-null
}
```

## Immutability

Use `readonly` fields and `readonly struct` by default. Introduce mutability only when required.

- Prefer `System.Collections.Immutable` (`ImmutableList<T>`, `ImmutableDictionary<K,V>`) for shared collections
- Use `record` for DTOs, API responses, domain events, value objects
- Use `record struct` / `readonly record struct` for small immutable value types
- Prefer positional records (`record Person(string Name, int Age)`) for simple data carriers
- Use `init` setters and `required` keyword for mandatory properties
- Use `with` expressions for non-destructive mutation
- Contain mutable state behind `ObservableObject` (UI) or thread-safe wrappers
- Reserve `class` with mutable state for entities with identity semantics

```csharp
// Immutable DTO
public record OrderSummary(string OrderId, decimal Total, DateTime CreatedAt);

// Modified copy
var updated = order with { Total = 99.99m };

// Readonly value type
public readonly record struct Point(double X, double Y);
```

## Concurrency

Use `async`/`await` for all async work. Never block the main thread.

- `ConfigureAwait(false)` in library code to avoid capturing the synchronization context
- Never use `.Result` or `.Wait()` — causes deadlocks
- Never use `async void` except for event handlers
- Accept `CancellationToken` in all async APIs
- Use `ValueTask<T>` only when the method frequently completes synchronously
- Use `Task.Run` for CPU-bound work, never on the UI thread

```csharp
// Library code — ConfigureAwait(false)
public async Task<Data> FetchAsync(CancellationToken ct = default)
{
    var response = await _client.GetAsync(url, ct).ConfigureAwait(false);
    return await ParseAsync(response, ct).ConfigureAwait(false);
}

// Application code — no ConfigureAwait needed
public async Task OnLoadAsync()
{
    var data = await _service.FetchAsync();
    UpdateUI(data);
}
```

## Dependency Injection

Constructor injection via `Microsoft.Extensions.DependencyInjection`. Use interface types for dependencies, not concrete types.

- `Transient` for lightweight stateless services
- `Scoped` for per-request services
- `Singleton` for thread-safe shared state
- Never inject a scoped service into a singleton (captive dependency)
- Use `IOptions<T>` / `IOptionsSnapshot<T>` for configuration binding
- Keep registrations in `Add*()` extension methods for modularity

```csharp
public static IServiceCollection AddMyFeature(this IServiceCollection services)
{
    services.AddSingleton<IFeatureManager, LocalFeatureManager>();
    services.AddTransient<IOrderService, OrderService>();
    return services;
}
```

## Logging

Inject `ILogger<T>` via constructor injection. The generic parameter sets the log category to the consuming class.

- Use structured message templates: `logger.LogInformation("Processing {OrderId}", orderId)`
- **Never** use string interpolation (`$"..."`) in log calls — it bypasses structured logging and prevents log aggregation
- Use the `[LoggerMessage]` source generator attribute for high-performance hot paths
- Configure log levels per category via `appsettings.json`

```csharp
// Standard logging
private readonly ILogger<OrderService> _logger;

_logger.LogInformation("Processing order {OrderId} for {CustomerId}", orderId, customerId);

// High-performance logging via source generator
[LoggerMessage(Level = LogLevel.Debug, Message = "Cache hit for key {Key}")]
static partial void LogCacheHit(ILogger logger, string key);
```

## Linting and Formatting

1. [`.editorconfig`](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/) at repo root for all code style rules.
2. Enable Roslyn analyzers in `.csproj`:

```xml
<PropertyGroup>
  <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
  <AnalysisLevel>latest-recommended</AnalysisLevel>
</PropertyGroup>
```

3. Use `dotnet format` CLI for auto-fixing.
4. Supplement with [Roslynator](https://github.com/dotnet/roslynator) or [Meziantou.Analyzer](https://github.com/meziantou/Meziantou.Analyzer) for additional rules.

## Testing

1. [xUnit](https://xunit.net/) with `[Fact]` for single tests and `[Theory]`/`[InlineData]` for parameterized tests.
2. [FluentAssertions](https://fluentassertions.com/) for readable assertions.
3. [NSubstitute](https://nsubstitute.github.io/) for mocking.
4. Every change needs tests. Every bug fix needs a regression test.
5. Prioritize unit tests over integration tests.

```csharp
[Fact]
public void ParseOrder_WithValidInput_ReturnsOrder()
{
    var result = OrderParser.Parse(validJson);
    result.Should().NotBeNull();
    result.OrderId.Should().Be("ORD-123");
}

[Theory]
[InlineData("", false)]
[InlineData("valid@email.com", true)]
[InlineData("no-at-sign", false)]
public void IsValidEmail_ReturnsExpected(string input, bool expected)
{
    EmailValidator.IsValid(input).Should().Be(expected);
}
```

## Secure Storage

- Use [DPAPI](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata) (`ProtectedData.Protect`/`Unprotect` with `DataProtectionScope.CurrentUser`) for Windows-only local secrets
- Use [User Secrets](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) (`Microsoft.Extensions.Configuration.UserSecrets`) for development-time secrets only (plaintext JSON — not for production)
- Never store tokens or credentials in plaintext config files or app settings

## Privacy

- Declare only required capabilities in `Package.appxmanifest` — avoid `broadFileSystemAccess` unless essential
- Use DPAPI for local secret storage (see Secure Storage above)
- No PII in logs, even at debug level
- Respect user consent: app must remain functional if optional data collection is denied

## Feature Flags

`IFeatureManager` interface + local JSON config as the default. Use the `Microsoft.FeatureManagement` NuGet package. Swap in Azure App Configuration for server-side flag evaluation later.

## Analytics

Interface + `ILogger`-backed implementation as the default. Same pattern as other platforms: no direct coupling to any analytics backend.
```

- [ ] **Step 2: Verify the file renders correctly**

Run: `wc -l guidelines/csharp.md`
Expected: ~170 lines

- [ ] **Step 3: Commit**

```bash
git add guidelines/csharp.md
git commit -m "feat: add C# / .NET coding guidelines"
```

---

### Task 2: Create `guidelines/windows.md`

**Files:**
- Create: `guidelines/windows.md`

- [ ] **Step 1: Create the file with full content**

```markdown
# Windows / WinUI 3 Conventions

Platform-specific guidance for Windows desktop development with WinUI 3 and the Windows App SDK.

## References

1. [WinUI 3 / Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/) — the primary UI framework for Windows desktop apps.
2. [Fluent 2 Design System](https://fluent2.microsoft.design/) — Microsoft's cross-platform design system.
3. [Windows Design Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/) — layout, navigation, typography, color, and motion.
4. [WinUI Gallery (GitHub)](https://github.com/microsoft/WinUI-Gallery) — interactive reference for all WinUI 3 controls.
5. [Windows App SDK (GitHub)](https://github.com/microsoft/WindowsAppSDK) — releases, issues, and roadmap.

## Architecture

Use MVVM with [CommunityToolkit.Mvvm](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/) — source-generated `ObservableObject`, `RelayCommand`, and messaging.

- NavigationView + Frame for page-level navigation
- Navigation service abstraction in the ViewModel layer — never manipulate Frame from code-behind
- Use [Template Studio](https://github.com/microsoft/TemplateStudio) for project scaffolding with MVVM, navigation, and theming pre-wired

```csharp
// ViewModel with CommunityToolkit.Mvvm source generators
[ObservableObject]
public partial class MainViewModel
{
    [ObservableProperty]
    private string _title = "Home";

    [RelayCommand]
    private async Task LoadDataAsync()
    {
        var data = await _dataService.FetchAsync();
        Title = data.Name;
    }
}
```

## Fluent Design

Use built-in WinUI 3 controls — they implement Fluent 2 natively. Never custom-draw what a standard control can do.

- Typography: Segoe UI Variable
- Icons: Segoe Fluent Icons
- Follow [Windows design guidance](https://learn.microsoft.com/en-us/windows/apps/design/) for layout, spacing, and navigation patterns

## Theming

WinUI 3 supports tri-state theming: Light, Dark, and High Contrast.

- Set app-level theme via `Application.RequestedTheme`, override per-element with `FrameworkElement.RequestedTheme`
- Always use `ThemeResource` (not `StaticResource`) for colors and brushes — enables runtime theme switching
- Use semantic color resources (`TextFillColorPrimary`, `CardBackgroundFillColorDefault`) not hex values
- Define custom theme-aware colors in a `ResourceDictionary` with `Default`/`Light`/`Dark` theme dictionaries

```xml
<!-- Good: semantic theme resource -->
<TextBlock Foreground="{ThemeResource TextFillColorPrimaryBrush}" />

<!-- Bad: hard-coded color -->
<TextBlock Foreground="#FFFFFF" />
```

## Accessibility

WinUI 3 controls expose [UI Automation](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview) patterns automatically. Set `AutomationProperties.Name` on interactive elements that lack visible text labels.

- Use `AutomationProperties.LabeledBy` for form fields
- Use `AutomationProperties.LiveSetting` for dynamic content regions
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

## Localization

Use MRT Core with `.resw` resource files. The `x:Uid` directive in XAML binds control properties to resource keys.

- `x:Uid="SaveButton"` maps to `SaveButton.Content`, `SaveButton.AutomationProperties.Name`, etc. in the `.resw` file
- Folder structure: `Strings/<language-tag>/Resources.resw` (e.g., `Strings/en-US/Resources.resw`)
- Code-behind access via `Microsoft.Windows.ApplicationModel.Resources.ResourceLoader`
- No hardcoded user-facing strings

```xml
<!-- XAML: localized via x:Uid -->
<Button x:Uid="SaveButton" />
```

## Deep Linking / Protocol Activation

Declare protocol handlers in `Package.appxmanifest` and handle activation through the Windows App SDK lifecycle APIs.

- Declare: `<uap:Protocol Name="myapp"/>` in manifest
- Handle via `AppInstance.GetActivatedEventArgs()` in `App.OnLaunched`
- Parse URI to determine target page/state, navigate accordingly
- Use `AppInstance.FindOrRegisterForKey()` for single-instancing (recommended for deep links)

## App Notifications

Use `AppNotificationManager` + `AppNotificationBuilder` fluent API for local notifications.

- Support text, images, buttons with activation arguments, progress bars, scheduled delivery
- Handle notification activation alongside protocol activation
- MSIX-packaged apps get notification identity automatically

## High DPI / Display Scaling

XAML layout uses effective pixels (epx) — scaling is automatic for all XAML-rendered content.

- Provide bitmap assets at multiple scales: `.scale-100`, `.scale-125`, `.scale-150`, `.scale-200`, `.scale-400`
- For custom rendering (Win2D, Direct3D interop), query `XamlRoot.RasterizationScale` and listen for `RasterizationScaleChanged`
- Never hard-code pixel sizes in code-behind — rely on XAML layout and the scaling system

## MSIX Packaging

- Use the single-project MSIX packaging model
- Declare capabilities minimally in `Package.appxmanifest`
- Sign packages with a trusted certificate for sideloading
- Version numbering: `Major.Minor.Build.Revision`, monotonically increasing

## Concurrency

See `csharp.md` for general async/await conventions. For WinUI 3 specifically:

- Use `DispatcherQueue.TryEnqueue` to marshal work back to the UI thread from background tasks
- Never access UI elements from non-UI threads

```csharp
DispatcherQueue.TryEnqueue(() =>
{
    StatusText.Text = "Updated from background";
});
```

## RTL Layout Support

- Set `FlowDirection="RightToLeft"` on the root element for RTL locales
- WinUI 3 XAML layout handles leading/trailing automatically when FlowDirection is set
- Mirror icons with directional meaning (forward/back arrows)
- Do NOT mirror non-directional icons (checkmarks, clocks)
- Test with RTL language packs installed

## Logging

`ILogger<T>` (same conventions as `csharp.md`). Additionally:

- Use ETW tracing (`EventSource`) for system-level diagnostics and startup timing
- Use XAML Live Visual Tree in Visual Studio for debugging visual tree issues
- Use [Visual Studio Performance Profiler](https://learn.microsoft.com/en-us/visualstudio/profiling/) for CPU, memory, and UI responsiveness analysis

## Debug Mode

Dev-only settings page guarded by `#if DEBUG`:

- Feature flag overrides
- Analytics event log
- Environment info (app version, OS version, device)
- Access via navigation menu item visible only in debug builds

## Design-Time Data

- Use `d:DataContext` and `d:DesignInstance` for XAML designer preview data
- Use XAML Hot Reload for live iteration during development
```

- [ ] **Step 2: Verify the file renders correctly**

Run: `wc -l guidelines/windows.md`
Expected: ~180 lines

- [ ] **Step 3: Commit**

```bash
git add guidelines/windows.md
git commit -m "feat: add Windows / WinUI 3 coding guidelines"
```

---

### Task 3: Update `guidelines/general.md` — add Windows entries

**Files:**
- Modify: `guidelines/general.md`

- [ ] **Step 1: Add Windows entry to Rule 4 (No blocking main thread)**

After the `**Python**` bullet in the async primitives list, add:
```
- **Windows/.NET**: `async`/`await`, `Task.Run` for CPU-bound work, `DispatcherQueue` for UI updates
```

- [ ] **Step 2: Add Windows entry to Rule 8 (Post-generation verification)**

In the Build step, add `dotnet build` to the command list:
```
1. **Build**: Compile for all target platforms (`xcodebuild`, `./gradlew build`, `npm run build`, `dotnet build`)
```

- [ ] **Step 3: Add Windows entry to Rule 9 (Instrumented logging)**

After the `**Python**` bullet, add:
```
- **Windows/.NET**: `ILogger<T>` from `Microsoft.Extensions.Logging` — category per class via generic parameter
```

- [ ] **Step 4: Add Windows entry to Rule 10 (Deep linking)**

After the `**Web**` bullet, add:
```
- **Windows**: Protocol activation via `<uap:Protocol>` declaration in manifest. `AppInstance.GetActivatedEventArgs()` for rich activation handling.
```

- [ ] **Step 5: Add Windows entry to Rule 11 (Scriptable and automatable)**

After the `**Web**` bullet, add:
```
- **Windows**: Protocol activation, command-line activation, `AppInstance` APIs. WinUI 3 has limited scripting support compared to other platforms.
```

- [ ] **Step 6: Add Windows entry to Rule 12 (Accessibility from day one)**

This rule has no platform bullets currently — it's a numbered list. After item 6, add a blank line and:
```
Platform-specific tooling:
- **Windows**: UI Automation patterns, Narrator testing, [Accessibility Insights](https://accessibilityinsights.io/), minimum 40x40 epx recommended touch targets
```

- [ ] **Step 7: Add Windows entry to Rule 13 (Localizability)**

After the `**Web**` bullet, add:
```
- **Windows**: `.resw` resource files with `x:Uid` in XAML. `ResourceLoader` from MRT Core for code-behind access.
```

- [ ] **Step 8: Add Windows entry to Rule 14 (RTL layout support)**

After the `**Web**` platform note, add:
```
- **Windows**: Use `FlowDirection` property. WinUI 3 XAML handles leading/trailing automatically.
```

- [ ] **Step 9: Update Rule 16.3 (Secure storage)**

Change the secure storage list from:
```
Tokens and credentials MUST use platform secure storage (Keychain, EncryptedSharedPreferences, HttpOnly cookies).
```
To:
```
Tokens and credentials MUST use platform secure storage (Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly cookies).
```

- [ ] **Step 10: Add Windows entry to Rule 20 (Debug mode)**

After the `**Web**` bullet, add:
```
- **Windows**: Debug-only settings page, guarded by `#if DEBUG`
```

- [ ] **Step 11: Add C#/.NET row to Rule 21 (Linting) table**

Add row to the table:
```
| C# / .NET | Roslyn Analyzers + .editorconfig | dotnet format |
```

- [ ] **Step 12: Commit**

```bash
git add guidelines/general.md
git commit -m "feat: add Windows/.NET entries to general coding guidelines"
```

---

### Task 4: Update `guidelines/best-practices-references.md`

**Files:**
- Modify: `guidelines/best-practices-references.md`

- [ ] **Step 1: Add Windows / .NET section between "Web" and "Cross-Platform"**

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

- [ ] **Step 2: Commit**

```bash
git add guidelines/best-practices-references.md
git commit -m "feat: add Windows/.NET references to best-practices-references"
```

---

### Task 5: Update `~/.claude/CLAUDE.md` — add guideline entries

**Files:**
- Modify: `~/.claude/CLAUDE.md` (symlinked from dotfiles repo)

- [ ] **Step 1: Add C# and Windows entries to the guidelines listing**

After the `python.md` line and before the `specs.md` line, add:
```
- `~/.claude/guidelines/csharp.md` — C# / .NET
- `~/.claude/guidelines/windows.md` — Windows / WinUI 3
```

- [ ] **Step 2: Commit and push in the dotfiles repo**

CLAUDE.md is symlinked from `/Users/mfullerton/projects/dotfiles/claude/CLAUDE.md`. Commit and push there:
```bash
cd /Users/mfullerton/projects/dotfiles
git add claude/CLAUDE.md
git commit -m "feat: add C# and Windows guideline entries"
git push
```

---

### Task 6: Install and verify symlinks

**Files:**
- No file changes — verification only

- [ ] **Step 1: Run install.sh**

```bash
cd /Users/mfullerton/projects/cat-herding
bash install.sh
```

Expected: output includes `[symlinked] csharp.md` and `[symlinked] windows.md` (or `[ok]` if already linked)

- [ ] **Step 2: Verify symlinks exist**

```bash
ls -la ~/.claude/guidelines/csharp.md ~/.claude/guidelines/windows.md
```

Expected: both are symlinks pointing to `/Users/mfullerton/projects/cat-herding/guidelines/csharp.md` and `windows.md`

- [ ] **Step 3: Verify content is readable**

```bash
head -5 ~/.claude/guidelines/csharp.md
head -5 ~/.claude/guidelines/windows.md
```

Expected: first 5 lines of each file match the headers written in Tasks 1 and 2

---

### Task 7: Update README.md with Guidelines section

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a Guidelines section after the Agents section**

After the last agent entry, add:

```markdown
## Coding Guidelines

Shared coding guidelines installed to `~/.claude/guidelines/` via `install.sh`. These are referenced by `CLAUDE.md` and apply to all projects using the matching language/platform.

| File | Scope |
|------|-------|
| `general.md` | Universal rules (all projects) |
| `engineering-principles.md` | Core engineering principles |
| `swift.md` | Swift / SwiftUI / AppKit |
| `kotlin.md` | Kotlin / Compose / Ktor |
| `typescript.md` | TypeScript / React / Web |
| `python.md` | Python (cat-herding conventions) |
| `csharp.md` | C# / .NET |
| `windows.md` | Windows / WinUI 3 |
| `specs.md` | Spec writing format |
| `best-practices-references.md` | External reference links |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add Coding Guidelines section to README"
```
