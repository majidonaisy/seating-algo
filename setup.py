from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup, Extension

ext_modules = [
    Pybind11Extension(
        "fast_solver",
        ["cpp_solver/solver.cpp"],
        include_dirs=[
            # Path to OR-Tools include directory
            "C:/or-tools/include",
        ],
        libraries=["ortools"],
        library_dirs=["C:/or-tools/lib"],
        cxx_std=17,
    ),
]

setup(
    name="fast_solver",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)