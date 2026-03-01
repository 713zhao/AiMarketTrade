#!/usr/bin/env python3
"""
Quick validation script for deerflow-openbb Phase 1 installation.

Checks Python version, dependency availability, and basic configuration.
Does not require API keys or full installation.
"""

import sys
import importlib.util
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        return False
    print("✅ Python version OK")
    return True


def check_dependencies():
    """Check if key dependencies are available."""
    required = [
        "pydantic",
        "pydantic_settings",
        "langgraph",
        "openbb",
        "pandas",
        "numpy",
    ]

    missing = []
    available = []

    for package in required:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing.append(package)
        else:
            available.append(package)

    print(f"\nDependencies:")
    print(f"  Available: {', '.join(available) if available else 'None'}")
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        print(f"  → Install with: pip install -e '.[dev]'")

    return len(missing) == 0


def check_project_structure():
    """Check project files exist."""
    project_root = Path(__file__).parent
    required_files = [
        "pyproject.toml",
        "README.md",
        ".env.template",
        "src/__init__.py",
        "src/config.py",
        "src/state.py",
        "src/nodes.py",
        "src/graph.py",
        "src/main.py",
        "tests/__init__.py",
        "tests/test_config.py",
        "tests/test_state.py",
        "tests/test_nodes.py",
        "tests/test_integration.py",
    ]

    print(f"\nProject structure:")
    all_exist = True
    for file in required_files:
        filepath = project_root / file
        exists = filepath.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False

    return all_exist


def check_syntax():
    """Validate Python syntax of all modules."""
    print(f"\nSyntax validation:")
    project_root = Path(__file__).parent

    py_files = list((project_root / "src").glob("*.py"))
    py_files.extend(list((project_root / "tests").glob("*.py")))

    errors = []
    for py_file in py_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file.name, 'exec')
            print(f"  ✅ {py_file.name}")
        except SyntaxError as e:
            print(f"  ❌ {py_file.name}: {e}")
            errors.append(str(py_file))

    return len(errors) == 0


def check_imports():
    """Test basic imports without executing code."""
    print(f"\nImport test:")
    project_root = Path(__file__).parent
    src_dir = project_root / "src"

    modules = [
        "config",
        "state",
        "nodes",
        "graph",
        "main",
    ]

    # Add src to path
    sys.path.insert(0, str(src_dir))

    success = []
    failed = []

    for module in modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
            success.append(module)
        except ImportError as e:
            # Some imports may fail due to missing deps, that's ok for this check
            # We just want to ensure our own imports are correct
            if "No module named" in str(e) and any(dep in str(e) for dep in ["pydantic", "langgraph", "openbb"]):
                # Missing dependency, not our fault
                print(f"  ⚠️  {module}: missing dependency ({e})")
                success.append(f"{module} (deps missing)")
            else:
                print(f"  ❌ {module}: {e}")
                failed.append(module)

    # Clean up sys.path
    if str(src_dir) in sys.path:
        sys.path.remove(str(src_dir))

    return len(failed) == 0


def main():
    print("="*60)
    print("DEERFLOW-OPENBB PHASE 1 VALIDATION")
    print("="*60)

    results = {
        "Python version": check_python_version(),
        "Project structure": check_project_structure(),
        "Syntax": check_syntax(),
        "Imports": check_imports(),
    }

    # Dependencies check is informational (may be missing)
    check_dependencies()

    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✅ All validation checks passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e '.[dev]'")
        print("2. Copy .env.template to .env and add API keys")
        print("3. Run: python -m deerflow_openbb --mode mock AAPL")
        print("4. Run tests: pytest tests/ -v")
    else:
        print("❌ Some validation checks failed. Please review above.")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
