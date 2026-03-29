# Roadmap Skill UX Refinements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make roadmap skills auto-invocable, instant-feeling, and deterministic in their UX output.

**Architecture:** Frontmatter changes enable auto-invoke on 5 skills. A new rule file and PostToolUse hook proactively offer roadmap conversion after planning sessions. plan-roadmap gets a conversion mode entry path, batched validation, and VERBATIM text blocks for deterministic output.

**Tech Stack:** Markdown (SKILL.md files), Bash (install/uninstall scripts), Python (test updates), JSON (settings.json hook)

**Spec:** `docs/superpowers/specs/2026-03-29-roadmap-skill-ux-refinements-design.md`

---

### Task 1: Update test expectations for auto-invoke change

**Files:**
- Modify: `tests/unit/test_skill_metadata.py:79-82`

- [ ] **Step 1: Update the disable-model-invocation test**

The current test asserts ALL skills have `disable-model-invocation: true`. Change it to only require it for skills that should keep it disabled.

```python
# Replace the test at line 79-82
SKILLS_REQUIRING_DISABLE_MODEL_INVOCATION = {
    "implement-roadmap",
    "implement-roadmap-interactively",
    "generate-test-roadmap",
    "import-shared-project",
    "progress-dashboard",
}

@pytest.mark.parametrize("skill_name", _skill_ids())
def test_disable_model_invocation_policy(self, skill_name):
    meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
    if skill_name in SKILLS_REQUIRING_DISABLE_MODEL_INVOCATION:
        assert meta.get("disable-model-invocation") is True, \
            f"Skill '{skill_name}' must have disable-model-invocation: true"
    else:
        assert "disable-model-invocation" not in meta or \
            meta.get("disable-model-invocation") is not True, \
            f"Skill '{skill_name}' should NOT have disable-model-invocation: true"
```

- [ ] **Step 2: Run the test to verify it fails (current skills still have the old fields)**

Run: `cd /Users/mfullerton/projects/cat-herding && python3 -m pytest tests/unit/test_skill_metadata.py::TestFrontmatterFields::test_disable_model_invocation_policy -v`

Expected: FAIL for plan-roadmap, plan-bugfix-roadmap, list-roadmaps, describe-roadmap, repair-roadmap (they still have `disable-model-invocation: true`)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_skill_metadata.py
git commit -m "test: update disable-model-invocation test for auto-invoke policy"
```

---

### Task 2: Create ROADMAP-PLANNING-RULE.md

**Files:**
- Create: `.claude/rules/ROADMAP-PLANNING-RULE.md`

- [ ] **Step 1: Create the rule file**

```markdown
# Roadmap Planning Rule

## When to invoke /plan-roadmap automatically

If the user says any of the following (or similar), invoke the plan-roadmap
skill immediately:

- "make this into a roadmap"
- "convert this plan to a roadmap"
- "save this as a roadmap"
- "create a roadmap from this"
- "turn this into a roadmap"
- "roadmap this"

Do not ask for confirmation — the user's intent is clear. Invoke the skill.

## When NOT to invoke

- Do not offer a roadmap unprompted during normal conversation.
  The PostToolUse hook on ExitPlanMode handles that.
- Do not invoke if plan-roadmap is already active.
- Do not invoke for /implement-roadmap — that requires explicit invocation.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/rules/ROADMAP-PLANNING-RULE.md
git commit -m "feat: add ROADMAP-PLANNING-RULE for auto-invoke trigger phrases"
```

---

### Task 3: Update plan-roadmap frontmatter and version

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md:1-6` (frontmatter)
- Modify: `skills/plan-roadmap/SKILL.md:11` (version check output)
- Modify: `skills/plan-roadmap/SKILL.md:93` (planning log version reference)
- Modify: `skills/plan-roadmap/SKILL.md:247` (plan-version in Step 5b)

- [ ] **Step 1: Update frontmatter — remove disable-model-invocation, update description, bump version to 14**

Replace the entire frontmatter block:
```yaml
---
name: plan-roadmap
version: "14"
description: "Plan a feature as a structured Roadmap with steps and PRs. Use when planning a feature, converting a plan to a roadmap, organizing work into steps, or saving a plan as a roadmap."
---
```

Note: Description is 178 chars (under the 200 char test limit).

- [ ] **Step 2: Update version check output**

Change `plan-roadmap v13` to `plan-roadmap v14` in the Version Check section.

- [ ] **Step 3: Update version references in body**

