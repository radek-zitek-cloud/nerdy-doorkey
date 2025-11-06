from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.dual_pane_browser import DualPaneBrowser, DualPaneBrowserError

__version__ = "0.2.1"


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
        default=None,
        help="Path for the left pane (default: last used or current directory).",
    )
    parser.add_argument(
        "right_directory",
        nargs="?",
        default=None,
        help="Path for the right pane (default: last used or current directory).",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point for the dual-pane browser."""
    args = parse_args()

    if not sys.stdout.isatty():
        print("The dual-pane browser requires an interactive terminal.")
        return 1

    # Load directories from arguments or saved session
    if args.left_directory is None and args.right_directory is None:
        # No directories specified - load from config
        from src.dual_pane_browser.config import get_last_directories
        saved_left, saved_right = get_last_directories()
        left = Path(saved_left).expanduser()
        right = Path(saved_right).expanduser()
    else:
        # Use provided directories (or current if only one provided)
        left = Path(args.left_directory or ".").expanduser()
        right = Path(args.right_directory or ".").expanduser()

    try:
        browser = DualPaneBrowser(left, right)
        final_left, final_right = browser.browse()
    except DualPaneBrowserError as err:
        print(f"Could not start browser: {err}")
        return 1

    # Save final directories to config for next session
    from src.dual_pane_browser.config import save_last_directories
    save_last_directories(str(final_left), str(final_right))

    print(f"Final left pane directory: {final_left}")
    print(f"Final right pane directory: {final_right}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
