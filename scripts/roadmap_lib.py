"""Shared roadmap discovery and parsing library.

Centralizes roadmap directory scanning, state reading, frontmatter
parsing, and step counting — used by the coordinator, cross-repo scanner,
display scripts, and migration tools.

Supports both the new per-directory layout (Roadmaps/YYYY-MM-DD-Name/)
and the old flat layout (Roadmaps/Active/, Definitions/, Completed/)
during the transition period.

No external dependencies — uses a simple YAML frontmatter parser
that handles the key-value and list structures used in roadmap files.
"""

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# YAML frontmatter parser (no PyYAML dependency)
# ---------------------------------------------------------------------------

def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file.

    Returns (metadata_dict, body_string).  If no frontmatter is found,
    returns ({}, full_content).

    Handles:
      - Simple key: value pairs
      - Nested list-of-dicts (change-history)
      - Quoted and unquoted string values
    """
    content = Path(filepath).read_text()
    if not content.startswith("---"):
        return {}, content

    end = content.find("\n---", 3)
    if end == -1:
        return {}, content

    fm_block = content[4:end]  # skip opening "---\n"
    body = content[end + 4:]   # skip closing "\n---"
    if body.startswith("\n"):
        body = body[1:]

    return _parse_yaml_block(fm_block), body


def _parse_yaml_block(block):
    """Parse a simple YAML block into a dict."""
    result = {}
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        # Top-level key: value
        m = re.match(r"^(\S[\w-]*)\s*:\s*(.*)", line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        value = m.group(2).strip()

        if not value:
            # Could be a list or nested structure
            items = []
            i += 1
            while i < len(lines):
                child = lines[i]
                if not child.strip() or (not child.startswith(" ") and not child.startswith("\t")):
                    break
                if child.strip().startswith("- "):
                    # Start of a list item — collect its fields
                    item = _parse_list_item(child)
                    i += 1
                    # Collect continuation lines (indented further)
                    while i < len(lines):
                        cont = lines[i]
                        if not cont.strip():
                            i += 1
                            continue
                        indent = len(cont) - len(cont.lstrip())
                        if indent >= 4 and not cont.strip().startswith("- "):
                            item.update(_parse_list_item("  - " + cont.strip()))
                            i += 1
                        else:
                            break
                    items.append(item)
                else:
                    i += 1
            result[key] = items
        else:
            # Strip quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            result[key] = value
            i += 1

    return result


def _parse_list_item(line):
    """Parse a YAML list item line like '  - key: value' into a dict."""
    stripped = line.strip()
    if stripped.startswith("- "):
        stripped = stripped[2:]
    m = re.match(r"(\S[\w-]*)\s*:\s*(.*)", stripped)
    if m:
        val = m.group(2).strip()
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        return {m.group(1): val}
    return {}


def write_frontmatter(metadata, body=""):
    """Render a metadata dict + body into a markdown string with YAML frontmatter."""
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        prefix = "  - " if first else "    "
                        lines.append(f"{prefix}{k}: {v}")
                        first = False
                else:
                    lines.append(f"  - {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    if body:
        return "\n".join(lines) + "\n\n" + body
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Roadmap discovery (supports old + new layouts)
# ---------------------------------------------------------------------------

def find_roadmap_dirs(repo_dir):
    """Find all roadmap directories in a repo (new layout).

    Returns list of Path objects for directories containing Roadmap.md.
    """
    roadmaps_dir = Path(repo_dir) / "Roadmaps"
    if not roadmaps_dir.exists():
        return []
    dirs = []
    for d in sorted(roadmaps_dir.iterdir()):
        if d.is_dir() and (d / "Roadmap.md").exists():
            dirs.append(d)
    return dirs


def find_roadmaps_old_layout(repo_dir):
    """Find roadmaps using the old flat layout (Active/Completed/Definitions).

    Returns list of dicts with 'name', 'roadmap_path', 'definition_path',
    'summary_path', 'location' (active/completed).
    """
    roadmaps_dir = Path(repo_dir) / "Roadmaps"
    if not roadmaps_dir.exists():
        return []

    results = []
    seen_names = set()

    # Scan Active
    for subdir_name, location in [("Active", "active"), ("Completed", "completed")]:
        subdir = roadmaps_dir / subdir_name
        if not subdir.exists():
            continue
        for f in sorted(list(subdir.glob("*-Roadmap.md")) + list(subdir.glob("*-FeatureRoadmap.md"))):
            name = f.stem.replace("-Roadmap", "").replace("-FeatureRoadmap", "")
            if name in seen_names:
                continue
            seen_names.add(name)
            def_path = roadmaps_dir / "Definitions" / f"{name}-Definition.md"
            summary_path = roadmaps_dir / "Completed" / f"{name}-Summary.md"
            results.append({
                "name": name,
                "roadmap_path": f,
                "definition_path": def_path if def_path.exists() else None,
                "summary_path": summary_path if summary_path.exists() else None,
                "location": location,
            })

    # Scan Definitions for orphans (definition exists but no roadmap)
    defs_dir = roadmaps_dir / "Definitions"
    if defs_dir.exists():
        for f in sorted(defs_dir.glob("*-Definition.md")):
            name = f.stem.replace("-Definition", "")
            if name not in seen_names:
                results.append({
                    "name": name,
                    "definition_path": f,
                    "roadmap_path": None,
                    "summary_path": None,
                    "location": "definition_only",
                })

    return results


def is_new_layout(repo_dir):
    """Check if a repo uses the new per-directory layout."""
    dirs = find_roadmap_dirs(repo_dir)
    return len(dirs) > 0


# ---------------------------------------------------------------------------
# State reading (new layout)
# ---------------------------------------------------------------------------

ACTIVE_STATES = {"Created", "Planning", "Ready", "Implementing", "Paused"}
COMPLETE_STATES = {"Complete"}


def current_state(roadmap_dir):
    """Get the current state from the newest file in State/.

    Filename format: YYYY-MM-DD-StateName.md
    Returns the StateName portion, or 'Unknown'.
    """
    state_dir = Path(roadmap_dir) / "State"
    if not state_dir.exists():
        return "Unknown"
    files = sorted(state_dir.glob("*.md"))
    if not files:
        return "Unknown"
    # "2026-03-24-Complete" → "Complete"
    stem = files[-1].stem
    parts = stem.split("-", 3)
    return parts[3] if len(parts) >= 4 else "Unknown"


def is_active(roadmap_dir):
    """Check if a roadmap is active (not completed)."""
    return current_state(roadmap_dir) in ACTIVE_STATES


def is_implementable(roadmap_dir):
    """Check if a roadmap is ready for implementation.

    Replaces the old Phase=Ready AND Status!=Complete check.
    """
    return current_state(roadmap_dir) == "Ready"


# ---------------------------------------------------------------------------
# Feature name and path helpers
# ---------------------------------------------------------------------------

def get_feature_name(roadmap_dir):
    """Extract feature name from a roadmap directory.

    Directory format: YYYY-MM-DD-FeatureName → FeatureName.
    Falls back to parsing the Roadmap.md heading.
    """
    dirname = Path(roadmap_dir).name
    parts = dirname.split("-", 3)
    if len(parts) >= 4:
        return parts[3]

    # Fallback: parse heading
    roadmap_path = Path(roadmap_dir) / "Roadmap.md"
    if roadmap_path.exists():
        content = roadmap_path.read_text()
        m = re.search(r"^# Feature Roadmap:\s*(.+)", content, re.MULTILINE)
        if m:
            return m.group(1).strip()

    return dirname


def roadmap_path(roadmap_dir):
    """Return the Roadmap.md path for a roadmap directory."""
    return Path(roadmap_dir) / "Roadmap.md"


def definition_path(roadmap_dir):
    """Return the Definition.md path for a roadmap directory."""
    return Path(roadmap_dir) / "Definition.md"


def summary_path(roadmap_dir):
    """Return the Summary.md path for a roadmap directory."""
    return Path(roadmap_dir) / "Summary.md"


# ---------------------------------------------------------------------------
# Step parsing (works on Roadmap.md content — unchanged from coordinator)
# ---------------------------------------------------------------------------

def count_steps(roadmap_file):
    """Count total and complete steps in a Roadmap.md file."""
    content = Path(roadmap_file).read_text()
    total = len(re.findall(r"^### Step \d+:", content, re.MULTILINE))
    complete = len(re.findall(
        r"^\- \*\*Status\*\*:\s*Complete", content, re.MULTILINE | re.IGNORECASE
    ))
    return total, complete


def parse_roadmap_heading(roadmap_file):
    """Extract feature name from a Roadmap.md file heading."""
    content = Path(roadmap_file).read_text()
    m = re.search(r"^# Feature Roadmap:\s*(.+)", content, re.MULTILINE)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Inline field parsing (old layout — for migration and backward compat)
# ---------------------------------------------------------------------------

def parse_inline_fields(content):
    """Parse **Field**: value pairs from markdown content.

    Returns a dict of field_name -> value.
    """
    fields = {}
    for m in re.finditer(r"^\*\*(.+?)\*\*:\s*(.+)$", content, re.MULTILINE):
        fields[m.group(1).strip()] = m.group(2).strip()
    return fields