Change `plan-roadmap v12` in the planning log header (Step 0d, line ~93) to `plan-roadmap v14`.
Change `plan-version` field reference in Step 5b from `12` to `14`.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/unit/test_skill_metadata.py -k "plan_roadmap" -v`

Expected: test_disable_model_invocation_policy PASS (no longer has the field), version consistency PASS, description under 200 PASS

- [ ] **Step 5: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "feat(plan-roadmap): enable auto-invoke, update description, bump to v14"
```

---

### Task 4: Add Output Rules and VERBATIM convention to plan-roadmap

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md` (insert after the Version Check section, before the ABSOLUTE RULE section)

- [ ] **Step 1: Insert the Output Rules section**

Insert between the `---` that closes the Version Check section (line 15) and the `# Plan Roadmap` heading (line 18). The Output Rules section goes before the skill's main heading:

```markdown
## Output Rules

Text inside `VERBATIM:` blocks MUST be printed exactly as written — character for character. No paraphrasing, no rewording, no additions, no omissions. Do not add greetings, commentary, or transitions around verbatim output.

---
```

- [ ] **Step 2: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "feat(plan-roadmap): add Output Rules section for VERBATIM convention"
```

---

### Task 5: Batch Step 0 validation in plan-roadmap

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md` (Steps 0a-0c, ~lines 52-79)

- [ ] **Step 1: Replace Steps 0a, 0b, 0c with a single batched validation step**

Replace the three separate steps (0a: Verify git, 0b: Create dir, 0c: Verify writable) with one combined step:

```markdown
## Step 0: Startup Validation

Run all environment checks in a single command. If any check fails, STOP and tell the user the specific error.

```bash
git rev-parse --is-inside-work-tree && \
PROJECT=$(basename $(git rev-parse --show-toplevel)) && \
mkdir -p "$HOME/.roadmaps/$PROJECT" && \
touch "$HOME/.roadmaps/$PROJECT/.verify" && \
rm "$HOME/.roadmaps/$PROJECT/.verify" && \
echo "OK:$PROJECT"
```

If the output starts with `OK:`, validation passed. Extract the project name from the output. If the command fails, report the specific error (not in a git repo, directory not writable, etc.).
```

Update Step 0d (Planning log) — keep the log format and entry type definitions, but replace the first paragraph (lines 83-85) with:

```markdown
This skill writes a planning log that records every decision, action, command, and user interaction. The log file is created in Step 5f when the roadmap directory is created. Until then, no log entries are accumulated — logging begins once the file path is known.
```

Remove the "accumulate log entries in memory" instruction. Keep all the `[timestamp]` format definitions that follow.

- [ ] **Step 2: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "feat(plan-roadmap): batch startup validation into single command"
```

---

### Task 6: Add Context Detection step (conversion mode) to plan-roadmap

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md` (insert new Step 0e after Step 0d, before Step 1)

- [ ] **Step 1: Insert Context Detection step**

After Step 0d and before `## Step 1: Open the Discussion`, insert:

```markdown
### 0e: Context Detection (Conversion Mode)

Before asking the user what they want to plan, check if the conversation already contains a plan or feature discussion.

**A plan is detected if ANY of these are true:**
- The conversation contains output from plan mode (ExitPlanMode was called earlier in this session)
- The conversation contains a numbered or bulleted list of implementation steps (3+ steps)
- The conversation contains a brainstorming spec or design document
- The user explicitly said "convert this" / "make this into a roadmap" (referencing existing context)

**If a plan is detected → Conversion Mode:**
1. Skip Phase 1 (Discussion) entirely — do not ask "What feature would you like to plan?"
2. Synthesize a discussion summary from what is already in the conversation context
3. Propose a PascalCase feature name derived from the context
4. Go directly to the Phase Gate prompt (Step 3)

**If no plan is detected:** Proceed to Step 1 as normal.
```

- [ ] **Step 2: Update Step 1 to note the conversion mode skip**

Add at the top of Step 1:

```markdown
> **Conversion mode**: If Context Detection (Step 0e) found an existing plan, this step is skipped. Proceed to Step 3.
```

- [ ] **Step 3: Update Step 3b to handle conversion mode source**

In Step 3b (Write Discussion Summary), add a note:

```markdown
> **Conversion mode**: In conversion mode, the discussion summary is synthesized from the pre-existing conversation context rather than from a Phase 1 discussion. Apply the same rules — capture the user's intent faithfully, include direct quotes where possible.
```

