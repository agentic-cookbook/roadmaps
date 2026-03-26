# TypeScript / React / Web Conventions

Platform-specific guidance for web development with TypeScript.

## CG-5.1. Linting and Formatting

1. [ESLint](https://eslint.org/) with `eslint.config.js`. Use `eslint-config-prettier` to avoid conflicts with the formatter.
2. [Prettier](https://prettier.io/) with `.prettierrc` for auto-formatting.
3. [Stylelint](https://stylelint.io/) with `.stylelintrc.json` for CSS linting.
4. Add as `package.json` scripts and pre-commit hooks.

## CG-5.2. Accessibility References

1. [WCAG 2.1](https://www.w3.org/TR/WCAG21/) — minimum AA conformance for all components.
2. [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) — correct ARIA roles, states, and properties.

## CG-5.3. Accessibility CSS Media Queries

Components MUST respond to these user preferences:

| Setting | Media Query | Action |
|---------|-------------|--------|
| Reduced Motion | `prefers-reduced-motion: reduce` | Disable/simplify CSS animations and JS transitions |
| High Contrast | `prefers-contrast: more` | Increase border widths, use higher-contrast colors |
| Forced Colors | `forced-colors: active` | Respect system color palette (Windows High Contrast) |
| Dark Mode | `prefers-color-scheme: dark` | Full dark theme support |
| Reduced Transparency | `prefers-reduced-transparency: reduce` | Use opaque backgrounds |
| Reduced Data | `prefers-reduced-data: reduce` | Lazy-load images, reduce asset sizes |

Screen reader support: use ARIA roles, `aria-live` for dynamic content, proper landmark regions.

## CG-5.4. Security

1. **Content Security Policy**: Configure CSP headers to restrict script sources and prevent XSS.
2. **HttpOnly cookies**: Use HttpOnly secure cookies for authentication tokens. Never store tokens in `localStorage`.
3. **Input sanitization**: Sanitize all user input before display to prevent XSS and injection.
4. **TLS only**: All network communication MUST use HTTPS.
5. Minimize third-party scripts. Respect the Do Not Track header.

## CG-5.5. Localization

Use an i18n library (`react-intl`, `i18next`, `FormatJS`). Extract all user-facing strings into message catalogs. No hardcoded strings.

## CG-5.6. RTL Layout Support

Use CSS logical properties throughout:

- `margin-inline-start` instead of `margin-left`
- `padding-inline-end` instead of `padding-right`
- `inset-inline-start` instead of `left`

Set `dir="rtl"` attribute on the root element for RTL locales.

## CG-5.7. Testing

Use [Playwright](https://playwright.dev/) for end-to-end and visual regression testing. Screenshot comparison for snapshot tests. Use Storybook for component catalog and visual tests where applicable.

## CG-5.8. Concurrency

Use `Promise`/`async`/`await` for async operations. Use Web Workers for CPU-intensive tasks. Never block the main thread.

## CG-5.9. Deep Linking

Every view MUST have a unique, shareable URL. Use framework routing (React Router, Next.js routing, etc.).

## CG-5.10. Debug Mode

Access via `/debug` route or keyboard shortcut (`Ctrl+Shift+D`), guarded by `process.env.NODE_ENV === 'development'`.

## CG-5.11. Feature Flags

TypeScript interface + `localStorage`-backed implementation as the default.

## CG-5.12. Analytics

TypeScript interface + `console`-backed implementation as the default.

## CG-5.13. Immutability

Use `const` by default. Use `var`/`let` only when mutation is required. Prefer `useState` (React) for contained mutable state.
