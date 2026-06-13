"""Pre-commit check: warns if documentation may be out of sync with source code.

Always exits with code 0 (never blocks the commit).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
TESTS_DIR = ROOT / "tests"
DOC_FILES = ["instructions", "project_plan.md"]

SKIP_FILES = {"__init__.py", "tokens.py"}

# Map source filenames to their expected test file basenames
SOURCE_TO_TEST = {
    "database.py": "test_database.py",
    "settings.py": "test_settings.py",
    "undo_manager.py": "test_undo_manager.py",
    "page.py": "test_models.py",
    "page_object.py": "test_page_object_repo.py",
    "page_repo.py": "test_page_repo.py",
    "page_object_repo.py": "test_page_object_repo.py",
    "sidebar.py": "test_sidebar.py",
    "main_window.py": "test_main_window.py",
    "editor.py": "test_main_window.py",
    "checkbox_widget.py": "test_sidebar.py",
    "dialogs.py": "test_main_window.py",
    "main.py": "test_main_window.py",
}


def find_src_files():
    """Find all .py files in src/ excluding __init__.py and tokens.py."""
    files = []
    for path in SRC_DIR.rglob("*.py"):
        if path.name not in SKIP_FILES:
            files.append(path)
    return files


def check_test_coverage(src_files):
    """Check if each meaningful source file has a corresponding test file."""
    warnings = []
    tested = set()

    for src_file in src_files:
        test_name = SOURCE_TO_TEST.get(src_file.name)
        if test_name:
            test_path = TESTS_DIR / test_name
            if test_path.exists():
                tested.add(src_file.name)
            else:
                warnings.append(
                    f"  {src_file.name} -> expected {test_name} but not found"
                )
        else:
            warnings.append(
                f"  {src_file.name} -> no test mapping defined (add to SOURCE_TO_TEST)"
            )

    return warnings


def check_doc_freshness():
    """Warn if source files are newer than documentation files."""
    warnings = []

    src_mtime = 0
    for py_file in SRC_DIR.rglob("*.py"):
        src_mtime = max(src_mtime, py_file.stat().st_mtime)

    for doc_name in DOC_FILES:
        doc_path = ROOT / doc_name
        if not doc_path.exists():
            warnings.append(f"  {doc_name} does not exist")
            continue
        doc_mtime = doc_path.stat().st_mtime
        if src_mtime > doc_mtime:
            warnings.append(f"  {doc_name} may be outdated (source files are newer)")

    return warnings


def main():
    src_files = find_src_files()

    print("Documentation sync check")
    print("=" * 40)

    all_warnings = []

    # Check test coverage
    test_warnings = check_test_coverage(src_files)
    if test_warnings:
        print("\n[1] Test coverage gaps:")
        all_warnings.extend(test_warnings)
        for w in test_warnings:
            print(w)
    else:
        print("\n[1] Test coverage: all source files have tests")

    # Check doc freshness
    doc_warnings = check_doc_freshness()
    if doc_warnings:
        print("\n[2] Documentation freshness:")
        all_warnings.extend(doc_warnings)
        for w in doc_warnings:
            print(w)
    else:
        print("\n[2] Documentation freshness: up to date")

    print()
    if all_warnings:
        print(f"Found {len(all_warnings)} warning(s). Documentation agent recommended.")
        print("Run: @docs sync documentation with current implementation")
    else:
        print("All checks passed.")

    # Always exit 0 — warnings only, never block the commit
    sys.exit(0)


if __name__ == "__main__":
    main()
