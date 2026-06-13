"""Pre-commit check: warns about code health issues.

Always exits with code 0 (never blocks the commit).
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
TESTS_DIR = ROOT / "tests"

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
    "styles.py": "test_main_window.py",
    "bulk_create_dialog.py": "test_bulk_create.py",
    "fun_imports.py": "test_sidebar.py",
    "checklist_widget.py": "test_main_window.py",
    "resizable_mixin.py": "test_main_window.py",
    "table_widget.py": "test_main_window.py",
}

FILE_SIZE_THRESHOLD = 500
FUNCTION_LENGTH_THRESHOLD = 80


def find_src_files():
    """Find all .py files in src/ excluding __init__.py and tokens.py."""
    files = []
    for path in SRC_DIR.rglob("*.py"):
        if path.name not in SKIP_FILES:
            files.append(path)
    return files


def check_file_sizes(src_files):
    """Warn if any source file exceeds the size threshold."""
    warnings = []
    for src_file in src_files:
        line_count = len(src_file.read_text(encoding="utf-8").splitlines())
        if line_count > FILE_SIZE_THRESHOLD:
            warnings.append(f"  {src_file.relative_to(ROOT)}: {line_count} lines")
    return warnings


def check_function_lengths(src_files):
    """Warn if any function/method exceeds the length threshold."""
    warnings = []
    for src_file in src_files:
        try:
            tree = ast.parse(
                src_file.read_text(encoding="utf-8"), filename=str(src_file)
            )
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                # Count lines from first statement to last
                if node.body:
                    start = node.body[0].lineno
                    end_lines = []
                    for n in ast.walk(node):
                        end_line = getattr(n, "end_lineno", None)
                        if end_line is not None:
                            end_lines.append(end_line)
                    end = max(end_lines) if end_lines else start
                    length = end - start + 1
                    if length > FUNCTION_LENGTH_THRESHOLD:
                        rel_path = src_file.relative_to(ROOT)
                        warnings.append(
                            f"  {rel_path}:{node.lineno} {node.name}(): {length} lines"
                        )
    return warnings


def check_dead_files(src_files):
    """Warn about empty source files (excluding __init__.py)."""
    warnings = []
    for src_file in src_files:
        line_count = len(src_file.read_text(encoding="utf-8").splitlines())
        if line_count == 0:
            warnings.append(f"  {src_file.relative_to(ROOT)}: 0 lines (may be unused)")
    return warnings


def check_test_coverage(src_files):
    """Warn if source files have no corresponding test file."""
    warnings = []
    for src_file in src_files:
        test_name = SOURCE_TO_TEST.get(src_file.name)
        if test_name:
            test_path = TESTS_DIR / test_name
            if not test_path.exists():
                warnings.append(
                    f"  {src_file.name} -> expected {test_name} but not found"
                )
        else:
            warnings.append(f"  {src_file.name} -> no test mapping defined")
    return warnings


def main():
    src_files = find_src_files()

    print("Code health check")
    print("=" * 40)

    all_warnings = []

    # Check file sizes
    size_warnings = check_file_sizes(src_files)
    if size_warnings:
        print(f"\n[1] Oversized files (>{FILE_SIZE_THRESHOLD} lines):")
        all_warnings.extend(size_warnings)
        for w in size_warnings:
            print(w)
    else:
        print(f"\n[1] File sizes: all under {FILE_SIZE_THRESHOLD} lines")

    # Check function lengths
    func_warnings = check_function_lengths(src_files)
    if func_warnings:
        print(f"\n[2] Long functions (>{FUNCTION_LENGTH_THRESHOLD} lines):")
        all_warnings.extend(func_warnings)
        for w in func_warnings:
            print(w)
    else:
        print(f"\n[2] Function lengths: all under {FUNCTION_LENGTH_THRESHOLD} lines")

    # Check dead files
    dead_warnings = check_dead_files(src_files)
    if dead_warnings:
        print("\n[3] Dead files:")
        all_warnings.extend(dead_warnings)
        for w in dead_warnings:
            print(w)
    else:
        print("\n[3] Dead files: none found")

    # Check test coverage
    test_warnings = check_test_coverage(src_files)
    if test_warnings:
        print("\n[4] Test coverage gaps:")
        all_warnings.extend(test_warnings)
        for w in test_warnings:
            print(w)
    else:
        print("\n[4] Test coverage: all files have tests")

    print()
    if all_warnings:
        print(
            f"Found {len(all_warnings)} warning(s). Run @health for detailed analysis."
        )
    else:
        print("All checks passed.")

    # Always exit 0 — warnings only, never block the commit
    sys.exit(0)


if __name__ == "__main__":
    main()
