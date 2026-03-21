#!/bin/bash
# Remove cat-herding shared skills from this machine.
# Run: ./uninstall.sh
#
# What it does:
#   1. Removes shared skills from ~/.claude/skills/
#   2. Removes shared skills from OpenClaw if present
#   Does NOT uninstall Claude Code or GitHub CLI.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"

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

# =============================================================================
# Main
# =============================================================================

main() {
    echo "=== Cat Herding Uninstall ==="
    echo "Repo: $SCRIPT_DIR"

    remove_skills "$SKILLS_DIR" "Claude Skills"

    local openclaw_dir
    openclaw_dir=$(find_openclaw_skills_dir)
    if [ -n "$openclaw_dir" ]; then
        remove_skills "$openclaw_dir" "OpenClaw Skills"
    fi

    echo ""
    echo "=== Done ==="
}

main
