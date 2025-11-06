from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

from nedok import DualPaneBrowser, DualPaneBrowserError
from nedok.config import get_last_session, save_session

__version__ = "0.4.4"

# Crash dump file location
CRASH_LOG_FILE = Path.home() / "nedok.crash.txt"


def validate_directory(path: Path, name: str) -> Path:
    """Validate that a directory exists and is accessible.

    Args:
        path: Path to validate
        name: Name of the directory (for error messages, e.g., "left pane")

    Returns:
        The validated path, or current directory if invalid
    """
    try:
        resolved = path.resolve()
        if not resolved.exists():
            print(f"⚠️  Warning: {name} directory does not exist: {path}", file=sys.stderr)
            print(f"   Using current directory instead", file=sys.stderr)
            return Path.cwd()
        if not resolved.is_dir():
            print(f"⚠️  Warning: {name} path is not a directory: {path}", file=sys.stderr)
            print(f"   Using current directory instead", file=sys.stderr)
            return Path.cwd()
        return resolved
    except (OSError, RuntimeError) as e:
        print(f"⚠️  Warning: Cannot access {name} directory: {path}", file=sys.stderr)
        print(f"   Error: {e}", file=sys.stderr)
        print(f"   Using current directory instead", file=sys.stderr)
        return Path.cwd()


def write_crash_log(exception: BaseException) -> None:
    """Write crash information to a log file.

    This is a last-resort handler for uncaught exceptions.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        crash_info = f"""
================================================================================
Nedok Crash Report
================================================================================
Timestamp: {timestamp}
Version: {__version__}
Python: {sys.version}
Platform: {sys.platform}

Exception Type: {type(exception).__name__}
Exception Message: {str(exception)}

Traceback:
{traceback.format_exc()}
================================================================================
"""
        with open(CRASH_LOG_FILE, "a") as f:
            f.write(crash_info)

        print(f"\n❌ Nedok crashed unexpectedly!", file=sys.stderr)
        print(f"   Crash details saved to: {CRASH_LOG_FILE}", file=sys.stderr)
        print(f"   Please report this issue with the crash log.", file=sys.stderr)
    except Exception:
        # If we can't even write the crash log, just print to stderr
        print(f"\n❌ Nedok crashed and could not write crash log!", file=sys.stderr)
        traceback.print_exc()


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
    try:
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

            # Validate session directories exist
            left = validate_directory(left, "left pane (from session)")
            right = validate_directory(right, "right pane (from session)")
        else:
            # Use provided directories (or current if only one provided)
            left = Path(args.left_directory or ".").expanduser()
            right = Path(args.right_directory or ".").expanduser()
            # Don't load SSH sessions when directories explicitly provided

            # Validate provided directories
            left = validate_directory(left, "left pane")
            right = validate_directory(right, "right pane")

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

        # Save final session state (directories + SSH connections) to config
        save_session(str(final_left), str(final_right), final_left_ssh, final_right_ssh)

        print(f"Final left pane directory: {final_left}")
        if final_left_ssh:
            print(f"  (SSH: {final_left_ssh['username']}@{final_left_ssh['hostname']}:{final_left_ssh['remote_directory']})")
        print(f"Final right pane directory: {final_right}")
        if final_right_ssh:
            print(f"  (SSH: {final_right_ssh['username']}@{final_right_ssh['hostname']}:{final_right_ssh['remote_directory']})")
        return 0

    except DualPaneBrowserError as err:
        print(f"Could not start browser: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        # User pressed Ctrl+C - this is a normal exit, don't log as crash
        print("\nInterrupted by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        # Unexpected exception - log it and exit
        write_crash_log(e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
