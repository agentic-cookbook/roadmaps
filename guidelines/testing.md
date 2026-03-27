# Testing Guidelines

Cross-platform testing principles, patterns, and tools. Consolidates and extends the
testing guidance in CG-1.6 (unit testing), CG-1.8 (post-generation verification), and
platform-specific testing sections.

## CG-14.1. References

1. [Google SWE Book Ch. 11: Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html)
2. [Martin Fowler: Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
3. [Kent Beck: Test Desiderata](https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b3)
4. [Martin Fowler: Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)
5. [Martin Fowler: Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
6. [ISTQB Foundation Syllabus](https://www.istqb.org/)

## CG-14.2. Test Pyramid

Follow the Google SWE Book ratio: **80% unit / 15% integration / 5% E2E**.

- **Unit tests** — fast, isolated, test one behavior. The foundation.
- **Integration tests** — verify components work together. Use real databases, real
  file systems, real HTTP where practical. Slower but higher confidence.
- **E2E tests** — full system from user perspective. Expensive, brittle, use sparingly.
  Reserve for critical user journeys.

If you're unsure what kind of test to write, write a unit test. If the unit test can't
cover the behavior (e.g., database queries, UI rendering), escalate to integration.

## CG-14.3. Properties of Good Tests

From Kent Beck's Test Desiderata — tests should be:

1. **Isolated** — no shared mutable state, no order dependency
2. **Composable** — can run any subset in any order
3. **Deterministic** — same result every time, no flakiness
4. **Fast** — milliseconds per unit test, seconds per integration test
5. **Writable** — easy to author, low ceremony
6. **Readable** — a failing test tells you what broke and why
7. **Behavioral** — test what the code does, not how it does it
8. **Structure-insensitive** — refactoring internals shouldn't break tests
9. **Automated** — no manual steps, no human judgment needed
10. **Specific** — a failure points to exactly one cause
11. **Predictive** — passing tests mean the code works in production
12. **Inspiring** — confidence to refactor and ship

## CG-14.4. Unit Test Patterns

**Structure — Arrange, Act, Assert (AAA):**

```
// Arrange — set up preconditions
// Act — call the method under test
// Assert — verify the result
```

**Rules:**
- One assertion concept per test (not one `assert` — one logical concept)
- No logic in tests — no `if`, `for`, `try/catch`, `switch`
- Test the public API, not internals — tests should survive refactoring
- Each test is independent — arrange its own state, don't rely on other tests

**Naming — use descriptive names that read as specifications:**
- `test_parse_order_with_valid_json_returns_order`
- `ParseOrder_WithMissingField_ThrowsValidationError`
- `"returns empty list when no results match"`

## CG-14.5. Property-Based Testing

When to use: parsers, serializers, data transformers, encoders/decoders, validators — anything
where "for all valid inputs X, property Y holds."

**The principle:** Instead of testing specific examples, describe properties of the output
and let the framework generate hundreds of random inputs to try to falsify them.

**Platform tools:**

| Platform | Library | Install |
|----------|---------|---------|
| Python | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | `pip install hypothesis` |
| TypeScript/JS | [fast-check](https://github.com/dubzzz/fast-check) | `npm install fast-check` |
| Swift | `@Test(arguments:)` (parameterized) | Built into swift-testing |
| .NET | [FsCheck](https://fscheck.github.io/FsCheck/) | `dotnet add package FsCheck` |
| Kotlin/JVM | [jqwik](https://jqwik.net/) | Gradle/Maven dependency |

**Write at least one property test per data transformation function.** Examples:

- `encode(decode(x)) == x` (round-trip)
- `sort(xs).length == xs.length` (preservation)
- `parse(serialize(obj)).fields == obj.fields` (fidelity)

```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.text())
def test_encode_decode_roundtrip(s):
    assert decode(encode(s)) == s
```

## CG-14.6. Mutation Testing

Mutation testing validates that your tests actually catch bugs — not just achieve coverage.

**How it works:** The tool mutates your source code (e.g., changes `<` to `<=`, `True` to
`False`, deletes a line) and re-runs your tests. If tests still pass, the mutant "survived"
— meaning your tests have a blind spot.

**The closed loop:**
1. Write tests
2. Run mutation testing
3. Examine surviving mutants
4. Write additional tests to kill surviving mutants
5. Repeat until mutation score is acceptable

**Run mutation testing before claiming "tests are complete."**

**Platform tools:**

| Platform | Tool | Install | Run |
|----------|------|---------|-----|
| Python | [mutmut](https://github.com/boxed/mutmut) | `pip install mutmut` | `mutmut run` |
| TypeScript/JS | [Stryker](https://stryker-mutator.io/) | `npm i -g stryker-cli` | `npx stryker run` |
| .NET | [Stryker.NET](https://stryker-mutator.io/) | `dotnet tool install -g dotnet-stryker` | `dotnet stryker` |
| Swift | [Muter](https://github.com/muter-mutation-testing/muter) | `brew install muter-mutation-testing/formulae/muter` | `muter` |
| Kotlin/JVM | [Pitest](https://pitest.org/) | Gradle/Maven plugin | `./gradlew pitest` |

## CG-14.7. Test Doubles

Use [Martin Fowler's taxonomy](https://martinfowler.com/bliki/TestDouble.html):

| Double | Purpose | Example |
|--------|---------|---------|
| **Dummy** | Fill a parameter, never used | `null` or empty object |
| **Stub** | Return canned answers | `stub.getUser() → User("test")` |
| **Spy** | Record calls for later verification | `spy.wasCalled("save")` |
| **Mock** | Verify expected interactions | `mock.verify(save, times: 1)` |
| **Fake** | Working implementation, simplified | In-memory database |

**Prefer fakes over mocks** when possible. Fakes exercise real behavior; mocks only verify
expectations. A fake in-memory database catches more bugs than a mock that returns canned SQL results.

**Never mock what you don't own.** Wrap external dependencies (HTTP clients, databases, SDKs)
behind your own interface. Mock your interface, not the third-party API directly. This
insulates tests from upstream API changes.

**Platform tools:**
- **Python:** `unittest.mock` (stdlib), [pytest-mock](https://github.com/pytest-dev/pytest-mock)
- **TypeScript/JS:** `jest.mock`, [vitest mocking](https://vitest.dev/guide/mocking.html)
- **Swift:** Protocol conformances (no framework needed), [swift-testing](https://github.com/apple/swift-testing)
- **.NET:** [NSubstitute](https://nsubstitute.github.io/)
- **Kotlin:** [MockK](https://mockk.io/), [Turbine](https://github.com/cashapp/turbine) for Flow testing

## CG-14.8. Security Testing

Run security scans as part of post-generation verification (CG-1.8). These are CLI tools
Claude Code can invoke directly.

**Static Analysis (SAST):**
- [Semgrep](https://semgrep.dev/) — all languages: `semgrep scan --config=auto .`
- [Bandit](https://github.com/PyCQA/bandit) — Python: `bandit -r src/`
- [CodeQL](https://codeql.github.com/) — deep analysis (Swift, Kotlin, C#, Python, TS, Go)

**Dependency Scanning:**
- Python: `pip-audit`
- Node.js: `npm audit`
- .NET: `dotnet list package --vulnerable`
- All: [Snyk](https://snyk.io/) CLI (`snyk test`)

**Dynamic Analysis (DAST):**
- [OWASP ZAP](https://www.zaproxy.org/) — scan running web services: `zap-cli quick-scan http://localhost:8888`

See CG-11 (Security Guidelines) for the full security reference.

## CG-14.9. Flaky Test Prevention

Flaky tests destroy confidence. Quarantine them immediately — fix or delete, never ignore.

**Rules:**
- No shared mutable state between tests (each test arranges its own)
- No dependency on test execution order
- No real network calls in unit tests (use fakes or stubs)
- No `sleep()` or timing-dependent assertions — use deterministic waits or callbacks
- No filesystem side effects in unit tests (use temp directories, clean up in teardown)
- No reliance on system clock — inject time as a dependency
- If a test fails intermittently, it is broken. Treat it as a P1 bug.

References:
- [Martin Fowler: Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
- [Google Testing Blog: Flaky Tests](https://testing.googleblog.com/)

## CG-14.10. Test Data

**Construct what you need, per test.** Avoid large shared fixture files.

- **Builder pattern** or **factory functions** for complex objects — each test calls
  `makeOrder(status: .pending)` with only the fields it cares about, defaults for the rest
- **Property-based generators** (Hypothesis strategies, fast-check arbitraries) for
  comprehensive input coverage
- **Inline literals** for simple cases — `assert parse("hello") == "hello"` is clear
- **No magic fixtures** — if a test needs specific data, the data should be visible in the test

## CG-14.11. The Testing Workflow

The recommended Claude Code testing workflow, combining all tools:

1. **Write implementation code**
2. **Write unit tests** — informed by property-based testing for data transformations
3. **Run tests** — `pytest` / `swift test` / `npm test` / `dotnet test`
4. **Validate test quality** — `mutmut run` / `npx stryker run` / `muter` / `dotnet stryker`
5. **Kill surviving mutants** — write additional tests targeting gaps
6. **Security scan** — `semgrep scan` + `bandit` / `pip-audit` / `npm audit`
7. **E2E verification** — Playwright for web UIs, platform test runners for native

This creates a closed loop: AI generates tests, deterministic tools validate those tests
actually catch bugs, AI writes more tests to close gaps.
