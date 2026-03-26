# Design: UI Design Guidelines

## Summary

Add a new `guidelines/ui.md` file covering cross-platform UI design principles. Provides sensible defaults when no project design system exists, while deferring to platform HIGs as the primary authority. Updates `CLAUDE.md`, `best-practices-references.md`, and `README.md` for consistency.

## Scope

- **In scope:** Visual hierarchy, spacing, typography, color, layout, state design, form design, feedback patterns, touch/click targets, animation/motion, data display. Cross-references to platform HIGs and existing guidelines.
- **Out of scope:** Platform-specific accessibility APIs (platform files), localization/RTL implementation (general.md), theming implementation (platform files), specific component libraries (platform files).

## Decisions

- Themed sections (like platform files), not numbered rules
- Platform HIG always takes precedence over defaults in this file
- Concrete default values provided (4px/8px grid, 44px targets, etc.) for when no design system exists
- Minimal overlap with general.md — cross-references for accessibility rules, no duplication
- Per-section references to authoritative sources (Apple HIG, Material Design, Fluent, WCAG, NNGroup)

---

## File 1: `guidelines/ui.md`

### Header & Platform Hierarchy

```
# UI Design Guidelines

Cross-platform UI principles for building consistent, usable interfaces. These guidelines
provide defaults when no project design system exists — always defer to the platform's
native design language first.

## Platform Design Languages

Defer to these canonical sources before applying the defaults in this file:

- **Apple**: [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- **Android**: [Material Design 3](https://m3.material.io/)
- **Windows**: [Fluent 2 Design System](https://fluent2.microsoft.design/)
- **Web**: [WCAG 2.1](https://www.w3.org/TR/WCAG21/) + platform-appropriate system

When the platform HIG prescribes a specific value (spacing, type size, target size),
use the platform value. Use the defaults below to fill gaps or establish a cross-platform
baseline.
```

### Section: Visual Hierarchy

```
## Visual Hierarchy

Establish clear importance through size, weight, color, and spacing. Every screen should
have one obvious focal point — the primary action or content the user came for.

- **One primary action per screen** — if everything is bold, nothing is bold
- Use size and weight (not just color) to distinguish heading levels
- Group related content with proximity; separate unrelated content with whitespace
- Interactive elements must be visually distinguishable from static content
- Disabled elements should be visually muted but still discoverable

See general.md rule 12 for accessibility requirements (contrast, labels, focus order).

References:
- [NNGroup: Visual Hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/)
- [Apple HIG: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design: Applying Layout](https://m3.material.io/foundations/layout/applying-layout/overview)
- [Fluent Design: Layout](https://learn.microsoft.com/en-us/windows/apps/design/layout/)
```

### Section: Spacing

```
## Spacing

Use a consistent spatial scale based on a **4px base unit** (8px primary grid). All spacing,
padding, and margin values should be multiples of 4. This aligns with Apple HIG, Material
Design, and Fluent Design.

Default spacing scale: **4, 8, 12, 16, 24, 32, 48, 64**

- **4px** — tight spacing within compact elements (icon-to-label, badge padding)
- **8px** — default inner padding, spacing between related items
- **12px** — padding within cards or list items
- **16px** — standard content padding from screen/container edges
- **24px** — separation between content groups
- **32-64px** — major section separation

Avoid arbitrary values (5px, 13px, 37px). If a value isn't on the scale, reconsider.

References:
- [Apple HIG: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design: Layout](https://m3.material.io/foundations/layout/overview)
- [Fluent Design: Layout](https://learn.microsoft.com/en-us/windows/apps/design/layout/)
```

### Section: Typography

