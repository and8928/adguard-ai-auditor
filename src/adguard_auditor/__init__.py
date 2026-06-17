"""AdGuard AI Auditor package.

The version is sourced from a single place — ``pyproject.toml`` — so it only
ever has to be bumped there. It is exposed as ``__version__`` and reused by the
FastAPI app and the web dashboard.
"""
from pathlib import Path


def _read_version() -> str:
    # Primary source: pyproject.toml at the project root (always up to date).
    try:
        import tomllib

        pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        # Fallback for installed distributions where pyproject.toml is absent.
        try:
            from importlib.metadata import version

            return version("adguard-auditor")
        except Exception:
            return "0.0.0"


__version__ = _read_version()
