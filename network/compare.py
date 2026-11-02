
from pathlib import Path
import difflib


def compare_backups(file_old, file_new):
    old_path = Path(file_old)
    new_path = Path(file_new)

    old_lines = old_path.read_text(
        encoding="utf-8"
    ).splitlines()

    new_lines = new_path.read_text(
        encoding="utf-8"
    ).splitlines()

    differences = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_path.name,
            tofile=new_path.name,
            lineterm=""
        )
    )


    added_count = sum(
        1 for line in differences
        if line.startswith("+") and not line.startswith("+++")
    )

    removed_count = sum(
        1 for line in differences
        if line.startswith("-") and not line.startswith("---")
    )

    return {
        "identical": old_lines == new_lines,
        "differences": differences,
        "added_count": added_count,
        "removed_count": removed_count,
        "total_changes": added_count + removed_count
    }
