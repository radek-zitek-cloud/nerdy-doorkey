"""Tests for configuration management."""

import copy
import tempfile
from pathlib import Path

from nedok import config
from nedok.config import (
    DEFAULT_CONFIG,
    load_config,
    save_config,
    _merge_config,
    get_ssh_credentials,
    save_ssh_credentials,
    get_last_session,
    save_session,
    get_file_mode_colors,
    get_git_mode_colors,
    get_dialog_colors,
)


def test_default_config_not_mutated():
    """Test that DEFAULT_CONFIG is not mutated by load_config() or _merge_config()."""
    # Take a deep copy of the original default config
    original_default = copy.deepcopy(DEFAULT_CONFIG)

    # Load config (simulates first load with no file)
    config1 = load_config()

    # Mutate the returned config
    config1["ssh"]["credentials"]["test-host"] = {"username": "test", "password": "secret"}
    config1["colors"]["file_mode"]["directory"] = "red"

    # Verify DEFAULT_CONFIG wasn't mutated
    assert DEFAULT_CONFIG == original_default, "DEFAULT_CONFIG was mutated after load_config()"
    assert "test-host" not in DEFAULT_CONFIG["ssh"]["credentials"]
    assert DEFAULT_CONFIG["colors"]["file_mode"]["directory"] == "blue_bold"

    # Load config again to ensure subsequent loads are clean
    config2 = load_config()
    assert "test-host" not in config2["ssh"]["credentials"]
    assert config2["colors"]["file_mode"]["directory"] == "blue_bold"


def test_merge_config_not_mutated():
    """Test that _merge_config doesn't mutate the default config."""
    # Take a deep copy of the original default config
    original_default = copy.deepcopy(DEFAULT_CONFIG)

    # Create user config with some overrides
    user_config = {
        "ssh": {
            "credentials": {
                "example.com": {"username": "user"}
            }
        }
    }

    # Merge configs
    merged = _merge_config(DEFAULT_CONFIG, user_config)

    # Mutate the merged config
    merged["ssh"]["credentials"]["another-host"] = {"username": "another"}

    # Verify DEFAULT_CONFIG wasn't mutated
    assert DEFAULT_CONFIG == original_default, "DEFAULT_CONFIG was mutated after _merge_config()"
    assert "example.com" not in DEFAULT_CONFIG["ssh"]["credentials"]
    assert "another-host" not in DEFAULT_CONFIG["ssh"]["credentials"]


def test_nested_mutation_protection():
    """Test that nested dictionaries are protected from mutation."""
    # Take a deep copy of the original default config
    original_default = copy.deepcopy(DEFAULT_CONFIG)

    # Load config
    config = load_config()

    # Deep mutation - modify nested dict
    config["colors"]["file_mode"]["new_type"] = "purple"
    config["colors"]["git_mode"]["new_status"] = "orange"

    # Verify DEFAULT_CONFIG wasn't mutated at any level
    assert DEFAULT_CONFIG == original_default
    assert "new_type" not in DEFAULT_CONFIG["colors"]["file_mode"]
    assert "new_status" not in DEFAULT_CONFIG["colors"]["git_mode"]

    # Load again to ensure clean state
    config2 = load_config()
    assert "new_type" not in config2["colors"]["file_mode"]
    assert "new_status" not in config2["colors"]["git_mode"]


def test_ssh_credentials_save_and_load(tmp_path):
    """Test saving and loading SSH credentials."""
    # Temporarily override config file location
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "test_config.toml"

        # Save credentials
        save_ssh_credentials("server.example.com", "testuser", "testpass")

        # Load credentials
        creds = get_ssh_credentials("server.example.com")
        assert creds is not None
        assert creds["username"] == "testuser"
        assert creds["password"] == "testpass"

        # Non-existent host returns None
        assert get_ssh_credentials("nonexistent.host") is None

    finally:
        config.CONFIG_FILE = original_config_file


def test_ssh_credentials_without_password(tmp_path):
    """Test saving SSH credentials without password."""
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "test_config.toml"

        # Save without password
        save_ssh_credentials("server.example.com", "testuser")

        creds = get_ssh_credentials("server.example.com")
        assert creds is not None
        assert creds["username"] == "testuser"
        assert "password" not in creds

    finally:
        config.CONFIG_FILE = original_config_file


