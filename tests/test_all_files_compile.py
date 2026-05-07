import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _python_files():
    targets = [ROOT / "my_toolbox", ROOT / "finance_toolbox"]
    for target in targets:
        for file_path in sorted(target.glob("*.py")):
            if file_path.name == "__pycache__":
                continue
            yield file_path


def test_all_toolbox_python_files_compile():
    for file_path in _python_files():
        py_compile.compile(str(file_path), doraise=True)
