"""Local orchestration for AI coding CLIs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("firstchair")
except PackageNotFoundError:
    __version__ = "0.1.0a1"
