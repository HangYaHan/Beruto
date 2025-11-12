"""
Initialization for the `src.data` package.

Expose common submodules and allow safe imports during development when
not all modules may be present yet.
"""
__all__ = []

try:
    # Import common modules if available to provide package-level access
    from . import fetcher, storage, exceptions, adapters  # type: ignore
    __all__ = ["fetcher", "storage", "exceptions", "adapters"]
except Exception:
    # ignore import-time errors during early development
    pass