- [ ] **Step 4: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "feat(plan-roadmap): add Context Detection step for conversion mode"
```

---

### Task 7: Convert fixed prompts to VERBATIM blocks in plan-roadmap

**Files:**
- Modify: `skills/plan-roadmap/SKILL.md` (Steps 0, 1, 3, 5c, 5d, 6c)

- [ ] **Step 1: Add VERBATIM to the version announcement**

The skill already prints `plan-roadmap v14` — wrap it:

After the version check section, add to the startup flow:

```markdown
VERBATIM:
```
plan-roadmap v14
```
```

- [ ] **Step 2: Add VERBATIM to Step 1 opening question**

Replace the current Step 1 prompt:
```
Ask the user:

```
What feature would you like to plan?
```
```

With:
```
VERBATIM:
```
What feature would you like to plan?
```
```

- [ ] **Step 3: Add VERBATIM to Step 3 Phase Gate prompt**

The Phase Gate prompt (lines 144-160) is already in a code block. Add `VERBATIM:` label before it:

```
VERBATIM:
```
Here's what I heard:

<summary>

Proposed feature name: <FeatureName>

If this looks right, I'll move to Planning and create:
  - Roadmap.md (feature definition + implementation steps with issue placeholders)

No implementation code will be written. No GitHub issues will be created.
Issues are created later by /implement-roadmap.

[x] yes — move to Planning
[ ] revise name
[ ] keep discussing
```
```

Note: The `<summary>` placeholder is generated content — VERBATIM applies to the scaffolding around it.

- [ ] **Step 4: Add VERBATIM to Step 5c alignment failure warning**

Add `VERBATIM:` label before the alignment failure code block that starts with `⚠️ ALIGNMENT FAILURE`:

```
VERBATIM:
```
⚠️ ALIGNMENT FAILURE — Roadmap does not match the discussion.
...
```
```

- [ ] **Step 5: Add VERBATIM to Step 5d draft approval prompt**

Add `VERBATIM:` label before the approval prompt code block that starts with `Above is the draft Feature Roadmap`:

```
VERBATIM:
```
Above is the draft Feature Roadmap (<N> implementation steps).

Sections marked _NEEDS INPUT_ need your input.

[x] approved — write to disk
[ ] <describe changes needed>
```
```

- [ ] **Step 6: Add VERBATIM to Step 6c final summary**

Add `VERBATIM:` label before the final summary code block that starts with `=== PLANNING COMPLETE`:

```
VERBATIM:
```
=== PLANNING COMPLETE: <FeatureName> ===
...
```
```

- [ ] **Step 7: Run skill metadata tests**

Run: `python3 -m pytest tests/unit/test_skill_metadata.py -v`

Expected: All tests PASS (line count under 500, version consistent, etc.)

- [ ] **Step 8: Commit**

```bash
git add skills/plan-roadmap/SKILL.md
git commit -m "feat(plan-roadmap): add VERBATIM blocks to all fixed user-facing prompts"
```

---

### Task 8: Update active-guards.md for conversion mode

**Files:**
- Modify: `skills/plan-roadmap/references/active-guards.md`

- [ ] **Step 1: Find and update the Discussion → Planning guard**

The guard that says "If you are about to skip the Phase Gate (Discussion → Planning) — STOP" needs clarification. Update it to:

```markdown
If you are about to skip the Phase Gate approval checkpoint — STOP. The user must always approve the transition to Planning, whether they went through Phase 1 (Discussion) or entered via Conversion Mode (Step 0e). The gate protects the user's right to approve, not the existence of a discussion phase.
```

- [ ] **Step 2: Commit**

```bash
git add skills/plan-roadmap/references/active-guards.md
git commit -m "feat(plan-roadmap): update active-guards to allow conversion mode"
```

---

### Task 9: Update minor skill frontmatter (plan-bugfix-roadmap, list-roadmaps, describe-roadmap, repair-roadmap)

**Files:**
- Modify: `skills/plan-bugfix-roadmap/SKILL.md:1-7`
- Modify: `skills/list-roadmaps/SKILL.md:1-7`
- Modify: `skills/describe-roadmap/SKILL.md:1-7`
- Modify: `skills/repair-roadmap/SKILL.md:1-7`

- [ ] **Step 1: Update plan-bugfix-roadmap**

Remove `disable-model-invocation: true`. Bump version from `"5"` to `"6"`. Update version check output to `plan-bugfix-roadmap v6`. Update description to:

```yaml
description: "Create a bugfix roadmap from GitHub issues. Use when the user wants to plan bug fixes, organize issues into a roadmap, or batch fix multiple bugs."
```

- [ ] **Step 2: Update list-roadmaps**

Remove `disable-model-invocation: true`. Bump version from `"6"` to `"7"`. Update version check output to `list-roadmaps v7`. Update description to:

```yaml
description: "List active roadmaps with progress. Use when the user asks what roadmaps exist, wants to see roadmap status, or asks about pending work."
```

- [ ] **Step 3: Update describe-roadmap**

Remove `disable-model-invocation: true`. Bump version from `"5"` to `"6"`. Update version check output to `describe-roadmap v6`. Update description to:

```yaml
description: "Show detailed info about a roadmap — goal, progress, steps. Use when the user wants to inspect a roadmap, see step details, check progress, or review what's left."
```

- [ ] **Step 4: Update repair-roadmap**

Remove `disable-model-invocation: true`. Bump version from `"3"` to `"4"`. Update version check output to `repair-roadmap v4`. Update description to:

```yaml
description: "Repair a broken or stuck roadmap by re-planning incomplete steps. Use when a roadmap has stuck steps, needs re-planning, or the user says a roadmap is broken."
```

- [ ] **Step 5: Run tests to verify all 4 skills pass**

Run: `python3 -m pytest tests/unit/test_skill_metadata.py -v`

Expected: ALL tests PASS — especially `test_disable_model_invocation_policy` for these 4 skills

- [ ] **Step 6: Commit**

```bash
git add skills/plan-bugfix-roadmap/SKILL.md skills/list-roadmaps/SKILL.md skills/describe-roadmap/SKILL.md skills/repair-roadmap/SKILL.md
git commit -m "feat: enable auto-invoke on plan-bugfix-roadmap, list-roadmaps, describe-roadmap, repair-roadmap"
```

---

### Task 10: Add hook and rule installation to install.sh

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add a function to install the ExitPlanMode hook into settings.json**

Add after the `verify_dash_cli` function (~line 558):

```bash
# --- ExitPlanMode Hook Installation ---

