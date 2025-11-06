# Code Review

## ✅ Resolved Critical Issues (v0.2.1)
- **Remote navigation crash** – ✅ FIXED in v0.2.1. Added `_PaneState.go_to_parent()` method that properly handles both Path (local) and str (remote) paths. No more AttributeError crashes when pressing backspace on SSH panes.
- **Configuration state mutation** – ✅ FIXED in v0.2.1. Replaced `DEFAULT_CONFIG.copy()` with `copy.deepcopy(DEFAULT_CONFIG)` in `load_config()` and `_merge_config()`. Runtime mutations no longer pollute module-level defaults. Regression test added (tests/test_config.py).
- **Silent configuration persistence failures** – ✅ FIXED in v0.2.1. `save_config()` now prints warnings to stderr when save fails. Users receive clear feedback instead of silent data loss.

## ✅ Resolved Security Concerns (v0.3.0)
- **Plaintext credential storage** – ✅ ADDRESSED in v0.3.0. Added prominent warnings (⚠️) throughout UI when saving/loading passwords. Integrated SSH agent support for key-based authentication. Users strongly encouraged to use SSH agent instead of passwords. Documentation updated with security best practices.
- **Host key trust-on-first-use without confirmation** – ✅ FIXED in v0.3.0. Replaced `AutoAddPolicy` with `InteractiveHostKeyPolicy` that requires user confirmation for unknown host keys. MITM protection now enabled. Accepted keys stored in `~/.ssh/known_hosts`.

## ✅ Resolved Functional Gaps & Usability (v0.3.0)
- **Remote workflows error handling** – ✅ FIXED in v0.3.0. Added comprehensive error handling to `_delete_remote_dir_recursive()`, `_copy_remote_dir_to_local()`, and `_copy_local_dir_to_remote()`. Network failures now provide detailed error messages with specific operation context.
- **Command execution feedback** – ✅ FIXED in v0.3.0. Added truncation indicator showing exactly how many lines were truncated. Format: "... [truncated N lines] ...". Applies to both local and remote command execution.
- **Limited key-based authentication** – ✅ ENHANCED in v0.3.0. SSH agent integration added with automatic key discovery. Authentication order: Agent keys → ~/.ssh/ keys → Password. Respects Paramiko's key discovery mechanism.

## Maintainability & structure
- **Monolithic input handler** – `_handle_navigation_key()` is approaching 100 lines of sequential conditionals, making it difficult to maintain. Break the handler into smaller intent-specific helpers (navigation, mode toggles, file ops) or dispatch via a mapping to improve readability. (See `src/dual_pane_browser/input_handlers.py`, lines 23-111.)
- **Shared logic belongs in `_PaneState`** – navigation actions manipulate `current_dir`, `cursor_index`, and `scroll_offset` directly from the mixin. Consolidate that state management inside `_PaneState` methods to avoid future desynchronization between local and remote behaviour. (See `src/dual_pane_browser/input_handlers.py`, lines 73-94, and `src/dual_pane_browser/state.py`, lines 126-210.)
- **UI layer hard-codes layout math** – `render_browser()` performs column sizing and layout decisions inline. Consider centralising layout calculations in `render_utils` so the rendering function focuses solely on drawing, which will simplify adapting to alternative terminal sizes.

## Testing & tooling
- **Remote features lack regression coverage** – none of the existing unit tests cover remote SSH flows, so the crash described above or credential persistence bugs slip through undetected. Introduce parametrized tests around `_PaneState._refresh_remote_entries()` and the SSH mixin methods using a fake SFTP client.
- **Config mutation** – ✅ FIXED in v0.3.0. Added comprehensive regression tests (tests/test_config.py) with 3 test cases covering deep copy protection, nested mutation protection, and isolation across loads.

## ✅ Resolved Documentation (v0.3.0)
- **Security caveats documentation** – ✅ FIXED in v0.3.0. Added comprehensive SSH Security section to README.md covering authentication methods, host key verification, credential storage warnings, and SSH agent setup examples. Enhanced .nedok.toml.example with security warnings and best practices.
