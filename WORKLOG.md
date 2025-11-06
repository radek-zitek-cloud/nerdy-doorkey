# Work Log

- 2025-11-06: Performed a full code review of the dual-pane browser, catalogued defects and improvement opportunities in `CODE_REVIEW.md`. Executed `PYTHONPATH=. pytest` to ensure the test suite still passes (initial run without PYTHONPATH failed to locate the package). No further issues encountered.

- 2025-11-06: Fixed all three critical bugs identified in CODE_REVIEW.md:
  1. Remote navigation crash - Added `_PaneState.go_to_parent()` method to handle both local (Path) and remote (str) paths, preventing AttributeError when pressing backspace on SSH panes
  2. Configuration mutation bug - Replaced shallow copy with `copy.deepcopy()` in `config.py` to prevent runtime mutations from polluting DEFAULT_CONFIG
  3. Silent save failures - Added error messages to stderr in `save_config()` to provide user feedback when configuration persistence fails
  All fixes tested with existing test suite (18 tests pass). Committed and pushed to GitHub (commit 4838776). Bumped version to 0.2.1 (commit bcd565e).

- 2025-11-06: Implemented comprehensive SSH security improvements (addressing CODE_REVIEW.md security concerns #4 and #5):
  1. SSH Agent Integration - Added support for key-based authentication via SSH agent, automatically tries agent keys before passwords
  2. Host Key Verification - Implemented `InteractiveHostKeyPolicy` to require user confirmation for unknown hosts, preventing MITM attacks
  3. Security Warnings - Added prominent warnings (⚠️) throughout UI when saving/loading plaintext passwords, encouraging SSH agent usage
  4. Documentation - Enhanced README.md with comprehensive SSH security section, added SSH agent setup example, updated .nedok.toml.example with security best practices
  All tests pass (18/18). Committed and pushed to GitHub (commit ef8881b).

- 2025-11-06: Addressed remaining CODE_REVIEW.md concerns and released v0.3.0:
  1. Command Output Truncation Indicator - Added "... [truncated N lines] ..." marker when command output exceeds buffer (200 lines), applies to both local and remote execution
  2. Enhanced Remote Error Handling - Added comprehensive error handling to `_delete_remote_dir_recursive()`, `_copy_remote_dir_to_local()`, and `_copy_local_dir_to_remote()` with detailed error messages for network failures
  3. Config Mutation Regression Tests - Added tests/test_config.py with 3 tests ensuring DEFAULT_CONFIG isolation and preventing pollution from runtime mutations
  4. Documentation Updates - Updated CODE_REVIEW.md to mark all resolved issues (critical bugs, security concerns, functional gaps, testing, documentation)
  5. Version Bump - Bumped version 0.2.1 → 0.3.0 (MINOR for new features), updated VERSION, main.py, __init__.py, CHANGELOG.md, VERSIONING.md
  All tests pass (21/21). All critical, security, and functional gap issues from CODE_REVIEW.md now resolved. Committed and pushed to GitHub (commit 8050894, tag v0.3.0).

- 2025-11-06: Improved Tab key behavior to toggle between panes:
  Changed Tab key from always switching to right pane to toggling back and forth between left and right panes (using `1 - active_index`). Arrow keys (←/→) and Shift+Tab still provide direct pane selection. Updated README.md and COMMANDS.md documentation. All tests pass (21/21). Committed and pushed to GitHub (commit 181b1a1).
