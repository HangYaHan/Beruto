from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pathlib import Path
import sys

compile_args = []
link_args = []
if sys.platform == "win32":
    compile_args.append("/std:c++17")
else:
    compile_args.append("-std=c++17")

this_dir = Path(__file__).parent

ext_modules = [
    Pybind11Extension(
        "Beruto_core",
        sources=[
            str(this_dir / "src" / "engine.cpp"),
            str(this_dir / "src" / "bindings.cpp"),
        ],
        include_dirs=[str(this_dir / "src")],
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    )
]

setup(
    name="Beruto_core",
    author="YaHan",
    description="ChronoEngine C++ core with pybind11 bindings",
    packages=["wrapper"],
    package_dir={"wrapper": "wrapper"},
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.9",
)
