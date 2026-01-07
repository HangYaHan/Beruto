from importlib import import_module

# Lazy import compiled extension; module name must match PYBIND11_MODULE
_core = import_module("Beruto_core")
ChronoEngine = _core.ChronoEngine

__all__ = ["ChronoEngine"]
