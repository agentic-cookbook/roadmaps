# Windows / WinUI 3 Conventions

Platform-specific guidance for Windows desktop development with WinUI 3 and the Windows App SDK.

## §8.1. References

1. [WinUI 3 / Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/) — the primary UI framework for Windows desktop apps.
2. [Fluent 2 Design System](https://fluent2.microsoft.design/) — Microsoft's cross-platform design system.
3. [Windows Design Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/) — layout, navigation, typography, color, and motion.
4. [WinUI Gallery (GitHub)](https://github.com/microsoft/WinUI-Gallery) — interactive reference for all WinUI 3 controls.
5. [Windows App SDK (GitHub)](https://github.com/microsoft/WindowsAppSDK) — releases, issues, and roadmap.

## §8.2. Architecture

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

## §8.3. Fluent Design

Use built-in WinUI 3 controls — they implement Fluent 2 natively. Never custom-draw what a standard control can do.

- Typography: Segoe UI Variable
- Icons: Segoe Fluent Icons
- Follow [Windows design guidance](https://learn.microsoft.com/en-us/windows/apps/design/) for layout, spacing, and navigation patterns

## §8.4. Theming

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

## §8.5. Accessibility

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

## §8.6. Localization

Use MRT Core with `.resw` resource files. The `x:Uid` directive in XAML binds control properties to resource keys.

- `x:Uid="SaveButton"` maps to `SaveButton.Content`, `SaveButton.AutomationProperties.Name`, etc. in the `.resw` file
- Folder structure: `Strings/<language-tag>/Resources.resw` (e.g., `Strings/en-US/Resources.resw`)
- Code-behind access via `Microsoft.Windows.ApplicationModel.Resources.ResourceLoader`
- No hardcoded user-facing strings

```xml
<!-- XAML: localized via x:Uid -->
<Button x:Uid="SaveButton" />
```

## §8.7. Deep Linking / Protocol Activation

Declare protocol handlers in `Package.appxmanifest` and handle activation through the Windows App SDK lifecycle APIs.

- Declare: `<uap:Protocol Name="myapp"/>` in manifest
- Handle via `AppInstance.GetActivatedEventArgs()` in `App.OnLaunched`
- Parse URI to determine target page/state, navigate accordingly
- Use `AppInstance.FindOrRegisterForKey()` for single-instancing (recommended for deep links)

## §8.8. App Notifications

Use `AppNotificationManager` + `AppNotificationBuilder` fluent API for local notifications.

- Support text, images, buttons with activation arguments, progress bars, scheduled delivery
- Handle notification activation alongside protocol activation
- MSIX-packaged apps get notification identity automatically

## §8.9. High DPI / Display Scaling

XAML layout uses effective pixels (epx) — scaling is automatic for all XAML-rendered content.

- Provide bitmap assets at multiple scales: `.scale-100`, `.scale-125`, `.scale-150`, `.scale-200`, `.scale-400`
- For custom rendering (Win2D, Direct3D interop), query `XamlRoot.RasterizationScale` and listen for `RasterizationScaleChanged`
- Never hard-code pixel sizes in code-behind — rely on XAML layout and the scaling system

## §8.10. MSIX Packaging

- Use the single-project MSIX packaging model
- Declare capabilities minimally in `Package.appxmanifest`
- Sign packages with a trusted certificate for sideloading
- Version numbering: `Major.Minor.Build.Revision`, monotonically increasing

## §8.11. Concurrency

See §7.5 for general async/await conventions. For WinUI 3 specifically:

- Use `DispatcherQueue.TryEnqueue` to marshal work back to the UI thread from background tasks
- Never access UI elements from non-UI threads

```csharp
DispatcherQueue.TryEnqueue(() =>
{
    StatusText.Text = "Updated from background";
});
```

## §8.12. RTL Layout Support

- Set `FlowDirection="RightToLeft"` on the root element for RTL locales
- WinUI 3 XAML layout handles leading/trailing automatically when FlowDirection is set
- Mirror icons with directional meaning (forward/back arrows)
- Do NOT mirror non-directional icons (checkmarks, clocks)
- Test with RTL language packs installed

## §8.13. Logging

`ILogger<T>` (same conventions as `csharp.md`). Additionally:

- Use ETW tracing (`EventSource`) for system-level diagnostics and startup timing
- Use XAML Live Visual Tree in Visual Studio for debugging visual tree issues
- Use [Visual Studio Performance Profiler](https://learn.microsoft.com/en-us/visualstudio/profiling/) for CPU, memory, and UI responsiveness analysis

## §8.14. Debug Mode

Dev-only settings page guarded by `#if DEBUG`:

- Feature flag overrides
- Analytics event log
- Environment info (app version, OS version, device)
- Access via navigation menu item visible only in debug builds

## §8.15. Design-Time Data

- Use `d:DataContext` and `d:DesignInstance` for XAML designer preview data
- Use XAML Hot Reload for live iteration during development