install_exitplanmode_hook() {
    echo ""
    echo "--- ExitPlanMode Hook ---"

    local settings_file="$HOME/.claude/settings.json"

    if [ ! -f "$settings_file" ]; then
        echo "  [skip] No settings.json found at $settings_file"
        return
    fi

    # Check if the hook already exists
    if python3 -c "
import json, sys
with open('$settings_file') as f:
    d = json.load(f)
hooks = d.get('hooks', {}).get('PostToolUse', [])
for h in hooks:
    if h.get('matcher') == 'ExitPlanMode':
        sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        echo "  [ok] ExitPlanMode hook already installed"
        return
    fi

    # Merge the new hook entry into the PostToolUse array
    python3 -c "
import json

settings_file = '$settings_file'
with open(settings_file) as f:
    d = json.load(f)

import json as json_mod
msg = 'ROADMAP-EVAL: Consider the plan just discussed. Would it benefit from being tracked as a multi-step Roadmap with individual PRs per step? If yes, offer to convert it with one line. If no, say nothing.'
inner_json = json_mod.dumps({'systemMessage': msg})
cmd = \"echo '\" + inner_json.replace(\"'\", \"'\\\\''\") + \"'\"
d.setdefault('hooks', {}).setdefault('PostToolUse', []).append({
    'matcher': 'ExitPlanMode',
    'hooks': [{
        'type': 'command',
        'command': cmd
    }]
})

with open(settings_file, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "  [installed] ExitPlanMode hook"
    else
        echo "  [error] Could not install ExitPlanMode hook"
    fi
}
```

- [ ] **Step 2: Add a function to install the rule file**

Add after the hook function:

```bash
# --- Rule File Installation ---

install_rule_files() {
    local method="$1"

    echo ""
    echo "--- Rule Files ---"

    local rule_src="$SCRIPT_DIR/.claude/rules/ROADMAP-PLANNING-RULE.md"
    if [ ! -f "$rule_src" ]; then
        echo "  [skip] No ROADMAP-PLANNING-RULE.md in repo"
        return
    fi

    # Rules go to the consuming project's .claude/rules/ — but install.sh
    # runs from the cat-herding repo itself, so we install to the global
    # rules directory that Claude Code reads for all projects
    local target_dir="$HOME/.claude/rules"
    mkdir -p "$target_dir"
    local target="$target_dir/ROADMAP-PLANNING-RULE.md"

    if [ -L "$target" ] && [ "$(readlink "$target")" = "$rule_src" ]; then
        echo "  [ok] ROADMAP-PLANNING-RULE.md (symlink)"
    elif [ -f "$target" ]; then
        echo "  [reinstall] ROADMAP-PLANNING-RULE.md"
        rm -f "$target"
        if [ "$method" = "symlink" ]; then
            ln -s "$rule_src" "$target"
            echo "  [symlinked] ROADMAP-PLANNING-RULE.md"
        else
            cp "$rule_src" "$target"
            echo "  [copied] ROADMAP-PLANNING-RULE.md"
        fi
    else
        if [ "$method" = "symlink" ]; then
            ln -s "$rule_src" "$target"
            echo "  [symlinked] ROADMAP-PLANNING-RULE.md"
        else
            cp "$rule_src" "$target"
            echo "  [copied] ROADMAP-PLANNING-RULE.md"
        fi
    fi
}
```

- [ ] **Step 3: Add both functions to main()**

In the `main()` function, add after `install_cli_scripts`:

```bash
    install_exitplanmode_hook
    install_rule_files "$method"
```

- [ ] **Step 4: Bump install.sh VERSION**

Change `VERSION="1.0.0"` to `VERSION="1.1.0"`.

- [ ] **Step 5: Commit**

```bash
git add install.sh
git commit -m "feat(install): add ExitPlanMode hook and ROADMAP-PLANNING-RULE installation"
```

---

### Task 11: Add hook and rule removal to uninstall.sh

**Files:**
- Modify: `uninstall.sh`

- [ ] **Step 1: Add a function to remove the ExitPlanMode hook**

Add before the `main()` function:

```bash
# --- ExitPlanMode Hook Removal ---

remove_exitplanmode_hook() {
    echo ""
    echo "--- ExitPlanMode Hook ---"

    local settings_file="$HOME/.claude/settings.json"

    if [ ! -f "$settings_file" ]; then
        echo "  [skip] No settings.json"
        return
    fi

    python3 -c "
import json, sys

settings_file = '$settings_file'
with open(settings_file) as f:
    d = json.load(f)

hooks = d.get('hooks', {}).get('PostToolUse', [])
original_len = len(hooks)
hooks = [h for h in hooks if h.get('matcher') != 'ExitPlanMode']

if len(hooks) == original_len:
    sys.exit(1)  # not found

d['hooks']['PostToolUse'] = hooks
with open(settings_file, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "  [removed] ExitPlanMode hook"
    else
        echo "  [skip] ExitPlanMode hook not found"
    fi
}
```

- [ ] **Step 2: Add a function to remove the rule file**

```bash
# --- Rule File Removal ---

remove_rule_files() {
    echo ""
    echo "--- Rule Files ---"

    local target="$HOME/.claude/rules/ROADMAP-PLANNING-RULE.md"
    if [ -L "$target" ] || [ -f "$target" ]; then
        rm -f "$target"
        echo "  [removed] ROADMAP-PLANNING-RULE.md"
    else
        echo "  [skip] ROADMAP-PLANNING-RULE.md not found"
    fi
}
```

- [ ] **Step 3: Add both to main()**

In `main()`, add after `remove_cli_scripts`:

```bash
    remove_exitplanmode_hook
    remove_rule_files
```

- [ ] **Step 4: Commit**

```bash
git add uninstall.sh
git commit -m "feat(uninstall): add ExitPlanMode hook and ROADMAP-PLANNING-RULE removal"
```

---

### Task 12: Final verification

**Files:** None (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `cd /Users/mfullerton/projects/cat-herding && python3 -m pytest tests/ -v`

Expected: ALL tests pass, including the updated `test_disable_model_invocation_policy`

- [ ] **Step 2: Verify skill frontmatter is consistent**

Run: `python3 -m pytest tests/unit/test_skill_metadata.py -v`

Expected: ALL skill metadata tests pass

- [ ] **Step 3: Verify ROADMAP-PLANNING-RULE.md exists**

Run: `cat .claude/rules/ROADMAP-PLANNING-RULE.md`

Expected: Rule content matches spec

- [ ] **Step 4: Verify plan-roadmap has all new sections**

Grep for key markers:
```bash
grep -c "VERBATIM:" skills/plan-roadmap/SKILL.md
grep -c "Context Detection" skills/plan-roadmap/SKILL.md
grep -c "Output Rules" skills/plan-roadmap/SKILL.md
grep "version:" skills/plan-roadmap/SKILL.md | head -1
```

Expected: Multiple VERBATIM blocks, Context Detection present, Output Rules present, version "14"

- [ ] **Step 5: Commit any remaining fixes**

If any verification step found issues, fix and commit.
