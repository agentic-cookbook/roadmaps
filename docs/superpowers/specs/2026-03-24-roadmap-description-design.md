# Roadmap Description on Dashboard Cards

## Goal

Add a one-line description to each roadmap so someone unfamiliar with the project can understand what it does at a glance from the dashboard overview.

## Data Flow

1. `/plan-roadmap` writes `description:` in Roadmap.md YAML frontmatter during Step 5b
2. `/implement-roadmap` reads it via `parse_frontmatter()` and includes it in the dashboard sync payload
3. Dashboard stores it in a `description` column on the `roadmaps` table
4. Overview HTML renders it on each card under the repo name, above the progress bar

## Description Format

- One line, ~80 characters, plain text
- Written by the LLM during planning (not auto-extracted from Goal section)
- Example: `description: Real-time menu bar app showing active Claude Code sessions, progress, and errors`

## Changes

### Database: `services/dashboard/db.py`
- Add `description TEXT` column to `roadmaps` table
- Schema migration: `ALTER TABLE roadmaps ADD COLUMN description TEXT`

### Models: `services/dashboard/models.py`
- Include `description` in create_roadmap, update_roadmap, sync_roadmap, and get_roadmap
- Read from sync payload: `data.get("description")`

### API: No route changes
- `description` is already covered by the generic field handling in create/update/sync
- GET response includes it automatically once it's in the model

### Overview UI: `services/dashboard/static/overview.html`
- Render `r.description` between the repo name and progress bar
- Style: `color: #c8c8d0; font-size: 13px; font-style: italic`
- Truncate with CSS `text-overflow: ellipsis` at ~120 chars
- Skip rendering if description is null/empty
- Bump overview version

### Plan-roadmap skill: `skills/plan-roadmap/SKILL.md`
- In Step 5b (Draft both documents), instruct: "Write a `description` field in the Roadmap frontmatter — a single sentence (~80 chars) summarizing what this feature does, written for someone unfamiliar with the project."

### Roadmap template: `skills/plan-roadmap/references/feature-roadmap-template.md`
- Add `description:` to the YAML frontmatter section

## Card Layout (Option B)

```
#2 StatusDashboard                                    [Running]
temporal-company/temporal
Real-time menu bar app showing active Claude Code sessions, progress, and errors
████████████░░░░░░░░░░░░░░░░░░
3/9 steps (33%)
```

## What Does NOT Change

- `scripts/roadmap_lib.py` — frontmatter parsing is already generic, handles any field
- API routes — no new endpoints needed
- Dashboard detail page — description only appears on overview cards
