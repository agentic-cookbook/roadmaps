#!/bin/bash
# Remove cat-herding shared skills and agents from this machine.
# Run: ./uninstall.sh
#
# What it does:
#   1. Removes shared skills from ~/.claude/skills/
#   2. Removes shared agents from ~/.claude/agents/
#   3. Removes shared skills from OpenClaw if present
#   Does NOT uninstall Claude Code or GitHub CLI.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
AGENTS_DIR="$CLAUDE_DIR/agents"

# --- Helpers ---

prompt_yn() {
    local prompt="$1"
    local reply
    echo -n "  $prompt [y/N] "
    read -r reply < /dev/tty
    [[ "$reply" =~ ^[Yy]$ ]]
}

detect_install_method() {
    local target="$1"
    if [ -L "$target" ]; then
        echo "symlink"
    elif [ -d "$target" ]; then
        echo "copy"
    else
        echo "none"
    fi
}

# --- Skill Removal ---

find_installed_skills() {
    local target_dir="$1"
    local found=()
    for skill_dir in "$SCRIPT_DIR/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        local skill_name
        skill_name=$(basename "$skill_dir")
        local target="$target_dir/$skill_name"
        local method
        method=$(detect_install_method "$target")
        if [ "$method" != "none" ]; then
            found+=("$skill_name|$method")
        fi
    done
    printf '%s\n' "${found[@]}"
}

remove_skills() {
    local target_dir="$1"
    local label="$2"

    echo ""
    echo "--- $label ---"

    if [ ! -d "$target_dir" ]; then
        echo "  [skip] $target_dir does not exist"
        return
    fi

    local installed
    installed=$(find_installed_skills "$target_dir")

    if [ -z "$installed" ]; then
        echo "  No cat-herding skills found in $target_dir"
        return
    fi

    echo "  Found in $target_dir:"
    while IFS='|' read -r name method; do
        echo "    $name ($method)"
    done <<< "$installed"

    echo ""
    if ! prompt_yn "Remove these skills?"; then
        echo "  [skip] kept all skills"
        return
    fi

    while IFS='|' read -r name method; do
        local target="$target_dir/$name"
        if [ -L "$target" ]; then
            rm "$target"
        elif [ -d "$target" ]; then
            rm -rf "$target"
        fi
        echo "  [removed] $name ($method)"
    done <<< "$installed"
}

# --- Agent Removal ---

find_installed_agents() {
    local target_dir="$1"
    local found=()
    for agent_file in "$SCRIPT_DIR/agents"/*.md; do
        [ -f "$agent_file" ] || continue
        local agent_name
        agent_name=$(basename "$agent_file")
        local target="$target_dir/$agent_name"
        if [ -L "$target" ]; then
            found+=("$agent_name|symlink")
        elif [ -f "$target" ]; then
            found+=("$agent_name|copy")
        fi
    done
    printf '%s\n' "${found[@]}"
}

remove_agents() {
    local target_dir="$1"
    local label="$2"

    echo ""
    echo "--- $label ---"

    if [ ! -d "$target_dir" ]; then
        echo "  [skip] $target_dir does not exist"
        return
    fi

    if [ ! -d "$SCRIPT_DIR/agents" ]; then
        echo "  No agents directory in repo"
        return
    fi

    local installed
    installed=$(find_installed_agents "$target_dir")

    if [ -z "$installed" ]; then
        echo "  No cat-herding agents found in $target_dir"
        return
    fi

    echo "  Found in $target_dir:"
    while IFS='|' read -r name method; do
        echo "    $name ($method)"
    done <<< "$installed"

    echo ""
    if ! prompt_yn "Remove these agents?"; then
        echo "  [skip] kept all agents"
        return
    fi

    while IFS='|' read -r name method; do
        local target="$target_dir/$name"
        rm -f "$target"
        echo "  [removed] $name ($method)"
    done <<< "$installed"
}

find_openclaw_skills_dir() {
    for candidate in \
        "$(npm root -g 2>/dev/null)/openclaw/skills" \
        "/opt/homebrew/lib/node_modules/openclaw/skills" \
        "/usr/local/lib/node_modules/openclaw/skills"; do
        if [ -d "$candidate" ]; then
            echo "$candidate"
            return
        fi
    done
}

find_openclaw_agents_dir() {
    for candidate in \
        "$(npm root -g 2>/dev/null)/openclaw/agents" \
        "/opt/homebrew/lib/node_modules/openclaw/agents" \
        "/usr/local/lib/node_modules/openclaw/agents"; do
        if [ -d "$candidate" ]; then
            echo "$candidate"
            return
        fi
    done
}

# --- Remove Renamed Extensions ---

RENAMED_SKILLS=(plan-feature implement-feature implement-roadmap)
RENAMED_AGENTS=(implement-feature-auto.md implement-roadmap-auto.md implement-roadmap-agent.md)

remove_renamed_extensions() {
    echo ""
    echo "--- Cleaning Up Old Names ---"

    local found=0

    for name in "${RENAMED_SKILLS[@]}"; do
        for dir in "$SKILLS_DIR"; do
            local target="$dir/$name"
            if [ -L "$target" ] || [ -d "$target" ]; then
                rm -rf "$target"
                echo "  [removed] skill $name from $dir"
                found=1
            fi
        done
        local openclaw_dir
        openclaw_dir=$(find_openclaw_skills_dir)
        if [ -n "$openclaw_dir" ]; then
            local target="$openclaw_dir/$name"
            if [ -L "$target" ] || [ -d "$target" ]; then
                rm -rf "$target"
                echo "  [removed] skill $name from $openclaw_dir"
                found=1
            fi
        fi
    done

    for name in "${RENAMED_AGENTS[@]}"; do
        local target="$AGENTS_DIR/$name"
        if [ -L "$target" ] || [ -f "$target" ]; then
            rm -f "$target"
            echo "  [removed] agent $name from $AGENTS_DIR"
            found=1
        fi
    done

    if [ "$found" -eq 0 ]; then
        echo "  No old names found"
    fi
}

# --- CLI Scripts Removal ---

remove_cli_scripts() {
    echo ""
    echo "--- CLI Scripts ---"

    local scripts_dir="$SCRIPT_DIR/scripts"
    [ -d "$scripts_dir" ] || return

    for script in "$scripts_dir"/*.py; do
        [ -f "$script" ] || continue
        local name
        name=$(basename "$script" .py)
        for bin_dir in "/usr/local/bin" "$HOME/.local/bin"; do
            local target="$bin_dir/$name"
            if [ -L "$target" ]; then
                rm -f "$target"
                echo "  [removed] $name from $bin_dir"
            fi
        done
    done
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "=== Cat Herding Uninstall ==="
    echo "Repo: $SCRIPT_DIR"

    remove_renamed_extensions
    remove_skills "$SKILLS_DIR" "Claude Skills"
    remove_agents "$AGENTS_DIR" "Claude Agents"
    remove_cli_scripts

    local openclaw_dir
    openclaw_dir=$(find_openclaw_skills_dir)
    if [ -n "$openclaw_dir" ]; then
        remove_skills "$openclaw_dir" "OpenClaw Skills"
    fi

    local openclaw_agents_dir
    openclaw_agents_dir=$(find_openclaw_agents_dir)
    if [ -n "$openclaw_agents_dir" ]; then
        remove_agents "$openclaw_agents_dir" "OpenClaw Agents"
    fi

    echo ""
    echo "=== Done ==="
}

main
