# Python Conventions

Guidelines specific to the cat-herding codebase and its Python libraries.

## 1. No external dependencies in core libraries

`roadmap_lib` uses the standard library only. Do not add PyYAML, requests, or other third-party packages to core library code. This keeps the library portable and installable without dependency management.

## 2. Testing

1. Use `pytest` for all tests.
2. Every change needs tests. Every bug fix needs a regression test.
3. Prioritize unit tests over integration tests.
4. Never remove or modify production dashboard data during testing — use demo port 9888, not production port 8888.

## 3. Type hints

Type hints are welcome but not required. Maintain Python 3.9 compatibility — use `from __future__ import annotations` or `typing` module forms (e.g., `list[str]` requires 3.9+, `Optional[str]` works everywhere).

## 4. File paths

Use `pathlib.Path`, not `os.path`. All path manipulation should go through `pathlib`.

```python
from pathlib import Path

roadmap_dir = Path.home() / ".roadmaps" / project_name
```

## 5. YAML frontmatter

Parse YAML frontmatter with the built-in frontmatter parser in `roadmap_lib`. Do not add a PyYAML dependency. The parser handles the `---` delimited frontmatter block at the top of markdown files.

## 6. Web services

Use Flask for web services. The dashboard service runs on Flask with a REST API and SSE/polling for live updates.

## 7. Database

Use SQLite with WAL mode for concurrent read access. No ORM — use direct SQL via the `sqlite3` standard library module.

```python
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
```

## 8. Use roadmap_lib

Use functions from `roadmap_lib` for all roadmap operations (reading state, parsing frontmatter, finding steps, etc.). Do not reimplement functionality that already exists in the library.

## 9. Deterministic IDs

Always use the roadmap file's own UUID from its YAML frontmatter. Never generate random UUIDs. IDs must be deterministic and reproducible.

## 10. Dashboard service is display-only

The dashboard service is a generic API and UI layer. It has no knowledge of git, files, or roadmap structure. Agents sync data to it; it only displays what it receives.

## 11. Shell scripts

Shell script `main()` functions must only call other functions — no inline logic. Keep scripts composable and testable.

## 12. Logging

Use the `logging` module with module-level loggers:

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Starting roadmap sync for %s", roadmap_id)
```
