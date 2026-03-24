# Roadmap Description on Dashboard Cards

## Goal

Add a one-line description to each roadmap so someone unfamiliar with the project can understand what it does at a glance from the dashboard overview.

## Data Flow

1. `/plan-roadmap` writes `description:` in Roadmap.md YAML frontmatter during Step 5b
2. The `dash load-roadmap` command reads it from frontmatter and includes it in the sync payload
3. Dashboard stores it in a `description` column on the `roadmaps` table
4. Overview HTML renders it on each card under the repo name, above the progress bar

## Description Format

- One line, ~80 characters, plain text
- Written by the LLM during planning (not auto-extracted from Goal section)
- Example: `description: Real-time menu bar app showing active Claude Code sessions, progress, and errors`

## Changes

### Database: `services/dashboard/db.py`
- Add `description TEXT` column to `roadmaps` CREATE TABLE in `SCHEMA_SQL`
- Bump `SCHEMA_VERSION` to 3
- Add migration entry `3: ["ALTER TABLE roadmaps ADD COLUMN description TEXT"]` to `MIGRATIONS` dict

### Models: `services/dashboard/models.py`
- `create_roadmap`: add `description` to the INSERT column list and extract from `data.get("description")`
- `update_roadmap`: add `"description"` to the `allowed` list
- `sync_roadmap`: add `"description": data.get("description")` to the `roadmap_data` dict
- `get_roadmap` / `get_all_roadmaps`: no changes needed — SELECT * already returns all columns

### Dashboard client: `scripts/dashboard_client.py`
- `create_roadmap`: add `description=None` parameter, include in data dict
- `sync`: no changes needed — already passes through arbitrary dict

### Dash CLI: `skills/progress-dashboard/references/dash`
- `svc_load_roadmap`: read `description` from Roadmap.md frontmatter via `parse_frontmatter()` and include it in the sync payload

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

### Tests
- `tests/unit/test_models.py`: test create/update/sync with description field
- `tests/unit/test_api_roadmaps.py`: test description in CRUD responses
- `tests/unit/test_api_sync.py`: test description passes through sync
- `tests/unit/test_db.py`: test migration to schema version 3

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
