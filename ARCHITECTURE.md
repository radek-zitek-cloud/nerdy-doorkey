# Architecture Documentation

This document describes the technical architecture, design patterns, and development guidelines for the Nerdy Doorkey file browser.

## Project Overview

This is a dual-pane terminal-based file browser built with Python curses. The application provides a side-by-side directory browser with comprehensive file operations and Git integration.

### Features

**File Operations:**
- Navigate directories (arrow keys, j/k, Enter, Backspace, PgUp/PgDn)
- Rename files/directories (n)
- Create new files (f) and directories (F)
- Copy (c), move (t), and delete (d) with confirmation
- View files in pager (v) and edit in $EDITOR (e)
- Execute shell commands in current directory (:)

**SSH/Remote Operations:**
- Connect to remote hosts via SSH (Shift+S)
- Browse remote directories and files
- Execute commands on remote hosts
- View remote files (downloads to temp, opens in $PAGER)
- Edit remote files (downloads to temp, opens in $EDITOR, uploads changes back)
- Copy files/directories: local↔remote, remote↔remote
- Move files/directories: local↔remote, remote↔remote
- Delete remote files and directories (recursive)
- Rename remote files and directories
- Create remote files and directories
- Mixed local/remote browsing (one pane local, one pane remote)

**Git Integration (Git mode):**
- View git status inline (M, A, D, ??, etc.)
- Stage (a) and unstage (u) files
- Restore files to HEAD (r) with confirmation
- View diff in pager with color (g)
- View file history (l) and blame (b) in pager
- Create commits with $EDITOR (o)

**UI Features:**
- Dual-pane layout with independent navigation
- Switch between File, Git, and Owner modes (m)
- Context-sensitive help (h)
- Confirmation dialogs for destructive operations
- Status messages and command output display
- Color-coded file display (mode-specific)
- Configuration file support (~/.nedok.toml)
- Session persistence (save/restore state including SSH connections)

**Color Scheme:**
- File mode: Blue directories (bold), green executables (bold), cyan symlinks, gray hidden files, yellow readonly files
- Git mode: Red untracked files (??), yellow modified unstaged, green staged, red deleted, cyan renamed, dim clean files

## Development Commands

Install dependencies (creates the Poetry-managed virtualenv):
```bash
poetry install
```

Run the application:
```bash
poetry run python -m src.nedok.cli [left_dir] [right_dir]
```

Run tests:
```bash
poetry run python -m pytest -q
```

Run a specific test file:
```bash
poetry run python -m pytest tests/test_<feature>.py -v
```

Add or update dependencies:
```bash
poetry add <package>
poetry add --group dev <package>  # for test/dev deps
```

## Architecture

### Entry Point & Flow
- `src/nedok/cli.py`: CLI entry point that validates terminal availability, parses arguments, instantiates `DualPaneBrowser`, and returns final directory paths
- The application uses Python's `curses.wrapper()` for proper terminal initialization and cleanup

### Core Components

**Architecture:** Mixin-based design for separation of concerns

**`src/nedok/browser.py`** (280 lines) - Core orchestration:
- `DualPaneBrowser`: Main class using three mixins for functionality
- Manages core state: two `_PaneState` instances (left/right), mode, overlays, buffers
- Event loop (`_loop`) dispatches keypresses to handlers in priority order
- Utility methods: `_refresh_panes()`, `_run_external()`, `_dismiss_overlays()`
- Properties: `_active_pane`, `_inactive_pane`
- **Delegates all operations to mixins** (see below)

**`src/nedok/input_handlers.py`** (674 lines) - InputHandlersMixin:
- All keyboard input handling methods:
  - `_handle_confirmation_key`: Y/N confirmation for destructive actions
  - `_handle_ssh_connect_key`: SSH connection dialog input (Tab between fields, Enter to connect)
  - `_handle_host_field_exit`: Detects saved credentials or SSH-agent availability after hostname entry and prompts user to reuse or override them
  - `_handle_rename_key`: Rename input handling
  - `_handle_create_key`: File/directory creation input handling
  - `_handle_mode_selection_key`: Mode prompt overlay (F/G/O to switch between File/Git/Owner modes)
  - `_handle_command_key`: Shell command input (ESC to cancel, Enter to execute)
  - `_handle_navigation_key`: Normal browsing (j/k, Enter, backspace, tab, PgUp/PgDn, Shift+S for SSH)
  - `_handle_mode_command`: Dispatches to file or git operations based on key
