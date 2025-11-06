from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nedok import DualPaneBrowser, DualPaneBrowserError
from nedok.config import get_last_session, save_session

__version__ = "0.4.3"


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

    # Load directories and SSH sessions from arguments or saved session
    left_ssh = None
    right_ssh = None

    if args.left_directory is None and args.right_directory is None:
        # No directories specified - load from config (including SSH sessions)
        session = get_last_session()
        left = Path(session["left_directory"]).expanduser()
        right = Path(session["right_directory"]).expanduser()
        left_ssh = session.get("left_ssh")
        right_ssh = session.get("right_ssh")
    else:
        # Use provided directories (or current if only one provided)
        left = Path(args.left_directory or ".").expanduser()
        right = Path(args.right_directory or ".").expanduser()
        # Don't load SSH sessions when directories explicitly provided

    try:
        browser = DualPaneBrowser(left, right)

        # Attempt to auto-reconnect SSH sessions if available
        if left_ssh or right_ssh:
            left_connected, right_connected = browser.auto_reconnect_ssh(left_ssh, right_ssh)
            if left_connected:
                print(f"✓ Reconnected left pane to {left_ssh['username']}@{left_ssh['hostname']}")
            if right_connected:
                print(f"✓ Reconnected right pane to {right_ssh['username']}@{right_ssh['hostname']}")
            if left_ssh and not left_connected:
                print(f"⚠  Could not reconnect left pane (using local directory)")
            if right_ssh and not right_connected:
                print(f"⚠  Could not reconnect right pane (using local directory)")

        final_left, final_right, final_left_ssh, final_right_ssh = browser.browse()
    except DualPaneBrowserError as err:
        print(f"Could not start browser: {err}")
        return 1

    # Save final session state (directories + SSH connections) to config
    save_session(str(final_left), str(final_right), final_left_ssh, final_right_ssh)

    print(f"Final left pane directory: {final_left}")
    if final_left_ssh:
        print(f"  (SSH: {final_left_ssh['username']}@{final_left_ssh['hostname']}:{final_left_ssh['remote_directory']})")
    print(f"Final right pane directory: {final_right}")
    if final_right_ssh:
        print(f"  (SSH: {final_right_ssh['username']}@{final_right_ssh['hostname']}:{final_right_ssh['remote_directory']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
