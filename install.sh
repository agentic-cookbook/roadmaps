#!/bin/bash
# Machine bootstrap for cat-herding shared Claude Code skills and agents.
# Run once on each new machine: ./install.sh
#
# What it does:
#   1. Installs Claude Code and GitHub CLI if missing
#   2. Installs shared skills into ~/.claude/skills/ (symlink or copy)
#   3. Installs shared agents into ~/.claude/agents/ (symlink or copy)
#   4. Installs shared skills into OpenClaw if present

VERSION="1.1.0"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
AGENTS_DIR="$CLAUDE_DIR/agents"

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
        echo "  Current install method: $current" > /dev/tty
    fi
    echo "" > /dev/tty
    echo -n "  Install skills as [s]ymlink or [c]opy? [s/c/q] " > /dev/tty
    local choice
    read -r choice < /dev/tty
    if [[ "$choice" =~ ^[qQ]$ ]]; then
        echo "quit"
        return
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
            echo "  [ok] $skill_name ($existing)"
        else
            if [ "$existing" != "none" ]; then
                echo "  [reinstall] $skill_name ($existing -> $method)"
                remove_skill "$target"
            fi
            install_skill "$skill_dir" "$SKILLS_DIR" "$method"
        fi
    done
}

# --- Agent Install Helpers ---

detect_agent_install_method() {
    local target="$1"
    if [ -L "$target" ]; then
        echo "symlink"
    elif [ -f "$target" ]; then
        echo "copy"
    else
        echo "none"
    fi
}

install_agent() {
    local agent_file="$1"
    local target_dir="$2"
    local method="$3"
    local agent_name
    agent_name=$(basename "$agent_file")
    local target="$target_dir/$agent_name"

    if [ "$method" = "symlink" ]; then
        ln -s "$agent_file" "$target"
        echo "  [symlinked] $agent_name"
    else
        cp "$agent_file" "$target"
        echo "  [copied] $agent_name"
    fi
}

# --- Claude Agents Installation ---