```
## Typography

Use the platform's system font. Establish a type scale with clear roles — don't invent
sizes ad-hoc.

Platform system fonts:
- **Apple**: SF Pro (iOS/macOS), New York (serif alternative)
- **Android**: Roboto, or system default via Material type system
- **Windows**: Segoe UI Variable
- **Web**: System font stack (`system-ui, -apple-system, sans-serif`)

Defaults when no design system exists:
- **Body text**: 14-17pt (16px is the safest cross-platform default)
- **Minimum readable size**: 11-12pt for captions/labels, never smaller
- **Line height**: 1.4x-1.5x font size for body text
- **Heading scale**: Use the platform's built-in type scale (Dynamic Type, Material type
  tokens, Fluent type ramp) rather than inventing sizes

General principles:
- Limit to 2-3 font weights per screen (regular, medium/semibold, bold)
- Avoid all-caps for more than a few words — harms readability and screen reader experience
- Paragraph width: 45-75 characters for comfortable reading
- See general.md rule 12 for Dynamic Type / font scaling requirements

References:
- [Apple HIG: Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [Material Design: Type Scale](https://m3.material.io/styles/typography/type-scale-tokens)
- [Fluent Design: Typography](https://learn.microsoft.com/en-us/windows/apps/design/style/typography)
- [WCAG 1.4.12: Text Spacing](https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html)
```

### Section: Color

```
## Color

Use color with intention — never as the sole means of conveying information.

- **Semantic color tokens** — use platform-provided semantic colors (e.g., `TextFillColorPrimary`,
  `label`, `onSurface`) rather than hard-coded hex values. They adapt to theme and accessibility
  settings automatically.
- **Limit the palette** — 1 primary/accent color, 1-2 neutral tones, plus semantic colors for
  success/warning/error. Avoid rainbow UIs.
- **Not color alone** — always pair color with a secondary indicator (icon, shape, text, pattern)
  for state changes, errors, and status.
- **Contrast minimums** (WCAG AA, per general.md rule 12 item 5):

| Element | AA Minimum | AAA Enhanced |
|---------|-----------|-------------|
| Normal text (<18pt / <14pt bold) | 4.5:1 | 7:1 |
| Large text (18pt+ or 14pt+ bold) | 3:1 | 4.5:1 |
| Non-text UI components | 3:1 | — |

- **Dark mode** — every color must work in both light and dark themes. Test both.

References:
- [WCAG 1.4.3: Contrast Minimum](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WCAG 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)
- [Apple HIG: Color](https://developer.apple.com/design/human-interface-guidelines/color)
- [Material Design: Color System](https://m3.material.io/styles/color/system/how-the-system-works)
- [Fluent Design: Color](https://learn.microsoft.com/en-us/windows/apps/design/style/color)
```

### Section: Layout

```
## Layout

Design for the content, not a fixed screen size. Layouts should adapt gracefully from
compact to expanded contexts.

- **Single-column by default** — multi-column only when content density justifies it and
  screen width supports it
- **Content-first** — decide what information the user needs, then choose a layout. Don't
  start with a grid and fill it.
- **Consistent alignment** — pick a leading edge and stick to it. Mixed alignment creates
  visual noise.
- **Responsive breakpoints** — use the platform's adaptive layout system (Size Classes,
  Window Size Classes, CSS media queries, VisualStateManager) rather than hard-coded widths
- **Content density** — prefer generous whitespace for consumer UIs, allow denser layouts
  for productivity/data-heavy tools. Never sacrifice readability for density.
- **Scroll direction** — one primary scroll direction per view. Avoid nested same-direction
  scrolling.

References:
- [Apple HIG: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design: Adaptive Layout](https://m3.material.io/foundations/layout/applying-layout/overview)
- [Fluent Design: Responsive Design](https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design)
- [NNGroup: Mobile-First Is Not Mobile-Only](https://www.nngroup.com/articles/mobile-first-not-mobile-only/)
```

### Section: State Design

```
## State Design

Every view that loads data or can be empty must handle all four states explicitly. Never
show a blank screen with no explanation.

**The four states:**

1. **Loading** — show progress (see general.md rule 5). Use skeleton screens for content-heavy
   views, spinners for actions. Never block the entire screen for a partial load.
2. **Empty** — explain what belongs here, why it's empty, and provide a single clear action to
   populate it. Use an icon or illustration, a brief message, and a CTA button.
3. **Error** — identify the problem, explain why if possible, and offer a recovery action (retry,
   go back, contact support). Never show raw error codes or stack traces. Don't blame the user.
4. **Loaded** — the normal content state.

Design empty and error states with the same care as the loaded state — they are often the
user's first impression.

References:
- [Apple HIG: Empty States](https://developer.apple.com/design/human-interface-guidelines/empty-states)
- [NNGroup: Empty State Design](https://www.nngroup.com/articles/empty-state-interface-design/)
- [NNGroup: Error Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- [Material Design: Empty States (M2 reference)](https://material.io/design/communication/empty-states.html)
```

