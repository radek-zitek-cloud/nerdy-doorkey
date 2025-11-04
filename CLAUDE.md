# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**Git Integration (Git mode):**
- View git status inline (M, A, D, ??, etc.)
- Stage (a) and unstage (u) files
- Restore files to HEAD (r) with confirmation
- View diff in pager with color (g)
- View file history (l) and blame (b) in pager
- Create commits with $EDITOR (o)

**UI Features:**
- Dual-pane layout with independent navigation
- Switch between File mode and Git mode (m)
- Context-sensitive help (h)
- Confirmation dialogs for destructive operations
- Status messages and command output display

## Development Commands

Activate the virtual environment first:
```bash
source .venv/bin/activate
```

Run the application:
```bash
python main.py [left_dir] [right_dir]
```

Run tests:
```bash
python -m pytest -q
```

Run a specific test file:
```bash
python -m pytest tests/test_<feature>.py -v
```

Install/update dependencies:
```bash
python -m pip install -r requirements.txt
```

## Architecture

### Entry Point & Flow
- `main.py`: CLI entry point that validates terminal availability, parses arguments, instantiates `DualPaneBrowser`, and returns final directory paths
- The application uses Python's `curses.wrapper()` for proper terminal initialization and cleanup

### Core Components

**Architecture:** Mixin-based design for separation of concerns

**`src/dual_pane_browser/browser.py`** (141 lines) - Core orchestration:
- `DualPaneBrowser`: Main class using three mixins for functionality
- Manages core state: two `_PaneState` instances (left/right), mode, overlays, buffers
- Event loop (`_loop`) dispatches keypresses to handlers in priority order
- Utility methods: `_refresh_panes()`, `_run_external()`, `_dismiss_overlays()`
- Properties: `_active_pane`, `_inactive_pane`
- **Delegates all operations to mixins** (see below)

**`src/dual_pane_browser/input_handlers.py`** (300 lines) - InputHandlersMixin:
- All keyboard input handling methods:
  - `_handle_confirmation_key`: Y/N confirmation for destructive actions
  - `_handle_rename_key`: Rename input handling
  - `_handle_create_key`: File/directory creation input handling
  - `_handle_mode_selection_key`: Mode prompt overlay (F/G to switch)
  - `_handle_command_key`: Shell command input (ESC to cancel, Enter to execute)
  - `_handle_navigation_key`: Normal browsing (j/k, Enter, backspace, tab, PgUp/PgDn)
  - `_handle_mode_command`: Dispatches to file or git operations based on key
- Shell command execution (`_execute_command()`) with output capture
- Confirmation request system (`_request_confirmation()`)

**`src/dual_pane_browser/file_operations.py`** (168 lines) - FileOperationsMixin:
- File operation methods:
  - `_delete_entry()`: Delete with confirmation
  - `_copy_entry()`, `_move_entry()`: Copy/move to other pane
  - `_start_rename()`, `_execute_rename()`: Interactive rename
  - `_create_file()`, `_create_directory()`, `_execute_create()`: Create new items
  - `_view_file()`, `_open_in_editor()`: View/edit with $PAGER/$EDITOR
- Uses `shutil` for copy/move/delete, `Path.rename()` for rename, `Path.touch()/mkdir()` for creation
- All operations refresh panes to show changes

**`src/dual_pane_browser/git_operations.py`** (378 lines) - GitOperationsMixin:
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

**`src/dual_pane_browser/state.py`** - Pane state management:
- `_PaneState`: Directory listing, cursor position, scroll offset, entry list
- `_PaneEntry`: File/directory metadata (path, size, mode, timestamp, git status)
- Entries sorted with directories first, then alphabetically
- `refresh_entries(mode)` rebuilds entry list; attaches git status when `mode == BrowserMode.GIT`
- Cursor visibility managed by `ensure_cursor_visible(viewport_height)`

**`src/dual_pane_browser/modes.py`** - Browser mode enumeration:
- `BrowserMode.FILE`: Shows standard file permissions in mode column
- `BrowserMode.GIT`: Shows git status codes (M, A, D, ??, etc.) in mode column instead

**`src/dual_pane_browser/git_status.py`** - Git integration:
- `collect_git_status(directory)`: Returns `(repo_root, {path: status_code})` by running `git status --porcelain=1`
- Handles renames (splits on ` -> ` and takes destination)
- Returns empty dict if not in a git repository

**`src/dual_pane_browser/render.py`** - All curses rendering:
- `render_browser()`: Top-level layout with dynamic sizing (splits terminal into top 2/3 browser panes, bottom 1/3 command/output)
- `render_browser_pane()`: Individual pane rendering with columns (Name, Mode/Git, Size, Modified)
- `render_command_area()`: Delegates to specialized renderers based on browser state:
  - `render_confirmation_dialog()`: Y/N confirmation prompt
  - `render_rename_input()`: Rename input with cursor positioning
  - `render_create_input()`: File/directory creation input with cursor positioning
  - `render_mode_prompt()`: Mode selection overlay
  - `render_help_panel()`: Comprehensive help text overlay
  - Default: Command prompt, status line, and output buffer (last 200 lines)
- Uses Unicode box-drawing characters (┌─┐│└┘)
- Dynamic column width calculation based on terminal size
- Cursor visibility managed: shown during command/rename/create input, hidden otherwise

**`src/dual_pane_browser/help_text.py`** - Context-sensitive help hints:
- `build_help_lines(mode)`: Returns compact hints (3 lines) appropriate for current mode
- Terse format: "key action | key action" for quick reference
- Mode-specific operations clearly indicated

**`src/dual_pane_browser/formatting.py`** - Display formatting utilities:
- `format_size()`: Human-readable sizes (B, KB, MB, GB)
- `format_timestamp()`: Timestamp formatting for modified dates

### Key Design Patterns

1. **Mixin Architecture**: Core functionality split across focused mixins:
   - `InputHandlersMixin`: All keyboard input handling (300 lines)
   - `FileOperationsMixin`: All file operations (168 lines)
   - `GitOperationsMixin`: All git operations (378 lines)
   - `DualPaneBrowser`: Core orchestration (141 lines)
   - **Benefits**: Each mixin has single responsibility, easier testing, better maintainability
   - **No API changes**: Mixins compose into single class, existing code works unchanged

2. **State Separation**: Browser state (`_PaneState`) is separate from rendering (`render.py`) and controller logic (`browser.py`)

3. **Mode System**: The `BrowserMode` enum switches between file browsing and git operations. Modes affect:
   - Column headers ("Mode" vs "Git")
   - Entry metadata (file permissions vs git status)
   - Available key commands (file ops vs git ops)

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

## Testing Approach

- Tests use `pytest` and live under `tests/`
- Test files mirror source structure: `test_<module>.py`
- Test coverage includes:
  - `test_browser_git_operations.py`: Git operations with temporary repos (uses `tmp_path` fixture)
  - `test_new_features.py`: Confirmation dialogs, rename, file/directory creation
  - `test_help_text.py`: Help text completeness for both modes
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
