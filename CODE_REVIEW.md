# Code Review

## Critical issues
- **Remote navigation crash** – `_handle_navigation_key` blindly calls `.parent` on `pane.current_dir`, which is a `Path` for local panes but plain `str` for remote panes. When browsing an SSH pane, pressing backspace raises an `AttributeError` and tears down the UI. Guard the branch by delegating to `_PaneState` helpers that understand remote paths instead of assuming a `Path` instance. (See `src/dual_pane_browser/input_handlers.py`, lines 85-94.)
- **Configuration state is mutable across runs** – `load_config()` and `_merge_config()` both rely on `DEFAULT_CONFIG.copy()`, which is only a shallow copy. Any nested dictionary that gets mutated at runtime (for example when saving SSH credentials) will modify the module-level default, so later runs inherit polluted defaults. Replace the shallow copy with a deep copy (e.g., `copy.deepcopy`) before merging user data. (See `src/dual_pane_browser/config.py`, lines 18-96.)
- **Silent configuration persistence failures** – `save_config()` swallows all exceptions and ignores the error. When the config directory is not writable, users receive no feedback and their session paths or credentials are silently lost. Emit at least a log/status message so the UI can surface the failure. (See `src/dual_pane_browser/config.py`, lines 77-85.)

## Security concerns
- **Plaintext credential storage** – `save_ssh_credentials()` writes usernames and passwords directly to `~/.nedok.toml`, and `_execute_ssh_connect()` will happily cache them after each connection prompt. At minimum, warn prominently in the UI, and preferably encrypt or integrate with an SSH agent/keyring before persisting secrets. (See `src/dual_pane_browser/config.py`, lines 118-134 and `src/dual_pane_browser/input_handlers.py`, lines 345-382.)
- **Host key trust-on-first-use without confirmation** – `SSHConnection.connect()` installs `AutoAddPolicy`, so every new host key is accepted silently and cached. That makes the client vulnerable to man-in-the-middle attacks. Prompt the user before trusting unknown hosts or require keys to be present in `known_hosts`. (See `src/dual_pane_browser/ssh_connection.py`, lines 30-56.)

## Functional gaps & usability
- **Remote workflows lack parity with local actions** – destructive operations such as remote deletes and recursive copies do not have error handling around the directory listings; a single network hiccup bubbles up as an uncaught exception. Harden `_delete_remote_dir_recursive()` and friends with transport-aware retries and failure messaging.
- **Command execution feedback** – `_execute_command()` truncates output to 200 lines but never indicates truncation. Consider displaying a “truncated” marker so users know they need to pipe to a pager.
- **Limited key-based authentication** – the SSH workflow only supports password or a single key file via `_execute_ssh_connect()`, and the UI never surfaces how to provide a key path. Extend the prompt so users can choose a key or respect `~/.ssh/config` defaults via Paramiko.

## Maintainability & structure
- **Monolithic input handler** – `_handle_navigation_key()` is approaching 100 lines of sequential conditionals, making it difficult to maintain. Break the handler into smaller intent-specific helpers (navigation, mode toggles, file ops) or dispatch via a mapping to improve readability. (See `src/dual_pane_browser/input_handlers.py`, lines 23-111.)
- **Shared logic belongs in `_PaneState`** – navigation actions manipulate `current_dir`, `cursor_index`, and `scroll_offset` directly from the mixin. Consolidate that state management inside `_PaneState` methods to avoid future desynchronization between local and remote behaviour. (See `src/dual_pane_browser/input_handlers.py`, lines 73-94, and `src/dual_pane_browser/state.py`, lines 126-210.)
- **UI layer hard-codes layout math** – `render_browser()` performs column sizing and layout decisions inline. Consider centralising layout calculations in `render_utils` so the rendering function focuses solely on drawing, which will simplify adapting to alternative terminal sizes.

## Testing & tooling
- **Remote features lack regression coverage** – none of the existing unit tests cover remote SSH flows, so the crash described above or credential persistence bugs slip through undetected. Introduce parametrized tests around `_PaneState._refresh_remote_entries()` and the SSH mixin methods using a fake SFTP client.
- **Config mutation is untested** – add a regression test that saves credentials and then reloads defaults in a fresh process to ensure the defaults remain pristine once the deep-copy fix lands.

## Documentation
- Document the security caveats (plaintext credentials, host-key policy) in the README until the implementation is hardened.
