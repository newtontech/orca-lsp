"""orca-lsp - Language Server Protocol for ORCA"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("orca-lsp")
except PackageNotFoundError:  # pragma: no cover - only used from an unpackaged source tree
    __version__ = "0.5.4"
