import ortools
import os
import sys

print("=== OR-Tools Installation Info ===")
print(f"Python version: {sys.version}")
print(f"OR-Tools version: {ortools.__version__}")

ortools_path = os.path.dirname(ortools.__file__)
print(f"OR-Tools path: {ortools_path}")

# Check for different possible include directories
possible_includes = [
    os.path.join(ortools_path, "include"),
    os.path.join(ortools_path, "..", "include"), 
    os.path.join(ortools_path, "..", "..", "include"),
    os.path.join(ortools_path, "..", "..", "..", "include"),
    # For conda installations
    os.path.join(sys.prefix, "include"),
    os.path.join(sys.prefix, "Library", "include"),
    # For pip installations  
    os.path.join(sys.prefix, "Lib", "site-packages", "ortools", "include"),
]

print(f"\nSearching for OR-Tools headers...")
found_include = None
for inc_path in possible_includes:
    cp_model_path = os.path.join(inc_path, "ortools", "sat", "cp_model.h")
    if os.path.exists(cp_model_path):
        print(f"✅ Found OR-Tools headers at: {inc_path}")
        found_include = inc_path
        break
    else:
        print(f"❌ Not found: {inc_path}")

# Check for libraries
libs_path = os.path.join(ortools_path, ".libs")
if os.path.exists(libs_path):
    print(f"✅ Found OR-Tools libraries at: {libs_path}")
    lib_files = [f for f in os.listdir(libs_path) if f.endswith('.dll') or f.endswith('.lib')]
    print(f"Library files: {lib_files}")
else:
    print(f"❌ No .libs directory found at: {libs_path}")

print(f"\n=== Configuration for setup.py ===")
if found_include:
    print(f'INCLUDE_PATH = r"{found_include}"')
else:
    print("❌ OR-Tools headers not found! You may need to install OR-Tools development headers.")

print(f'LIBS_PATH = r"{libs_path}"')