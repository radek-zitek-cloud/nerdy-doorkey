from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.dual_pane_browser import DualPaneBrowser, DualPaneBrowserError

__version__ = "0.1.0"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the browser."""
    parser = argparse.ArgumentParser(
        description="Browse two directories side-by-side in the terminal."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version number and exit.",
    )
    parser.add_argument(
        "left_directory",
        nargs="?",
        default=".",
        help="Path for the left pane (default: current directory).",
    )
    parser.add_argument(
        "right_directory",
        nargs="?",
        default=".",
        help="Path for the right pane (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point for the dual-pane browser."""
    args = parse_args()

    if not sys.stdout.isatty():
        print("The dual-pane browser requires an interactive terminal.")
        return 1

    left = Path(args.left_directory).expanduser()
    right = Path(args.right_directory).expanduser()

    try:
        browser = DualPaneBrowser(left, right)
        final_left, final_right = browser.browse()
    except DualPaneBrowserError as err:
        print(f"Could not start browser: {err}")
        return 1

    print(f"Final left pane directory: {final_left}")
    print(f"Final right pane directory: {final_right}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
