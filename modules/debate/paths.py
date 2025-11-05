from pathlib import Path

def find_repo_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__).resolve()).parent
    for _ in range(6):
        if (p / "pyproject.toml").exists() or (p / "main.py").exists():
            return p
        p = p.parent
    return (start or Path(__file__).resolve()).parents[3]

REPO_ROOT = find_repo_root()
LOG_DIR = REPO_ROOT / "logs" / "research_dialogs"
RESULTS_DIR = REPO_ROOT / "results"
