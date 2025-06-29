REM filepath: c:\Users\Hp\Desktop\m1-project\build.bat
@echo off
echo Building C++ extension...

REM Install build dependencies
pip install pybind11[global] setuptools wheel

REM Clean previous builds
if exist build rmdir /s /q build
if exist fast_solver.*.pyd del fast_solver.*.pyd

REM Build the extension
python setup.py build_ext --inplace

if exist fast_solver.*.pyd (
    echo Build successful!
    echo Testing the extension...
    python test_cpp.py
) else (
    echo Build failed!
    pause
)