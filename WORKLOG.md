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
