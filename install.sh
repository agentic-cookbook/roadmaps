#!/bin/bash
# Machine bootstrap for cat-herding shared Claude Code skills.
# Run once on each new machine: ./install.sh
#
# What it does:
#   1. Installs Claude Code and GitHub CLI if missing
#   2. Installs shared skills into ~/.claude/skills/ (symlink or copy)
#   3. Installs shared skills into OpenClaw if present

VERSION="1.0.0"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"

# --- Platform Detection ---

detect_platform() {
    if [[ "$(uname -s)" == "Darwin" ]]; then echo "macos"
    elif grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl"
    else echo "linux"
    fi
}
PLATFORM="$(detect_platform)"

is_macos() { [[ "$PLATFORM" == "macos" ]]; }
is_wsl()   { [[ "$PLATFORM" == "wsl" ]]; }
is_linux() { [[ "$PLATFORM" == "linux" || "$PLATFORM" == "wsl" ]]; }

# --- Helpers ---

prompt_yn() {
    local prompt="$1"
    local reply
    echo -n "  $prompt [y/N/q] "
    read -r reply < /dev/tty
    if [[ "$reply" =~ ^[qQ]$ ]]; then
        echo "  EXIT"
        exit 0
    fi
    [[ "$reply" =~ ^[Yy]$ ]]
}

# --- Tool Check Functions (silent, return 0=installed / 1=missing) ---

check_claude_code() {
    command -v claude > /dev/null 2>&1 || [[ -x "$HOME/.local/bin/claude" ]]
}

check_github_cli() {
    command -v gh > /dev/null 2>&1
}

# --- Tool Install Functions (just install logic, no check or prompt) ---

do_install_claude_code() {
    echo "  INSTALL Claude Code ..."
    if curl -fsSL https://claude.ai/install.sh | bash > /dev/null 2>&1; then
        hash -r
        echo "  OK    Claude Code installed"
    else
        echo "  FAIL  could not install Claude Code, try manually: curl -fsSL https://claude.ai/install.sh | bash"
        return 1
    fi
}

do_install_github_cli() {
    if is_macos; then
        if ! command -v brew > /dev/null 2>&1; then
            echo "  SKIP  brew not found, install GitHub CLI manually: https://cli.github.com"
            return 1
        fi
        echo "  INSTALL GitHub CLI ..."
        if brew install gh > /dev/null 2>&1; then
            echo "  OK    GitHub CLI installed"
        else
            echo "  FAIL  could not install GitHub CLI, try manually: brew install gh"
            return 1
        fi
    elif is_linux; then
        echo "  INSTALL GitHub CLI (via apt) ..."
        if curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg > /dev/null 2>&1 && \
           echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
           sudo apt-get update -qq > /dev/null 2>&1 && \
           sudo apt-get install -y -qq gh > /dev/null 2>&1; then
            echo "  OK    GitHub CLI installed"
        else
            echo "  FAIL  could not install GitHub CLI, try manually: https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
            return 1
        fi
    fi
}

# --- Tool Registry ---
# Format: "display_name|check_fn|install_fn|platform"
# platform: "all" = both macOS+WSL+Linux, "macos" = macOS only, "wsl" = WSL only
TOOLS=(
    "Claude Code|check_claude_code|do_install_claude_code|all"
    "GitHub CLI|check_github_cli|do_install_github_cli|all"
)

# --- Batch Tool Scanner & Installer ---