- Shell command execution (`_execute_command()`) with output capture, supports both local and remote execution
- SSH connection management (`_start_ssh_connect()`, `_execute_ssh_connect()`)
- Confirmation request system (`_request_confirmation()`)

**`src/nedok/file_operations.py`** (527 lines) - FileOperationsMixin:
- File operation methods supporting both local and remote:
  - `_delete_entry()`: Delete with confirmation (local or remote, recursive for directories)
  - `_copy_entry()`: Universal copy supporting all combinations (local↔local, local↔remote, remote↔local, remote↔remote)
  - `_move_entry()`: Universal move (copy + delete source)
  - `_start_rename()`, `_execute_rename()`: Interactive rename (local or remote)
  - `_create_file()`, `_create_directory()`, `_execute_create()`: Create new items (local or remote)
  - `_view_file()`: View with $PAGER (downloads remote files to temp)
  - `_open_in_editor()`: Edit with $EDITOR (downloads remote, uploads changes back if modified)
- Helper methods for remote operations:
  - `_delete_remote_dir_recursive()`: Recursive remote directory deletion
  - `_copy_local_to_local()`, `_copy_remote_to_local()`, `_copy_local_to_remote()`, `_copy_remote_to_remote()`: Copy routing
  - `_copy_remote_dir_to_local()`, `_copy_local_dir_to_remote()`: Recursive directory copy via SFTP
- Remote-to-remote copies use temp directory as intermediary
- Edit operations detect file changes by comparing mtime before/after editing
- All operations refresh panes to show changes

**`src/nedok/git_operations.py`** (378 lines) - GitOperationsMixin:
- Git operation methods:
  - `_git_stage_entry()`, `_git_unstage_entry()`: Stage/unstage changes
  - `_git_restore_entry()`: Restore to HEAD with confirmation
  - `_git_diff_entry()`: View colored diff in pager
  - `_git_commit()`: Create commit with $EDITOR
  - `_git_log_entry()`: View file history in pager
  - `_git_blame_entry()`: View file blame in pager
- Helper methods:
  - `_git_context()`: Resolve repo root and relative path
  - `_run_git_command()`: Execute git commands with error handling
- All pager operations write to temp files with color support (less -R)
- External commands suspend curses, run synchronously, then refresh

**`src/nedok/state.py`** (404 lines) - Pane state management:
- `_PaneState`: Directory listing, cursor position, scroll offset, entry list, SSH connection
- `_PaneEntry`: File/directory metadata (path, size, mode, timestamp, git status, is_executable, is_symlink, is_readonly, is_remote)
- Entries sorted with directories first, then alphabetically
- `refresh_entries(mode)` rebuilds entry list; handles both local and remote directories
- `_refresh_local_entries(mode)` for local filesystem operations
- `_refresh_remote_entries(mode)` for SSH/SFTP operations
- File attributes (executable, symlink, readonly) detected via stat() for color rendering
- Cursor visibility managed by `ensure_cursor_visible(viewport_height)`
- Remote path support: paths stored as strings for remote, Path objects for local

**`src/nedok/ssh_connection.py`** (325 lines) - SSH connection management:
- `SSHConnection`: Manages SSH client and SFTP session using paramiko
- Methods: `connect()`, `disconnect()`, `list_directory()`, `stat()`, `get_file()`, `put_file()`
- Remote file operations: `remove()`, `rmdir()`, `rename()`, `mkdir()`, `open()`
- Connection state tracking and validation
- Automatic host key policy handling

**`src/nedok/modes.py`** (26 lines) - Browser mode enumeration:
- `BrowserMode.FILE`: Shows standard file permissions in mode column
- `BrowserMode.GIT`: Shows git status codes (M, A, D, ??, etc.) in mode column
- `BrowserMode.OWNER`: Shows file ownership (user:group) in columns
- `ALL_MODES`: List of all available modes for iteration

**`src/nedok/git_status.py`** (68 lines) - Git integration:
- `collect_git_status(directory)`: Returns `(repo_root, {path: status_code})` by running `git status --porcelain=1`
- Handles renames (splits on ` -> ` and takes destination)
- Returns empty dict if not in a git repository

**`src/nedok/colors.py`** (158 lines) - Color management:
- `ColorPair`: IntEnum defining all color pair constants for curses
- `init_colors()`: Initializes curses color pairs (called in event loop setup)
- `get_file_color(entry)`: Returns appropriate color attributes for File mode based on entry type
- `get_git_color(entry)`: Returns appropriate color attributes for Git mode based on git status
- File mode colors: Blue directories, green executables, cyan symlinks, gray hidden files, yellow readonly
- Git mode colors: Red untracked, yellow modified, green staged, red deleted, cyan renamed, dim clean
- Colors combine with curses attributes (e.g., A_BOLD, A_REVERSE for selection)

