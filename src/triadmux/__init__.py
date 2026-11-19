"""Local orchestration for AI coding CLIs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("triadmux")
except PackageNotFoundError:
    __version__ = "0.0.0"
