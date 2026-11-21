"""Record the Git commit in the built package. Everything else is in pyproject.toml."""

import importlib.util
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent


def checkout_commit() -> str | None:
    # Load the helper by path: the package itself is not importable during a build.
    spec = importlib.util.spec_from_file_location("_firstchair_init", ROOT / "src/firstchair/__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.checkout_commit(ROOT)


class BuildWithCommit(build_py):
    def run(self) -> None:
        super().run()
        commit = checkout_commit()
        if commit and not self.dry_run:
            target = Path(self.build_lib) / "firstchair" / "_build.py"
            target.write_text(f"COMMIT = {commit!r}\n", encoding="utf-8")


setup(cmdclass={"build_py": BuildWithCommit})