**`src/nedok/render.py`** (369 lines) - Main curses rendering:
- `render_browser()`: Top-level layout with dynamic sizing
  - Allocates space for: browser panes (top), command console (middle), help hints (bottom 3 lines)
  - Permanent help hints always visible at bottom
- `render_browser_pane()`: Individual pane rendering with columns (Name, Mode/Git/Owner, Size, Modified/User/Group)
  - Displays connection status in pane title (user@host:path for remote)
  - Applies colors from `get_file_color()` or `get_git_color()` based on current mode
  - Combines colors with A_REVERSE attribute for cursor selection
- `render_command_area()`: Delegates to specialized renderers in render_dialogs.py based on browser state
  - Default: Command prompt, status line, and output buffer (last 200 lines)
- `render_help_hints()`: Permanent compact help display at screen bottom (dimmed)
- Cursor visibility managed: shown during command/rename/create/SSH input, hidden otherwise

**`src/nedok/render_dialogs.py`** (283 lines) - Modal dialog rendering:
- `render_confirmation_dialog()`: Y/N confirmation prompt
- `render_ssh_connect_input()`: SSH connection form (Host, User, Password with Tab navigation)
- `render_rename_input()`: Rename input with cursor positioning
- `render_create_input()`: File/directory creation input with cursor positioning
- `render_mode_prompt()`: Mode selection overlay (File/Git/Owner)
- `render_help_panel()`: Comprehensive help text overlay
- All dialogs use frame rendering utilities from render_utils.py

**`src/nedok/render_utils.py`** (138 lines) - Rendering utilities:
- `draw_frame()`, `draw_frame_title()`: Unicode box-drawing characters (┌─┐│└┘)
- `determine_column_widths()`: Dynamic column width calculation based on terminal size
- `truncate_start()`, `truncate_end()`: Text truncation helpers
- Box drawing character constants

**`src/nedok/help_text.py`** (18 lines) - Context-sensitive help hints:
- `build_help_lines(mode)`: Returns compact hints (3 lines) appropriate for current mode
- Terse format: "key action | key action" for quick reference
- Mode-specific operations clearly indicated

**`src/nedok/config.py`** (231 lines) - Configuration file management:
- `load_config()`, `save_config()`: Read/write ~/.nedok.toml configuration file
- `get_file_mode_colors()`, `get_git_mode_colors()`: Color scheme configuration
- `get_ssh_credentials()`, `save_ssh_credentials()`: SSH credential storage (plaintext warning in docs)
- `get_last_session()`, `save_session()`: Session state persistence (directories and SSH connections)
- Default configuration with color schemes and session state
- Uses tomllib (Python 3.11+) or tomli for reading, tomli_w for writing
- Automatic migration and merging of user config with defaults

**`src/nedok/formatting.py`** (28 lines) - Display formatting utilities:
- `format_size()`: Human-readable sizes (B, KB, MB, GB)
- `format_timestamp()`: Timestamp formatting for modified dates

### Key Design Patterns

1. **Mixin Architecture**: Core functionality split across focused mixins:
   - `InputHandlersMixin`: All keyboard input handling (674 lines)
   - `FileOperationsMixin`: All file operations (527 lines)
   - `GitOperationsMixin`: All git operations (378 lines)
   - `DualPaneBrowser`: Core orchestration (280 lines)
   - **Benefits**: Each mixin has single responsibility, easier testing, better maintainability
   - **No API changes**: Mixins compose into single class, existing code works unchanged

2. **State Separation**: Browser state (`_PaneState`) is separate from rendering (`render.py`, `render_dialogs.py`, `render_utils.py`) and controller logic (`browser.py`)

3. **Mode System**: The `BrowserMode` enum switches between three display modes. Modes affect:
   - `FILE`: Shows file permissions, size, and modification time
   - `GIT`: Shows git status, size, and modification time
   - `OWNER`: Shows file permissions, owner username, and group name
   - All file operations and git operations are available in all modes
   - Modes only change what information is displayed, not what commands are available

4. **Modal Input Handling**: The event loop checks multiple input modes in priority order:
   - Confirmation dialogs (highest priority - prevent other actions during confirmation)
   - Rename/create input modes (text input with ESC to cancel)
   - Mode selection overlay
   - Command mode (shell commands)
   - Normal navigation (default)