scan_and_install_tools() {
    local missing_names=()
    local missing_install_fns=()

    echo ""
    for entry in "${TOOLS[@]}"; do
        local name="${entry%%|*}"
        local rest="${entry#*|}"
        local check_fn="${rest%%|*}"
        rest="${rest#*|}"
        local install_fn="${rest%%|*}"
        local tool_platform="${rest#*|}"

        # Skip tools not for this platform
        if [[ "$tool_platform" == "macos" ]] && ! is_macos; then continue; fi
        if [[ "$tool_platform" == "wsl" ]] && ! is_wsl; then continue; fi

        if "$check_fn"; then
            echo "  OK    $name"
        else
            echo "  MISS  $name"
            missing_names+=("$name")
            missing_install_fns+=("$install_fn")
        fi
    done

    if [[ ${#missing_names[@]} -eq 0 ]]; then
        echo ""
        echo "  All tools are installed!"
        return
    fi

    # Interactive install loop — re-prompt after each pick
    while [[ ${#missing_names[@]} -gt 0 ]]; do
        echo ""
        echo "  Missing tools:"
        for i in "${!missing_names[@]}"; do
            echo "    $((i + 1)). ${missing_names[$i]}"
        done

        echo ""
        echo -n "  Press Enter to install all, enter a number to install one, [s] to skip, or [q] to quit: "
        local choice
        read -r choice < /dev/tty

        if [[ -z "$choice" ]]; then
            # Default: install all
            local still_missing_names=()
            local still_missing_fns=()
            for i in "${!missing_names[@]}"; do
                echo ""
                echo "  --- Installing ${missing_names[$i]} ---"
                if ! "${missing_install_fns[$i]}"; then
                    if ! prompt_yn "Installation failed. Continue?"; then
                        echo "  ABORT"
                        return 1
                    fi
                    still_missing_names+=("${missing_names[$i]}")
                    still_missing_fns+=("${missing_install_fns[$i]}")
                fi
            done
            missing_names=("${still_missing_names[@]+"${still_missing_names[@]}"}")
            missing_install_fns=("${still_missing_fns[@]+"${still_missing_fns[@]}"}")
        elif [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#missing_names[@]} )); then
            local idx=$((choice - 1))
            echo ""
            echo "  --- Installing ${missing_names[$idx]} ---"
            if ! "${missing_install_fns[$idx]}"; then
                if ! prompt_yn "Installation failed. Continue?"; then
                    echo "  ABORT"
                    return 1
                fi
            else
                # Remove installed item from arrays
                local new_names=() new_fns=()
                for i in "${!missing_names[@]}"; do
                    if [[ $i -ne $idx ]]; then
                        new_names+=("${missing_names[$i]}")
                        new_fns+=("${missing_install_fns[$i]}")
                    fi
                done
                missing_names=("${new_names[@]+"${new_names[@]}"}")
                missing_install_fns=("${new_fns[@]+"${new_fns[@]}"}")
            fi
        elif [[ "$choice" =~ ^[sS]$ ]]; then
            echo "  SKIP  all missing tools"
            return
        elif [[ "$choice" =~ ^[qQ]$ ]]; then
            echo "  EXIT"
            exit 0
        else
            echo "  Invalid choice, try again."
        fi
    done

    echo ""
    echo "  All selected tools installed!"
}

# --- Skills Install Helpers ---

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

remove_skill() {
    local target="$1"
    if [ -L "$target" ]; then
        rm "$target"
    elif [ -d "$target" ]; then
        rm -rf "$target"
    fi
}

install_skill() {
    local skill_dir="$1"
    local target_dir="$2"
    local method="$3"
    local skill_name
    skill_name=$(basename "$skill_dir")
    local target="$target_dir/$skill_name"

    if [ "$method" = "symlink" ]; then
        ln -s "$skill_dir" "$target"
        echo "  [symlinked] $skill_name"
    else
        cp -R "$skill_dir" "$target"
        echo "  [copied] $skill_name"
    fi
}

detect_current_method() {
    for skill_dir in "$SCRIPT_DIR/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        local skill_name
        skill_name=$(basename "$skill_dir")
        local method
        method=$(detect_install_method "$SKILLS_DIR/$skill_name")
        if [ "$method" != "none" ]; then
            echo "$method"
            return
        fi
    done
    echo "none"
}

prompt_install_method() {
    local current="$1"
    if [ "$current" != "none" ]; then
        echo "  Current install method: $current"
    fi
    echo ""
    echo -n "  Install skills as [s]ymlink or [c]opy? [s/c/q] "
    local choice
    read -r choice < /dev/tty
    if [[ "$choice" =~ ^[qQ]$ ]]; then
        echo "  EXIT"
        exit 0
    elif [[ "$choice" =~ ^[cC]$ ]]; then
        echo "copy"
    else
        echo "symlink"
    fi
}

# --- Claude Skills Installation ---

install_claude_skills() {
    local method="$1"

    echo ""
    echo "--- Skills Installation ---"

    mkdir -p "$SKILLS_DIR"

    for skill_dir in "$SCRIPT_DIR/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        local skill_name
        skill_name=$(basename "$skill_dir")
        local target="$SKILLS_DIR/$skill_name"
        local existing
        existing=$(detect_install_method "$target")

        if [ "$existing" = "$method" ]; then
            echo "  [ok] $skill_name (already ${method}ed)"
        else
            if [ "$existing" != "none" ]; then
                echo "  [reinstall] $skill_name ($existing -> $method)"
                remove_skill "$target"
            fi
            install_skill "$skill_dir" "$SKILLS_DIR" "$method"
        fi
    done
}

# --- OpenClaw Skills Installation ---

install_openclaw_skills() {
    local method="$1"

    echo ""
    echo "--- OpenClaw Skills Installation ---"

    local openclaw_skills=""
    for candidate in \
        "$(npm root -g 2>/dev/null)/openclaw/skills" \
        "/opt/homebrew/lib/node_modules/openclaw/skills" \
        "/usr/local/lib/node_modules/openclaw/skills"; do
        if [ -d "$candidate" ]; then
            openclaw_skills="$candidate"
            break
        fi
    done

    if [ -z "$openclaw_skills" ]; then
        echo "  [skip] OpenClaw not found — skipping OpenClaw skill install"
        return
    fi

    echo "  OpenClaw skills dir: $openclaw_skills"
    echo "  Using same method: $method"
    for skill_dir in "$SCRIPT_DIR/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        local skill_name
        skill_name=$(basename "$skill_dir")
        local target="$openclaw_skills/$skill_name"
        local existing
        existing=$(detect_install_method "$target")

        if [ "$existing" = "$method" ]; then
            echo "  [ok] $skill_name (already ${method}ed)"
        elif [ "$existing" != "none" ]; then
            # Could be a built-in — don't remove automatically
            echo "  [skip] $skill_name (exists as $existing — may be built-in)"
        else
            install_skill "$skill_dir" "$openclaw_skills" "$method"
        fi
    done
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "=== Cat Herding Setup (v${VERSION}) ==="
    echo "Repo: $SCRIPT_DIR"

    echo ""
    echo "--- Checking Tools ---"
    scan_and_install_tools

    local current_method
    current_method=$(detect_current_method)

    local method
    method=$(prompt_install_method "$current_method")

    install_claude_skills "$method"
    install_openclaw_skills "$method"

    echo ""
    echo "=== Done ==="
    echo "Shared skills are now available in Claude Code."
}

main
