# Engineering Principles

Core principles that guide all technical decisions. Each principle optimizes for making future change cheaper and safer.

## CG-2.1. Simplicity

Simple and easy are not synonyms. Simple means no interleaving of concerns. Easy means familiar or convenient. Optimizing for easy leads to complexity that kills velocity. Optimizing for simple keeps systems understandable and changeable.

- Before adding abstraction, ask: "Am I braiding two concerns together?"
- Favor constructs that do one thing over constructs that feel convenient
- Complexity is never removed later — it compounds. Resist it at introduction time

## CG-2.2. Make It Work, Make It Right, Make It Fast

Separate correctness, design quality, and performance into sequential phases:

1. Get a working solution for the common case
2. Refactor for clarity, handle edge cases, clean up design
3. Optimize only what measurement proves is slow

Never skip phase 2 to jump to phase 3.

## CG-2.3. Composition over inheritance

Default to composing behaviors from small, focused pieces. Use inheritance only for genuine "is-a" relationships, and even then sparingly. Prefer protocols/interfaces over base classes. When extending behavior, wrap rather than subclass.

## CG-2.4. Dependency injection

A component should receive its dependencies from the outside, not construct them internally:

- Pass services via constructor/initializer parameters or protocol properties
- Never instantiate a concrete service inside the component that uses it
- Use protocol/interface types for dependencies, not concrete types
- Avoid service locator pattern (hidden global lookup)

## CG-2.5. Immutability by default

Mutable shared state is the root cause of most concurrency bugs. Default to immutable values; introduce mutability only where necessary:

- Use `let` (Swift), `val` (Kotlin), `const` (JS/TS) by default
- Prefer value types (structs, data classes) over reference types
- Contain mutation behind clear boundaries (actors, StateFlow, useState)

## CG-2.6. Fail fast

Invalid state should be detected and surfaced immediately at the point of origin, not propagated silently:

- Use assertions and preconditions in debug builds
- Validate inputs at system boundaries
- Return typed errors rather than swallowing exceptions
- Never use empty catch blocks
- In production, fail gracefully with clear messages; in debug, fail loudly

## CG-2.7. Idempotency

User actions and system operations should be safe to repeat without duplicate side effects:

- Debounce or disable buttons during async operations
- Use idempotency keys for API calls with side effects
- Database migrations must be safe to run multiple times
- Check current state before applying state transitions

## CG-2.8. Design for deletion

Every line of code is a maintenance liability. Build disposable software, not reusable software:

- Write code that is easy to throw away without affecting the rest of the system
- Treat lines of code as lines spent — deleting code reduces maintenance cost
- Do not abstract prematurely in pursuit of reuse
- When in doubt, duplicate rather than couple

## CG-2.9. YAGNI

Build for today's known requirements. Speculative generality adds code that must be maintained but delivers no current value. If a future need materializes, the cost of adding it then is almost always lower than maintaining premature abstractions now.

## CG-2.10. Explicit over implicit

Hidden behavior, magic, and implicit coupling create bugs that take days to find:

- Make dependencies visible (injection over hidden globals)
- Name things for what they do, not how they are implemented
- Prefer clear parameter passing over ambient state

## CG-2.11. Small, reversible decisions

If a decision is cheap to reverse, make it fast. If it is expensive to reverse, invest in understanding first:

- Prefer incremental delivery over phased releases
- Defer binding decisions until the last responsible moment
- Treat architecture as a continuous activity, not an up-front phase

## CG-2.12. Tight feedback loops

The speed of your feedback loop is the speed of your learning:

- Optimize test suite runtime — slow tests do not get run
- Deploy small changes frequently
- Get real user feedback as early as possible
- Automate everything between commit and production observation

## CG-2.13. Separation of concerns

A module should have one reason to change. If describing what a module does requires "and," consider splitting. This applies at every scale: functions, modules, services, teams.

## CG-2.14. Principle of least astonishment

APIs, UI, and system behavior should match what users and callers expect. If a name suggests one behavior, it must deliver that behavior. Side effects should be obvious from the API signature.

## CG-2.15. Manage complexity through boundaries

Well-defined boundaries between subsystems let each side evolve independently. Define ports (interfaces) that describe what the application needs. Use adapters to translate between external technologies and your ports. Test the core application without databases, UIs, or networks.

## CG-2.16. Meta-Principle: Optimize for Change

Every principle above is a strategy for making future change cheaper and safer. When evaluating any technical decision, the primary question is: "Does this make future change easier or harder?"
