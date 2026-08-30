"""
Small path-resolution helper.

Mirrors the same "resolve relative paths against the project root, not the
process's current working directory" approach already used in
app/db/database.py — duplicated here (rather than importing from there) so
Phase 4 doesn't touch the existing database module.
"""

from pathlib import Path

# backend/app/core/paths.py -> parents[3] is the project root
# (ipo-research-platform/), i.e. the parent of backend/.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_project_path(relative: str) -> Path:
    """Resolve a project-relative path like './data/uploads' to an absolute
    Path anchored at the project root, regardless of where the process was
    started from."""
    cleaned = relative[2:] if relative.startswith("./") else relative
    return (PROJECT_ROOT / cleaned).resolve()