### Section: Form Design

```
## Form Design

Forms are where users do real work. Reduce friction at every step.

**Layout:**
- Single-column layout — outperforms multi-column for completion rate
- Top-aligned or floating labels — fastest to scan and complete
- Group related fields visually with spacing or section headers
- Place primary action (Submit/Save) at the bottom, aligned with the form fields

**Validation:**
- Validate on **blur** (when user leaves the field), not on every keystroke
- Validate the **full form on submit** as a final safety net
- Never validate while the user is still actively typing in a field
- Success indicators (checkmarks) only for fields where the user genuinely wonders if
  input was accepted (e.g., username availability)

**Error messages:**
- Show errors **inline, directly below the field** — not only at the top of the form
- Use color + icon + text (never color alone)
- Be specific and actionable: "Password must be at least 8 characters" not "Invalid input"
- Don't blame the user

**Other principles:**
- Use placeholder text for format hints, not as label replacement — placeholders disappear on focus
- Pre-fill and default where possible to reduce effort
- Mark optional fields, not required ones (most fields should be required; if they're not,
  reconsider asking)

References:
- [NNGroup: Form Design Guidelines](https://www.nngroup.com/articles/web-form-design/)
- [NNGroup: Error Messages in Forms](https://www.nngroup.com/articles/errors-forms-design-guidelines/)
- [Apple HIG: Text Fields](https://developer.apple.com/design/human-interface-guidelines/text-fields)
- [Material Design: Text Fields](https://m3.material.io/components/text-fields/guidelines)
```

### Section: Feedback Patterns

```
## Feedback Patterns

Every user action should have visible feedback. The weight of the feedback should match
the weight of the action.

- **Inline feedback** — field-level validation, character counts, progress within a component.
  Lowest weight, least disruptive.
- **Toast / Snackbar** — non-critical confirmations ("Saved", "Copied to clipboard"). Auto-dismiss
  after 3-5 seconds. No user action required. Don't use for errors.
- **Banner / Inline alert** — persistent messages that need attention but don't block work
  (connectivity warning, degraded mode). Dismissible.
- **Dialog / Alert** — destructive or irreversible actions requiring explicit confirmation
  ("Delete 12 items? This cannot be undone."). Use sparingly — dialog fatigue leads to
  click-through without reading.
- **Never use dialogs for success messages** — a toast or inline confirmation is sufficient.
- **Destructive actions** must require explicit confirmation with a clearly labeled action
  ("Delete", not "OK"). Default focus should be on the safe option (Cancel).

References:
- [Apple HIG: Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts)
- [Material Design: Snackbar](https://m3.material.io/components/snackbar/overview)
- [NNGroup: Confirmation Dialogs](https://www.nngroup.com/articles/confirmation-dialog/)
- [NNGroup: Ten Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) (Heuristic #1: Visibility of system status)
```

### Section: Touch & Click Targets

```
## Touch & Click Targets

Interactive elements must be large enough to tap or click accurately. Defer to the platform
HIG first — each prescribes its own minimum:

| Platform | Minimum Target | Recommended |
|----------|---------------|-------------|
| Apple (iOS) | 44x44 pt | 44x44 pt |
| Android (Material) | 48x48 dp | 48x48 dp |
| Windows (Fluent) | 32x32 epx | 40x40 epx |
| Web (WCAG AA) | 24x24 CSS px | 44x44 CSS px |

**Cross-platform default: 44x44** when no platform HIG applies.

- The visual element (icon, text) can be smaller than the touch target — pad the hit area
- Minimum **8px spacing** between adjacent targets to prevent mis-taps
- Inline text links in paragraphs are exempt from size minimums but should have sufficient
  line height for comfortable tapping

See general.md rule 12 for full accessibility requirements.

References:
- [Apple HIG: Accessibility — User Interaction](https://developer.apple.com/design/human-interface-guidelines/accessibility#User-interaction)
- [Material Design: Accessibility Basics](https://m3.material.io/foundations/accessible-design/accessibility-basics)
- [Fluent Design: Targeting Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/input/guidelines-for-targeting)
- [WCAG 2.5.8: Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
```

### Section: Animation & Motion

