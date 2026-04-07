# Cat Herding — Project Rules

## Plugin Dependencies

This project's skills and agents depend on the following Claude Code plugins. Install them before using the roadmap system.

### Required (core functionality)

| Plugin | Marketplace | Used By |
|--------|-------------|---------|
| `superpowers` | claude-plugins-official | Brainstorming, plan writing, TDD, debugging, worktrees, verification |
| `pr-review-toolkit` | claude-plugins-official | Code review, silent failure hunting, test analysis, type design analysis |
| `code-review` | claude-plugins-official | Guideline compliance checking |
| `code-simplifier` | claude-plugins-official | Post-implementation simplification pass |
| `feature-dev` | claude-plugins-official | Code exploration, architecture analysis, code review |
| `security-guidance` | claude-plugins-official | Security vulnerability detection |

### Recommended (enhanced workflows)

| Plugin | Marketplace | Used By |
|--------|-------------|---------|
| `frontend-design` | claude-plugins-official | Dashboard UI, documentation site |
| `claude-md-management` | claude-plugins-official | CLAUDE.md file management |
| `ralph-loop` | claude-plugins-official | Autonomous iteration loops |
| `claude-code-setup` | claude-plugins-official | Project setup assistance |
| `hookify` | claude-plugins-official | Custom hooks from natural language |
| `skill-creator` | claude-plugins-official | Skill benchmarking and eval |
| `document-skills` | anthropic-agent-skills | PDF, DOCX, PPTX, XLSX creation |

### Language Support

| Plugin | Marketplace |
|--------|-------------|
| `swift-lsp` | claude-plugins-official |
| `kotlin-lsp` | claude-plugins-official |
| `typescript-lsp` | claude-plugins-official |
| `pyright-lsp` | claude-plugins-official |
| `csharp-lsp` | claude-plugins-official |

### Install Commands

```bash
# Required
claude plugin install superpowers@claude-plugins-official
claude plugin install pr-review-toolkit@claude-plugins-official
claude plugin install code-review@claude-plugins-official
claude plugin install code-simplifier@claude-plugins-official
claude plugin install feature-dev@claude-plugins-official
claude plugin install security-guidance@claude-plugins-official

# Recommended
claude plugin install frontend-design@claude-plugins-official
claude plugin install claude-md-management@claude-plugins-official
claude plugin install hookify@claude-plugins-official
claude plugin install skill-creator@claude-plugins-official
claude plugin install document-skills@anthropic-agent-skills
```

## Coding Guidelines

See `.claude/rules/` for enforcement rules.

## Review Configuration

Default review agents for `/implement-roadmap`. Per-roadmap override via the `reviews` field in Roadmap.md frontmatter.

```yaml
reviews:
  per-step: [code-reviewer]
  final: [code-reviewer, silent-failure-hunter, pr-test-analyzer]
```

Available agents: `code-reviewer`, `silent-failure-hunter`, `pr-test-analyzer`, `type-design-analyzer`, `comment-analyzer`, `code-simplifier`.

## Project Conventions

- Versions are single integers, bumped as the first action when making changes
- Every code change must have tests
- Every bug fix must have a regression test
- Dashboard HTML pages must have version numbers, incremented on every commit
- Never modify dashboard HTML while a real roadmap is running
- Never directly modify roadmap state — build tools for it
- Commit and push immediately after making changes

## Agentic Cookbook

This project uses the [agentic-cookbook](https://github.com/agentic-cookbook/cookbook).

- **Cookbook path**: `../agentic-cookbook/`
- **Rule**: `cookbook.md` (minimal, ~10 lines — guardrails only)
- **Pipeline**: `/cookbook-start` to begin, `/cookbook-next` to advance one step
- **Preferences**: Recipe prompts enabled, contribution prompts enabled, committing included
- **Available skills**: /configure-cookbook, /install-cookbook, /cookbook-start, /cookbook-next, /lint-project-with-cookbook, /plan-cookbook-recipe, /contribute-to-cookbook

Run `/configure-cookbook` to manage preferences.