def test_session_save_and_load(tmp_path):
    """Test saving and loading session state."""
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "test_config.toml"

        # Save session with SSH connections
        left_ssh = {
            "hostname": "server1.com",
            "username": "user1",
            "remote_directory": "/home/user1"
        }
        right_ssh = {
            "hostname": "server2.com",
            "username": "user2",
            "remote_directory": "/var/www"
        }

        save_session("/tmp/left", "/tmp/right", left_ssh, right_ssh)

        # Load session
        session = get_last_session()
        assert session["left_directory"] == "/tmp/left"
        assert session["right_directory"] == "/tmp/right"
        assert session["left_ssh"]["hostname"] == "server1.com"
        assert session["left_ssh"]["username"] == "user1"
        assert session["right_ssh"]["hostname"] == "server2.com"

    finally:
        config.CONFIG_FILE = original_config_file


def test_session_save_without_ssh(tmp_path):
    """Test saving session without SSH connections."""
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "test_config.toml"

        # Save session without SSH
        save_session("/home/user", "/tmp")

        session = get_last_session()
        assert session["left_directory"] == "/home/user"
        assert session["right_directory"] == "/tmp"
        assert session["left_ssh"] is None
        assert session["right_ssh"] is None

    finally:
        config.CONFIG_FILE = original_config_file


def test_session_clears_ssh_on_none(tmp_path):
    """Test that passing None for SSH clears saved SSH state."""
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "test_config.toml"

        # First save with SSH
        left_ssh = {"hostname": "server.com", "username": "user", "remote_directory": "/home"}
        save_session("/tmp", "/tmp", left_ssh=left_ssh)

        # Verify it was saved
        session = get_last_session()
        assert session["left_ssh"] is not None

        # Now save without SSH (None)
        save_session("/tmp", "/tmp", left_ssh=None)

        # Verify it was cleared
        session = get_last_session()
        assert session["left_ssh"] is None

    finally:
        config.CONFIG_FILE = original_config_file


def test_color_mode_getters():
    """Test color configuration getters."""
    file_colors = get_file_mode_colors()
    assert "directory" in file_colors
    assert file_colors["directory"] == "blue_bold"

    git_colors = get_git_mode_colors()
    assert "untracked" in git_colors
    assert git_colors["untracked"] == "red_bold"

    dialog_colors = get_dialog_colors()
    assert "foreground" in dialog_colors
    assert "background" in dialog_colors


def test_save_and_load_config(tmp_path):
    """Test saving and loading configuration file."""
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "test_config.toml"

        # Create custom config
        custom_config = copy.deepcopy(DEFAULT_CONFIG)
        custom_config["colors"]["file_mode"]["directory"] = "red_bold"
        custom_config["session"]["left_directory"] = "/custom/path"

        # Save it
        save_config(custom_config)

        # Verify file exists
        assert config.CONFIG_FILE.exists()

        # Load it back
        loaded = load_config()
        assert loaded["colors"]["file_mode"]["directory"] == "red_bold"
        assert loaded["session"]["left_directory"] == "/custom/path"

        # Verify defaults are still present
        assert "git_mode" in loaded["colors"]

    finally:
        config.CONFIG_FILE = original_config_file


def test_merge_config_preserves_user_values():
    """Test that merge preserves user-specified values."""
    default = {
        "a": 1,
        "b": {"c": 2, "d": 3},
        "e": 4
    }

    user = {
        "b": {"c": 99},
        "f": 5
    }

    merged = _merge_config(default, user)

    # User value should override
    assert merged["b"]["c"] == 99
    # Default value should be preserved
    assert merged["b"]["d"] == 3
    # Default top-level should be preserved
    assert merged["a"] == 1
    assert merged["e"] == 4
    # User addition should be included
    assert merged["f"] == 5


def test_config_file_creation_failure_doesnt_crash():
    """Test that config save failure doesn't crash the application."""
    original_config_file = config.CONFIG_FILE
    try:
        # Point to an invalid location (directory instead of file)
        config.CONFIG_FILE = Path("/dev/null/invalid/path.toml")

        # This should not raise an exception
        save_config(DEFAULT_CONFIG)

    finally:
        config.CONFIG_FILE = original_config_file


def test_corrupted_config_file_returns_defaults(tmp_path):
    """Test that corrupted config file returns defaults."""
    original_config_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = tmp_path / "corrupted.toml"

        # Write invalid TOML
        config.CONFIG_FILE.write_text("this is not valid TOML {{{")

        # Should return defaults instead of crashing
        loaded = load_config()
        assert loaded == DEFAULT_CONFIG

    finally:
        config.CONFIG_FILE = original_config_file
