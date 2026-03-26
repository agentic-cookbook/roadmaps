# Spec Writing Conventions

Format and structure rules for behavioral specifications, derived from the litterbox and temporal-platform repos.

## CG-12.1. Frontmatter

Every spec starts with a YAML frontmatter block:

```yaml
---
version: 1.0.0
status: draft | review | accepted | deprecated
created: YYYY-MM-DD
last-updated: YYYY-MM-DD
author: Name or claude-code
copyright: 2026 Mike Fullerton / Temporal. All rights reserved.
platforms: [Apple, Android, Windows, Web]
tags: [category, feature-area]
dependencies:
  - path/to/other-spec.md@1.0.0
supersedes: null
---
```

Field definitions:

- **version**: Semver. Major for breaking changes, minor for new requirements, patch for clarifications.
- **status**: `draft` (work in progress), `review` (ready for feedback), `accepted` (stable), `deprecated` (superseded).
- **created**: Immutable date of first creation.
- **last-updated**: Date of most recent change.
- **platforms**: Which platforms this spec targets.
- **dependencies**: Other specs this one references, with version pins. Omit if none.

## CG-12.2. RFC 2119 Keywords

Use RFC 2119 keywords for all behavioral requirements:

- **MUST** / **MUST NOT**: Absolute requirements. Every MUST requires at least one test vector.
- **SHOULD** / **SHOULD NOT**: Recommendations.
- **MAY**: Optional behavior.

## CG-12.3. Requirement Numbering

Number requirements sequentially: `REQ-001`, `REQ-002`, etc. Never reuse numbers, even if a requirement is removed. This makes requirements unambiguous, testable, and referenceable from test vectors.

## CG-12.4. Template Variables

Specs use `{{placeholder}}` tokens for consumer-specific values:

| Variable | Example | Purpose |
|----------|---------|---------|
| `{{app_name}}` | `Temporal` | Application name (PascalCase) |
| `{{app_name_lower}}` | `temporal` | Application name (lowercase) |
| `{{org_package}}` | `company.temporal` | Package/bundle identifier root |
| `{{api_base_url}}` | `https://api.temporal.today` | Production API URL |
| `{{api_dev_url}}` | `http://localhost:8080` | Development API URL |
| `{{db_name}}` | `temporal.db` | Local database filename |
| `{{bundle_id}}` | `com.company.app` | Bundle/package identifier |

## CG-12.5. Standard Sections

Include these sections in order (omit those that do not apply):

1. **Overview** — purpose, scope, in/out of scope
2. **Terminology** — domain-specific terms table
3. **Behavioral Requirements** — REQ-NNN with RFC 2119 keywords
4. **Data Structures** — JSON Schema, field tables, example JSON
5. **Appearance** — visual spec with concrete values (UI specs)
6. **States** — state table with transitions and appearance/behavior changes
7. **API Contract** — endpoints, request/response, errors
8. **Accessibility** — roles, labels, keyboard nav, tap targets, contrast
9. **Conformance Test Vectors** — input/output pairs linked to REQ-NNN
10. **Edge Cases** — boundary conditions, error states
11. **Logging** — exact log messages per event (see below)
12. **Deep Linking** — URL patterns for navigable entities/views
13. **Privacy** — what data is collected, why, how stored, PII handling
14. **Feature Flags** — flag keys that gate this feature
15. **Analytics** — event names and property schemas
16. **Platform Notes** — Swift, Kotlin, TypeScript guidance
17. **Design Decisions** — LLM-made choices needing user approval
18. **Changelog** — version history

## CG-12.6. Test Vector Formats

Two formats, use whichever fits:

### Behavioral (table)

For state/action/outcome tests:

```markdown
| ID | Requirements | Input | Expected |
|----|-------------|-------|----------|
| component-001 | REQ-001 | Action description | Expected outcome |
| component-002 | REQ-002, REQ-003 | Action description | Expected outcome |
```

### Data (JSON blocks)

For serialization, algorithms, and wire formats:

```markdown
#### vector-name-001
**Input**:
```json
{ "field": "value" }
```
**Expected**:
```json
{ "result": "value" }
```
```

For complex components, test vectors may also be published as separate JSON files in a `vectors/` directory.

## CG-12.7. Logging Section

Every behavioral spec MUST include a Logging section with exact log messages. This enables verification by grepping output rather than visual inspection.

Format: `Subsystem: {{org_package}} | Category: ComponentName`

```markdown
## Logging

Subsystem: `{{bundle_id}}` | Category: `ComponentName`

| Event | Level | Message |
|-------|-------|---------|
| Tap | debug | `ComponentName: tapped, starting async action` |
| Action success | debug | `ComponentName: async action completed (success, {duration}ms)` |
| Action failure | debug | `ComponentName: async action failed ({error})` |
| State change | debug | `ComponentName: state changed to {state}` |
```

## CG-12.8. Privacy Section

Document what data is collected, why it is needed, how it is stored, and how PII is handled. This section is required for any spec that involves data collection.

## CG-12.9. Feature Flags Section

List the feature flag keys that gate this feature. Use the `FeatureFlagProvider` interface pattern described in the general guidelines.

## CG-12.10. Analytics Section

Define event names and property schemas for all significant user actions instrumented by this feature.
