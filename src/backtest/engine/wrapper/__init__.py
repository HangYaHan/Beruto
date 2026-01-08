from importlib import import_module
from pathlib import Path
import sys

# Lazy import compiled extension; module name must match PYBIND11_MODULE
try:
	_core = import_module("Beruto_core")
except ModuleNotFoundError:
	root = Path(__file__).resolve().parents[1]
	build_dir = root / "build"
	if build_dir.exists():
		# First, try by adding build lib dirs to sys.path
		for libdir in sorted(build_dir.glob("lib.*")):
			sys.path.insert(0, str(libdir))
			try:
				_core = import_module("Beruto_core")
				break
			except ModuleNotFoundError:
				continue
		# If still not found, try loading the .pyd directly
		if "_core" not in locals():
			import importlib.util
			for pyd in sorted(build_dir.glob("lib.*")):
				for candidate in pyd.glob("Beruto_core*.pyd"):
					spec = importlib.util.spec_from_file_location("Beruto_core", candidate)
					if spec and spec.loader:
						module = importlib.util.module_from_spec(spec)
						spec.loader.exec_module(module)
						_core = module
						break
				if "_core" in locals():
					break
	if "_core" not in locals():
		raise

ChronoEngine = _core.ChronoEngine

__all__ = ["ChronoEngine"]