5. **Confirmation System**: Destructive operations use `_request_confirmation(message, action)`:
   - Stores `(message, callback)` in `pending_action`
   - Renders confirmation dialog
   - Executes callback only on 'y' keypress
   - Prevents accidental data loss

6. **Command Buffer**: Shell commands executed via `:` capture output (last 200 lines) and display in bottom pane

7. **Git Operations**:
   - All git commands resolve repository root first via `_git_context(entry)`
   - Construct relative paths for git commands
   - Diff/log/blame write colored output to temp files and open in $PAGER
   - Operations refresh pane state to show updated git status
   - Commit opens $EDITOR for commit message

8. **External Process Handling**: Editor/pager invocations suspend curses (`curses.endwin()`), run synchronously, then restore terminal state with `_stdscr.refresh()`. Temp files cleaned up in finally blocks.

9. **Constants**: Magic numbers extracted to module-level constants (e.g., `OUTPUT_BUFFER_MAX_LINES`, `PAGE_SCROLL_LINES`) for maintainability

10. **SSH/Remote Operations**:
   - Each pane can independently connect to a remote host via SSH
   - `_PaneState.ssh_connection` holds optional SSHConnection instance
   - `_PaneEntry.is_remote` flag distinguishes local from remote entries
   - Remote paths stored as strings (POSIX), local paths as Path objects
   - Directory listing adapts: uses `iterdir()` for local, SFTP `listdir_attr()` for remote
   - Shell commands execute locally or remotely based on active pane state
   - Mixed mode: left pane can be local while right pane browses remote host
   - SSH connection uses paramiko with password or key-based authentication
   - Connection details entered via modal dialog (Shift+S keybinding)

11. **Universal File Operations (Local/Remote)**:
   - All file operations (copy, move, delete, rename, create, view, edit) work seamlessly across local and remote
   - Copy/move routing: Detects source and destination types, dispatches to appropriate handler
   - Four copy paths: local→local (shutil), local→remote (SFTP put), remote→local (SFTP get), remote→remote (temp download+upload)
   - Remote directory operations are recursive via SFTP list/get/put
   - View/edit: Remote files downloaded to temp, operations performed locally, changes uploaded back (edit only if mtime changed)
   - Delete: Remote directories deleted recursively by listing contents and removing files/subdirs depth-first
   - Temp files: Used for remote view/edit and remote-to-remote copies, cleaned up in finally blocks

12. **Configuration System**: TOML-based configuration file (~/.nedok.toml):
   - Color schemes: Customizable colors for File mode and Git mode
   - SSH credentials: Saved hostname/username/password (plaintext - not recommended for production)
   - Session persistence: Last directories and SSH connections saved on exit
   - Auto-reconnect: SSH sessions restored on startup if credentials/keys available
   - Graceful fallback: Uses defaults if config file missing or corrupted
   - Manual override: Command-line arguments bypass saved session state

13. **Rendering Architecture**: Modular rendering split across three files:
   - `render.py`: Main browser and pane rendering, top-level layout
   - `render_dialogs.py`: All modal dialogs (confirmation, SSH connect, rename, create, mode selection, help)
   - `render_utils.py`: Shared utilities (box drawing, column width calculation, text truncation)
   - **Benefits**: Cleaner separation of concerns, easier to maintain dialog code separately

## Testing Approach

- Tests use `pytest` and live under `tests/`
- Test files mirror source structure: `test_<module>.py`
- Test coverage includes:
  - `test_browser_git_operations.py`: Git operations with temporary repos (uses `tmp_path` fixture)
  - `test_new_features.py`: Confirmation dialogs, rename, file/directory creation
  - `test_help_text.py`: Help text completeness for all three modes
  - `test_config.py`: Configuration file loading, saving, credential management, session persistence
  - `test_formatting.py`, `test_git_status.py`, `test_main.py`: Unit tests for utilities
- Browser tests interact with `DualPaneBrowser` instance directly, manipulating `_PaneState` and calling internal methods
- Confirmation tests simulate user actions by executing pending callbacks
- No UI mocking - tests work with actual `_PaneState` and git subprocess calls
- Git operations that open pager are tested for error cases only (pager display not testable in headless mode)

## Code Style

- PEP 8: 4 spaces, `snake_case` functions/variables, `PascalCase` classes
- Type hints required for new functions
- Docstrings for public functions explaining side effects
- Prefer `from __future__ import annotations` for forward references
- Private methods/classes prefixed with `_`