```
## Animation & Motion

Motion should be purposeful — guide attention, show spatial relationships, and provide
feedback. Never animate for decoration.

**Duration defaults** (when no platform value exists):

| Interaction | Duration |
|------------|----------|
| Micro-feedback (ripple, highlight) | 50-100ms |
| State change (hover, toggle, press) | 100-200ms |
| Component enter/exit | 200-350ms |
| Page/navigation transition | 300-500ms |
| Complex choreography (rare) | 500-1000ms |

- Under 100ms feels instant. Over 500ms feels sluggish.
- Prefer platform-native spring/easing curves over linear or custom beziers
- **Always respect reduced-motion preferences** — see general.md rule 15 and each platform
  file's accessibility settings table. When reduced motion is enabled, replace animations
  with instant state changes or simple cross-fades.
- Avoid motion that covers large distances, loops continuously, or flashes

References:
- [Apple HIG: Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- [Material Design: Motion](https://m3.material.io/styles/motion/overview)
- [Fluent Design: Timing and Easing](https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing)
```

### Section: Iconography

```
## Iconography

Icons supplement text — they do not replace it (except for universally understood symbols
like play, pause, close, and search).

- Use the platform's native icon set first (SF Symbols, Material Symbols, Segoe Fluent Icons)
- All icons accompanying actions must have a text label or accessible name
- Maintain consistent size and weight across the UI — don't mix outlined and filled styles
  without intention (e.g., filled = selected, outlined = unselected)
- Minimum icon size: 16x16pt for decorative, 24x24pt for interactive (see Touch & Click Targets
  for the full hit area)
- Icons conveying state (error, success, warning) must be paired with color AND shape —
  see Color section

References:
- [Apple HIG: SF Symbols](https://developer.apple.com/design/human-interface-guidelines/sf-symbols)
- [Material Design: Icons](https://m3.material.io/styles/icons/overview)
- [Fluent Design: Icons](https://learn.microsoft.com/en-us/windows/apps/design/style/icons)
```

### Section: Data Display

```
## Data Display

Choose the right pattern for the content type and user task.

- **List** — sequential, scannable content. Best for homogeneous items where the user reads
  top-to-bottom (messages, settings, search results). Support pull-to-refresh and pagination
  for dynamic data.
- **Table** — comparable, multi-attribute data. Best for desktop/tablet when users need to
  compare values across rows (spreadsheets, admin panels, logs). Tables must be sortable
  by column. On mobile, consider collapsing to cards or a detail-on-tap list.
- **Cards** — heterogeneous, browsable content. Best when items have varying content types
  or sizes (news feed, dashboard widgets). Cards should each be a single tappable unit with
  one primary action.
- **Grid** — uniform visual items. Best for content where the visual is primary (photos,
  products, icons). Maintain consistent aspect ratios.

For collections of **10+ items**, provide sort and/or filter controls. For **50+ items**,
add search.

References:
- [Apple HIG: Lists and Tables](https://developer.apple.com/design/human-interface-guidelines/lists-and-tables)
- [Material Design: Lists](https://m3.material.io/components/lists/overview)
- [NNGroup: Cards](https://www.nngroup.com/articles/cards-component/)
```

---

## File 2: Updates to existing files

### `~/.claude/CLAUDE.md`

Add to the guidelines listing between `windows.md` and `specs.md`:
```
- `~/.claude/guidelines/ui.md` — Cross-platform UI design principles
```

### `guidelines/best-practices-references.md`

Add new section between "Windows / .NET" and "Cross-Platform":
```markdown
## UI Design

- [NNGroup: Visual Hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/)
- [NNGroup: Form Design Guidelines](https://www.nngroup.com/articles/web-form-design/)
- [NNGroup: Error Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- [NNGroup: Empty State Design](https://www.nngroup.com/articles/empty-state-interface-design/)
- [NNGroup: Ten Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
```

### `README.md`

Add `ui.md` row to the Coding Guidelines table between `windows.md` and `specs.md`:
```
| `ui.md` | Cross-platform UI design principles |
```

---

## Implementation Order

1. Create `guidelines/ui.md`
2. Update `guidelines/best-practices-references.md` — add UI Design section
3. Update `~/.claude/CLAUDE.md` — add guideline entry (commit + push dotfiles)
4. Update `README.md` — add row to guidelines table
5. Run `install.sh`, verify symlink
