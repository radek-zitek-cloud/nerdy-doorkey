"""Command-line entry point for Nerdy Doorkey.

This module is intentionally documented in plain language so that someone new to
Python can trace what happens when the program starts.  It provides a small
wrapper around the :class:`nedok.browser.DualPaneBrowser` user interface:

1. Read command line arguments or previously saved session details.
2. Check that the requested directories really exist.
3. Launch the interactive dual-pane browser.
4. Save where the user ended up, or log any crash information.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

from nedok import DualPaneBrowser, DualPaneBrowserError
from nedok.config import get_last_session, save_session

__version__ = "0.5.0"

# Crash dump file location
CRASH_LOG_FILE = Path.home() / "nedok.crash.txt"


def validate_directory(path: Path, name: str) -> Path:
    """Check that a path exists and points to a directory the program can use.

    The browser always needs a real folder to open.  When the user provides a
    bad path (for example, a typo or a file instead of a folder) we keep the
    application running by falling back to the current working directory and
    printing a friendly warning.

    Args:
        path: Candidate path supplied by the user or the saved session.
        name: Human-readable description used in warning messages, e.g.
            ``"left pane"`` or ``"right pane (from session)"``.

    Returns:
        A usable :class:`pathlib.Path`.  The original path is returned when it
        checks out; otherwise ``Path.cwd()`` is used as a safe default.
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
    """Append a detailed crash report to :data:`CRASH_LOG_FILE`.

    This function only runs when something has gone very wrong.  We collect the
    time, Python version, and a full traceback so that a developer can reproduce
    the problem later.
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
        print("   Please report this issue with the crash log.", file=sys.stderr)
    except Exception:
        # If we can't even write the crash log, just print to stderr
        print(f"\n❌ Nedok crashed and could not write crash log!", file=sys.stderr)
        traceback.print_exc()


def parse_args() -> argparse.Namespace:
    """Turn the command-line text (``sys.argv``) into structured information.

    ``argparse`` handles the tedious work of recognising optional switches and
    positional arguments.  We keep the accepted arguments simple so that new
    users can experiment easily: zero, one, or two directory paths plus a
    ``--version`` flag.
    """
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
    """Launch the dual-pane browser and manage session persistence.

    The body of this function is written in distinct stages with extensive
    comments.  The aim is to make it obvious how user input flows into the
    application and how we gracefully handle any problems along the way.
    """
    try:
        # 1) Collect command line choices (if any).
        args = parse_args()

        # The user interface uses the terminal directly.  When stdout is not a
        # terminal (for example, when someone runs ``python cli.py > log.txt``),
        # the curses UI would fail.  We detect that early and exit with a short
        # explanation.
        if not sys.stdout.isatty():
            print("The dual-pane browser requires an interactive terminal.")
            return 1

        # Default to no SSH information; the values will be filled either from
        # the saved session or by the user during the run.
        left_ssh = None
        right_ssh = None

        # 2) Decide which directories to open.
        if args.left_directory is None and args.right_directory is None:
            # No directories were provided, so reuse the last session that was
            # saved when the program exited.  This includes SSH metadata if the
            # previous session was remote.
            session = get_last_session()
            left = Path(session["left_directory"]).expanduser()
            right = Path(session["right_directory"]).expanduser()
            left_ssh = session.get("left_ssh")
            right_ssh = session.get("right_ssh")

            # Guard against the saved directories being deleted or renamed while
            # the application was not running.
            left = validate_directory(left, "left pane (from session)")
            right = validate_directory(right, "right pane (from session)")
        else:
            # The user supplied one or both directories explicitly.  Missing
            # values fall back to the current directory (``"."``).
            left = Path(args.left_directory or ".").expanduser()
            right = Path(args.right_directory or ".").expanduser()
            # When directories are given manually we ignore saved SSH sessions
            # to avoid surprising side-effects.

            # Ensure the paths really exist before launching the UI.
            left = validate_directory(left, "left pane")
            right = validate_directory(right, "right pane")

        # 3) Create the interactive browser and optionally reconnect SSH panes.
        browser = DualPaneBrowser(left, right)

        # Attempt to auto-reconnect SSH sessions if available
        if left_ssh or right_ssh:
            left_connected, right_connected = browser.auto_reconnect_ssh(left_ssh, right_ssh)
            if left_connected:
                print(f"✓ Reconnected left pane to {left_ssh['username']}@{left_ssh['hostname']}")
            if right_connected:
                print(f"✓ Reconnected right pane to {right_ssh['username']}@{right_ssh['hostname']}")
            if left_ssh and not left_connected:
                print("⚠  Could not reconnect left pane (using local directory)")
            if right_ssh and not right_connected:
                print("⚠  Could not reconnect right pane (using local directory)")

        # 4) Launch the curses user interface.  Control returns here when the
        # user quits the program.
        final_left, final_right, final_left_ssh, final_right_ssh = browser.browse()

        # 5) Persist the ending state so the next run can resume effortlessly.
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
