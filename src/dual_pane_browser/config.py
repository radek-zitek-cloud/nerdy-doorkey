"""Configuration file management for nerdy-doorkey."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

import tomli_w

# Default configuration file location
CONFIG_FILE = Path.home() / ".nedok.toml"

# Default configuration
DEFAULT_CONFIG = {
    "colors": {
        "file_mode": {
            "directory": "blue_bold",
            "executable": "green_bold",
            "symlink": "cyan",
            "hidden": "gray_dim",
            "readonly": "yellow",
            "regular": "white",
        },
        "git_mode": {
            "untracked": "red_bold",
            "deleted": "red",
            "modified_unstaged": "yellow",
            "staged": "green_bold",
            "renamed": "cyan",
            "clean": "gray_dim",
            "directory": "blue_bold",
        },
    },
    "ssh": {
        "credentials": {},
        # Format: {"hostname": {"username": "user", "password": "encrypted_pass"}}
    },
    "session": {
        "left_directory": ".",
        "right_directory": ".",
    },
}

# Color name to curses color mapping
COLOR_MAP = {
    "blue_bold": ("blue", "bold"),
    "green_bold": ("green", "bold"),
    "cyan": ("cyan", "normal"),
    "gray_dim": ("white", "dim"),
    "yellow": ("yellow", "normal"),
    "white": ("white", "normal"),
    "red_bold": ("red", "bold"),
    "red": ("red", "normal"),
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    if not CONFIG_FILE.exists():
        return copy.deepcopy(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
        # Merge with defaults to ensure all keys exist
        return _merge_config(DEFAULT_CONFIG, config)
    except Exception:
        # If config is corrupted, return defaults
        return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "wb") as f:
            tomli_w.dump(config, f)
    except Exception as err:
        # Don't break the app if config save fails, but inform the user
        print(f"Warning: Failed to save configuration to {CONFIG_FILE}: {err}", file=sys.stderr)


def _merge_config(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user config with defaults, preserving user values."""
    result = copy.deepcopy(default)
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def get_file_mode_colors() -> Dict[str, str]:
    """Get file mode color configuration."""
    config = load_config()
    return config.get("colors", {}).get("file_mode", DEFAULT_CONFIG["colors"]["file_mode"])


def get_git_mode_colors() -> Dict[str, str]:
    """Get git mode color configuration."""
    config = load_config()
    return config.get("colors", {}).get("git_mode", DEFAULT_CONFIG["colors"]["git_mode"])


def get_ssh_credentials(hostname: str) -> Optional[Dict[str, str]]:
    """Get saved SSH credentials for hostname."""
    config = load_config()
    credentials = config.get("ssh", {}).get("credentials", {})
    return credentials.get(hostname)


def save_ssh_credentials(hostname: str, username: str, password: Optional[str] = None) -> None:
    """Save SSH credentials for hostname."""
    config = load_config()
    if "ssh" not in config:
        config["ssh"] = {"credentials": {}}
    if "credentials" not in config["ssh"]:
        config["ssh"]["credentials"] = {}

    config["ssh"]["credentials"][hostname] = {
        "username": username,
    }
    if password:
        # Note: Storing passwords in plaintext is not secure
        # This is a simple implementation - users should use SSH keys in production
        config["ssh"]["credentials"][hostname]["password"] = password

    save_config(config)


def create_default_config() -> None:
    """Create default configuration file if it doesn't exist."""
    if CONFIG_FILE.exists():
        return

    save_config(DEFAULT_CONFIG)


def get_last_directories() -> tuple[str, str]:
    """Get last used directories from session state."""
    config = load_config()
    session = config.get("session", {})
    left = session.get("left_directory", ".")
    right = session.get("right_directory", ".")
    return (left, right)


def save_last_directories(left: str, right: str) -> None:
    """Save last used directories to session state."""
    config = load_config()
    if "session" not in config:
        config["session"] = {}
    config["session"]["left_directory"] = left
    config["session"]["right_directory"] = right
    save_config(config)


__all__ = [
    "CONFIG_FILE",
    "load_config",
    "save_config",
    "get_file_mode_colors",
    "get_git_mode_colors",
    "get_ssh_credentials",
    "save_ssh_credentials",
    "create_default_config",
    "get_last_directories",
    "save_last_directories",
]
