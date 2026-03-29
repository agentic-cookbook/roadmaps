---
name: import-shared-project
version: "2"
description: "Add a shared project reference to the current project's CLAUDE.md. Takes a project name (looked up in ~/projects/) or a Git URL (cloned next to the current project)."
argument-hint: "<project-name-or-git-url>"
disable-model-invocation: true
---

## Version Check

If `$ARGUMENTS` is `--version`, respond with exactly:

> import-shared-project v2

Then stop. Do not continue with the rest of the skill.

---

# Import Shared Project

Adds a reference block to the current project's CLAUDE.md so that Claude Code sessions know about a sibling project's specs, conventions, or shared code.

## Step 0: Parse Arguments

`$ARGUMENTS` is either:
- A **project name** (e.g., `litterbox`) — looked up in the workspace
- A **Git URL** (e.g., `git@github.com:user/repo.git` or `https://github.com/user/repo`) — cloned next to this project

If `$ARGUMENTS` is empty, ask the user:

```
What shared project do you want to import?

Enter a project name (I'll look in ~/projects/) or a Git URL to clone.
```

**STOP. Wait for the user's response.**

---

## Step 1: Resolve the Project

### If the argument looks like a Git URL (contains `github.com`, `gitlab.com`, `.git`, or `://`):

1. Extract the repo name from the URL (e.g., `litterbox` from `git@github.com:user/litterbox.git`)
2. Determine the target path: `../<repo_name>/` (next to the current project)
3. Check if it already exists:
   ```bash
   test -d "../<repo_name>" && echo "EXISTS" || echo "NOT_FOUND"
   ```
   - If `EXISTS`: print `Found existing clone at ../<repo_name>/` and continue to Step 2
   - If `NOT_FOUND`: clone it:
     ```bash
     git clone "<url>" "../<repo_name>"
     ```
     If clone fails, **STOP** and report the error.

Store:
- `PROJECT_NAME` = the repo name
- `PROJECT_PATH` = `../<repo_name>/`
- `PROJECT_URL` = the Git URL

### If the argument is a project name:

1. Look for the project in common workspace locations:
   ```bash
   for dir in "../<name>" "$HOME/projects/<name>"; do
     test -d "$dir" && echo "$dir" && break
   done
   ```
2. If found: use that path
3. If not found: ask the user:
   ```
   Project '<name>' not found in ../ or ~/projects/.

   Do you have a Git URL I can clone from?
   ```
   **STOP. Wait for the user's response.** Then follow the Git URL flow above.

Store:
- `PROJECT_NAME` = the project name
- `PROJECT_PATH` = the resolved relative path (prefer `../<name>/` if it works)
- `PROJECT_URL` = get from the project's git remote:
  ```bash
  git -C "$PROJECT_PATH" remote get-url origin 2>/dev/null || echo ""
  ```

---

## Step 2: Gather Context

Ask the user what this shared project provides:

```
Found <PROJECT_NAME> at <PROJECT_PATH>.

What does this project provide to the current project?
Examples:
  - "Component specs" (like UI specs, API specs)
  - "Shared libraries" (imported as a dependency)
  - "Configuration templates"
  - "Documentation and conventions"

Describe briefly:
```

**STOP. Wait for the user's response.**

Store the answer as `PURPOSE`.

---

## Step 3: Check for Spec Directory

Look for common spec/doc directories in the shared project:

```bash
ls "$PROJECT_PATH" | head -20
```

Also check for template files:

```bash
find "$PROJECT_PATH" -name "_template*" -o -name "*.template.*" 2>/dev/null | head -5
```

Store:
- `SPEC_DIR` = the directory containing specs (e.g., `ui/`, `specs/`, `docs/`) — or empty if none found
- `TEMPLATE_FILE` = path to a template file if one exists

---

## Step 4: Build the Reference Block

Construct the reference block to add to CLAUDE.md:

```markdown
## Shared Project: <PROJECT_NAME>

This project uses <PURPOSE> from the <PROJECT_NAME> repo.
Expected path: <PROJECT_PATH>
Repo: <PROJECT_URL>

Before reading any <PURPOSE>, verify <PROJECT_PATH> exists. If it doesn't, ask the user whether to clone it.

<PURPOSE_SPECIFIC_INSTRUCTIONS>
```

The `PURPOSE_SPECIFIC_INSTRUCTIONS` vary based on the purpose:

**For component specs:**
```
Component specs are in <PROJECT_PATH><SPEC_DIR> — read the spec and implement idiomatically for this project's platform.
When implementing any feature or component, first check for an existing spec. If none exists, offer to create one following <TEMPLATE_FILE> and save it back to that repo.
```

**For shared libraries:**
```
Shared library source is in <PROJECT_PATH> — reference it for API conventions and patterns.
```

**For documentation/conventions:**
```
Documentation is in <PROJECT_PATH> — follow the conventions described there.
```

**For other purposes:** adapt the instructions based on the user's description.

---

## Step 5: Present and Confirm

Print the reference block and ask:

```
I'll add this to your CLAUDE.md:

<reference block>

[x] looks good — add it
[ ] <changes needed>
```

**STOP. Wait for the user's response.**

If changes requested: revise and re-present.

---

## Step 6: Write to CLAUDE.md

Determine the CLAUDE.md location:

```bash
CLAUDE_MD="$(git rev-parse --show-toplevel)/CLAUDE.md"
```

If the file doesn't exist, create it with a header:

```markdown
# Project Rules
```

Append the reference block to the end of CLAUDE.md.

Verify by reading the file back.

---

## Step 7: Summary

Print:

```
=== SHARED PROJECT IMPORTED ===

Project: <PROJECT_NAME>
Path: <PROJECT_PATH>
Added to: CLAUDE.md

Claude Code sessions in this project will now know about <PROJECT_NAME>.
```
