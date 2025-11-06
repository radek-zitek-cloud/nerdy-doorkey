import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_main_requires_interactive_terminal():
    result = subprocess.run(
        [sys.executable, "-m", "src.nedok.cli"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "requires an interactive terminal" in result.stdout
    assert result.stderr == ""
