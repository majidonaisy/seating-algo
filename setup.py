from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup, Extension
import pybind11

# You need to find your OR-Tools installation path
# Common paths on Windows:
ORTOOLS_PATH = r"C:\Python313\Lib\site-packages\ortools"  # Adjust this path

ext_modules = [
    Pybind11Extension(
        "fast_solver",
        ["cpp_solver/solver.cpp"],
        include_dirs=[
            pybind11.get_cmake_dir() + "/../../../include",
            ORTOOLS_PATH + r"\..\..\..\include",  # OR-Tools headers
        ],
        libraries=["ortools"],
        library_dirs=[ORTOOLS_PATH + r"\.libs"],
        language='c++',
        cxx_std=17,
        define_macros=[("VERSION_INFO", '"dev"')],
    ),
]

setup(
    name="fast_solver",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
)