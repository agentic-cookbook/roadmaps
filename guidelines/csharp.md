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
