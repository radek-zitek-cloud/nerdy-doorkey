"""Tests for configuration management."""

import copy
from nedok.config import DEFAULT_CONFIG, load_config, _merge_config


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
