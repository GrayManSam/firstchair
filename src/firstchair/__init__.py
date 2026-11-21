"""Local orchestration for AI coding CLIs."""

import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("firstchair")
except PackageNotFoundError:
    __version__ = "0.1.0a2"


def checkout_commit(root: Path) -> str | None:
    """The short commit of the Git checkout at ``root``, marked when files differ from it."""
    if not (root / ".git").exists():
        return None
    try:
        def git(*args: str) -> str:
            return subprocess.run(
                ("git", "-C", str(root), *args), capture_output=True, text=True, timeout=5, check=True,
            ).stdout.strip()
        commit = git("rev-parse", "--short", "HEAD")
        return f"{commit}, modified" if git("status", "--porcelain", "--untracked-files=no") else commit
    except (OSError, subprocess.SubprocessError):
        return None


def build_commit() -> str | None:
    """The commit this copy was built from, so a stale install can be told from a current one."""
    try:
        from ._build import COMMIT  # Written by setup.py when the package is built.
    except ImportError:
        # Running from the source tree: src/firstchair/__init__.py sits two levels down.
        return checkout_commit(Path(__file__).resolve().parents[2])
    return COMMIT if isinstance(COMMIT, str) and COMMIT else None


def describe_version() -> str:
    commit = build_commit()
    return f"{__version__} ({commit})" if commit else __version__