install_claude_agents() {
    local method="$1"

    echo ""
    echo "--- Agents Installation ---"

    if [ ! -d "$SCRIPT_DIR/agents" ] || [ -z "$(ls "$SCRIPT_DIR/agents"/*.md 2>/dev/null)" ]; then
        echo "  [skip] No agents found in repo"
        return
    fi

    mkdir -p "$AGENTS_DIR"

    for agent_file in "$SCRIPT_DIR/agents"/*.md; do
        [ -f "$agent_file" ] || continue
        local agent_name
        agent_name=$(basename "$agent_file")
        local target="$AGENTS_DIR/$agent_name"
        local existing
        existing=$(detect_agent_install_method "$target")

        if [ "$existing" = "$method" ]; then
            echo "  [ok] $agent_name ($existing)"
        else
            if [ "$existing" != "none" ]; then
                echo "  [reinstall] $agent_name ($existing -> $method)"
                rm -f "$target"
            fi
            install_agent "$agent_file" "$AGENTS_DIR" "$method"
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
            echo "  [ok] $skill_name ($existing)"
        elif [ "$existing" != "none" ]; then
            # Could be a built-in — don't remove automatically
            echo "  [skip] $skill_name (exists as $existing — may be built-in)"
        else
            install_skill "$skill_dir" "$openclaw_skills" "$method"
        fi
    done
}

# --- OpenClaw Agents Installation ---

install_openclaw_agents() {
    local method="$1"

    echo ""
    echo "--- OpenClaw Agents Installation ---"

    if [ ! -d "$SCRIPT_DIR/agents" ] || [ -z "$(ls "$SCRIPT_DIR/agents"/*.md 2>/dev/null)" ]; then
        echo "  [skip] No agents found in repo"
        return
    fi

    local openclaw_root=""
    for candidate in \
        "$(npm root -g 2>/dev/null)/openclaw" \
        "/opt/homebrew/lib/node_modules/openclaw" \
        "/usr/local/lib/node_modules/openclaw"; do
        if [ -d "$candidate" ]; then
            openclaw_root="$candidate"
            break
        fi
    done

    if [ -z "$openclaw_root" ]; then
        echo "  [skip] OpenClaw not found"
        return
    fi

    local openclaw_agents="$openclaw_root/agents"
    mkdir -p "$openclaw_agents"

    for agent_file in "$SCRIPT_DIR/agents"/*.md; do
        [ -f "$agent_file" ] || continue
        local agent_name
        agent_name=$(basename "$agent_file")
        local target="$openclaw_agents/$agent_name"
        local existing
        existing=$(detect_agent_install_method "$target")

        if [ "$existing" = "$method" ]; then
            echo "  [ok] $agent_name ($existing)"
        elif [ "$existing" != "none" ]; then
            echo "  [skip] $agent_name (exists as $existing — may be built-in)"
        else
            install_agent "$agent_file" "$openclaw_agents" "$method"
        fi
    done
}

# --- Remove Renamed Extensions ---
# Clean up old names from prior installs so they don't coexist with the new names.

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
        for candidate in \
            "$(npm root -g 2>/dev/null)/openclaw/skills" \
            "/opt/homebrew/lib/node_modules/openclaw/skills" \
            "/usr/local/lib/node_modules/openclaw/skills"; do
            if [ -d "$candidate/$name" ] || [ -L "$candidate/$name" ]; then
                rm -rf "$candidate/$name"
                echo "  [removed] skill $name from $candidate"
                found=1
            fi
        done
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

# --- Verify dash CLI ---
# The dash CLI inside progress-dashboard/references/ must be executable and
# match the installed version (symlink or copy).

verify_dash_cli() {
    local method="$1"
    local dash_installed="$SKILLS_DIR/progress-dashboard/references/dash"
    local dash_repo="$SCRIPT_DIR/skills/progress-dashboard/references/dash"

    echo ""
    echo "--- Verify dash CLI ---"

    if [ ! -f "$dash_repo" ]; then
        echo "  [skip] No dash CLI in repo"
        return
    fi

    if [ ! -f "$dash_installed" ]; then
        echo "  [error] dash CLI not found at $dash_installed"
        return
    fi

    # If copy method, ensure it matches the repo version
    if [ "$method" = "copy" ]; then
        if ! diff -q "$dash_repo" "$dash_installed" > /dev/null 2>&1; then
            cp "$dash_repo" "$dash_installed"
            echo "  [updated] dash CLI (copy was stale)"
        else
            echo "  [ok] dash CLI (copy matches repo)"
        fi
    else
        echo "  [ok] dash CLI (via symlinked skill dir)"
    fi

    # Ensure executable
    if [ ! -x "$dash_installed" ]; then
        chmod +x "$dash_installed"
        echo "  [fixed] dash CLI now executable"
    fi
}

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

msg = 'ROADMAP-EVAL: Consider the plan just discussed. Would it benefit from being tracked as a multi-step Roadmap with individual PRs per step? If yes, offer to convert it with one line. If no, say nothing.'
inner_json = json.dumps({'systemMessage': msg})
cmd = \"echo '\" + inner_json + \"'\"
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

# --- CLI Scripts Installation ---

install_cli_scripts() {
    echo ""
    echo "--- CLI Scripts ---"

    local scripts_dir="$SCRIPT_DIR/scripts"
    if [ ! -d "$scripts_dir" ]; then
        echo "  [skip] No scripts directory"
        return
    fi

    local bin_dir="/usr/local/bin"
    if [ ! -d "$bin_dir" ] || [ ! -w "$bin_dir" ]; then
        bin_dir="$HOME/.local/bin"
        mkdir -p "$bin_dir"
    fi

    # Library scripts (roadmap_lib.py etc.) — symlink to ~/.claude/scripts/
    # so that installed skills can import them
    local lib_dir="$HOME/.claude/scripts"
    mkdir -p "$lib_dir"

    for script in "$scripts_dir"/*.py; do
        [ -f "$script" ] || continue
        local name
        name=$(basename "$script" .py)

        # Library scripts (no shebang / not executable) go to ~/.claude/scripts/
        # CLI scripts (have shebang) go to bin_dir
        if head -1 "$script" | grep -q '^#!/'; then
            local target="$bin_dir/$name"
            if [ -L "$target" ] && [ "$(readlink "$target")" = "$script" ]; then
                echo "  [ok] $name -> $target (symlink)"
            else
                [ -e "$target" ] && rm -f "$target"
                ln -s "$script" "$target"
                echo "  [symlinked] $name -> $target"
            fi
        fi

        # Always symlink to ~/.claude/scripts/ for import access
        local lib_target="$lib_dir/$(basename "$script")"
        if [ -L "$lib_target" ] && [ "$(readlink "$lib_target")" = "$script" ]; then
            echo "  [ok] $(basename "$script") -> $lib_target (lib symlink)"
        else
            [ -e "$lib_target" ] && rm -f "$lib_target"
            ln -s "$script" "$lib_target"
            echo "  [symlinked] $(basename "$script") -> $lib_target (lib)"
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
    if [ "$method" = "quit" ]; then
        echo "  EXIT"
        return
    fi

    remove_renamed_extensions
    install_claude_skills "$method"
    install_claude_agents "$method"
    verify_dash_cli "$method"
    install_openclaw_skills "$method"
    install_openclaw_agents "$method"
    install_cli_scripts
    install_exitplanmode_hook
    install_rule_files "$method"

    echo ""
    echo "=== Done ==="
    echo "Shared skills and agents are now available in Claude Code."
}

main
