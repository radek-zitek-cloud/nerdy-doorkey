# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.4] - 2025-11-06

### Fixed
- **Workflow permissions** – Added `permissions: contents: write` to GitHub Actions workflow
  - Fixes 403 error when creating releases
  - Required for softprops/action-gh-release action to work
  - Binaries now properly attached to GitHub releases

## [0.4.3] - 2025-11-06

### Fixed
- **Missing spec file** – Added nedok.spec to git repository (was previously ignored)
  - Spec file is required for GitHub Actions workflow builds
  - Contains pathex=['src'] for proper module discovery
  - Fixes "Spec file not found" error in CI/CD pipeline

### Changed
- Updated .gitignore to allow nedok.spec tracking while still ignoring temporary spec files

## [0.4.2] - 2025-11-06

### Fixed
- **GitHub Actions workflow** – Fixed PyInstaller build process to use nedok.spec file
  - Ensures pathex=['src'] is properly used for absolute imports
  - Builds now use `pyinstaller --clean nedok.spec` instead of command-line args
  - Fixes binary build failures that would occur with absolute imports
- **Build script** – Fixed typos and updated to use spec file consistently
  - Fixed "Buildingnedok" → "Building nedok"
  - Fixed "dis/tnedok" → "dist/nedok"
  - Updated to use nedok.spec file for reliable builds

### Technical
- Binary builds now correctly handle nedok.* absolute imports
- Workflow trigger verified: runs on any v* tag push
- Manual testing available via workflow_dispatch

## [0.4.1] - 2025-11-06

### Changed
- **Absolute imports** – Converted all relative imports (`.something`) to absolute imports (`nedok.something`)
  - Updated 8 source files in src/nedok/
  - Updated 6 test files in tests/
  - Improves code clarity and follows modern Python packaging best practices
  - Better compatibility with various Python tooling and IDEs

### Technical
- Python version constraint updated to >=3.8,<3.15 in pyproject.toml
- Added pyinstaller to dev dependencies for binary distribution support

## [0.4.0] - 2025-11-06

### Changed
- **Poetry build system** – Migrated from pip/requirements.txt to Poetry for modern dependency and build management
  - Added pyproject.toml with Poetry configuration
  - Dependencies managed via Poetry (paramiko, tomli, tomli-w)
  - Dev dependencies (pytest) in separate group
  - Build backend: poetry-core>=1.8.0
- **Package structure** – Formalized src-layout package structure for Poetry build
  - Package configuration: `packages = [{ include = "nedok", from = "src" }]`
  - Maintains existing CLI entry point: `python -m src.nedok.cli`

### Technical
- Modern Python packaging with Poetry
- Cleaner dependency management
- Reproducible builds with poetry.lock (when generated)
- Preparation for future PyPI distribution

## [0.3.1] - 2025-11-07

### Changed
- **Package rename** – Runtime module renamed from `dual_pane_browser` to `nedok` to better reflect the project identity. Update your imports to `from src.nedok ...`.
- **SSH credential workflow** – When leaving the host field the browser now discovers saved credentials or SSH-agent access, informs the user, and offers to reuse them or override with new details.
- **Documentation refresh** – README, CLAUDE, CODE_REVIEW, and tests updated to reference the `nedok` package and explain the credential autodetect prompt.

### Fixed
- **Version bump** – Incremented to 0.3.1 to capture the package rename and SSH UX improvements.

## [0.3.0] - 2025-11-06

### Added

#### SSH Security Features
- **SSH Agent Integration** - Automatic support for SSH agent key-based authentication
  - Authentication priority: Agent keys → Key files → Password
  - Reduces reliance on password storage for better security
- **Host Key Verification** - Interactive confirmation for unknown SSH host keys
  - New `InteractiveHostKeyPolicy` class for MITM attack prevention
  - Users must explicitly approve new host keys
  - Accepted keys stored in `~/.ssh/known_hosts`
- **Security Warnings** - Prominent warnings (⚠️) throughout UI
  - Warning emoji displayed when saving/loading plaintext passwords
  - Status messages encourage SSH agent usage
  - Connection prompts explain authentication order

#### Usability Improvements
- **Command Output Truncation Indicator** - Shows how many lines were truncated
  - Format: "... [truncated N lines] ..."
  - Applies to both local and remote command execution
  - Users now know when output is incomplete

#### Testing & Reliability
- **Config Mutation Regression Tests** - Prevents DEFAULT_CONFIG pollution
  - Three comprehensive tests for deep copy protection
  - Ensures configuration isolation across runs
- **Enhanced Remote Error Handling** - Better error messages for network failures
  - Added detailed error messages for remote delete operations
  - Improved error handling for remote copy operations (remote→local, local→remote)
  - Network hiccups now provide clear feedback

### Changed
- **Documentation** - Comprehensive SSH security section in README.md
  - Added authentication methods explanation
  - Added host key verification documentation
  - Added SSH agent setup example
  - Enhanced `.nedok.toml.example` with security best practices

All improvements address concerns identified in CODE_REVIEW.md (critical bugs, security issues, and functional gaps).

## [0.2.1] - 2025-11-06

### Fixed

#### Critical Bug Fixes
- **Remote navigation crash** - Fixed AttributeError when pressing backspace on SSH panes
  - Added `_PaneState.go_to_parent()` method to handle both local (Path) and remote (str) paths
  - Remote paths now use `PurePosixPath` for parent directory navigation
  - Modified `input_handlers.py` to use new method instead of direct `.parent` access
- **Configuration mutation bug** - Fixed runtime mutations polluting DEFAULT_CONFIG
  - Replaced shallow copy (`dict.copy()`) with deep copy (`copy.deepcopy()`)
  - SSH credentials and other config changes no longer corrupt module-level defaults
  - Fixed in `load_config()` and `_merge_config()` functions
- **Silent save failures** - Added error feedback when configuration save fails
  - Configuration save failures now print warnings to stderr
  - Users receive feedback instead of silent data loss
  - Preserves non-breaking behavior while informing users of issues

All fixes identified in CODE_REVIEW.md and verified with existing test suite.

## [0.2.0] - 2025-01-05

### Added

#### Configuration System
- **TOML configuration file** support (`~/.nedok.toml`)
- Color customization for File and Git modes
- Define custom colors for file types and git statuses
- Example configuration file (`.nedok.toml.example`)
- Framework for future configuration expansion

#### SSH Credential Management
- **Auto-save credentials** after successful SSH connection
- **Auto-load credentials** when entering known hostname
- Confirmation prompt to save credentials (y/n)
- Credentials stored in `~/.nedok.toml` under `[ssh.credentials]`
- Security warnings about plaintext password storage
- Pre-populate username and password fields for saved hosts

#### Session Persistence
- **Auto-save directories** on exit to configuration file
- **Auto-restore directories** when launching without arguments
- Session state stored in `~/.nedok.toml` under `[session]`
- Manual override by specifying directories as arguments
- Seamless workflow: exit and restart to continue where you left off

#### External Command Improvements
- **Keypress wait** after external commands (pager, editor)
- Display "Press any key to continue..." prompt
- Prevents terminal content from being immediately overwritten
- Applies to view (`v`), edit (`e`), and git operations (`g`, `l`, `b`)
- Raw terminal input capture for single keypress

#### Dependencies
- Added `tomli` for TOML parsing (Python 3.11+ uses built-in `tomllib`)
- Added `tomli-w` for TOML writing

### Changed
- Modified argument parsing to allow optional directories (default: load from config)
- Enhanced `_run_external()` to include keypress wait
- Updated help text for command-line arguments
- Updated `.gitignore` to exclude `.nedok.toml` (contains credentials)

### Documentation
- Updated README.md with Configuration File section
- Added Session Management documentation with examples
- Updated COMMANDS.md with SSH credential workflow
- Documented auto-save/auto-load behavior
- Added security warnings for plaintext password storage
- Updated `.nedok.toml.example` with all sections

### Technical
- New `config.py` module for configuration management
- Config merging strategy (user config + defaults)
- Graceful fallback if config file missing or corrupted
- Session state tracking in browser instance
- Terminal raw mode handling with `tty`/`termios`

## [0.1.0] - 2025-01-05

### 🎉 Initial Release

First working release of Nerdy Doorkey - a powerful dual-pane terminal file browser.

### Added

#### Core Features
- **Dual-pane file browser** with independent navigation
- **Three display modes**:
  - File mode: Shows file size and modification time
  - Git mode: Shows git status inline
  - Owner mode: Shows user:group file ownership
- **SSH/Remote support**: Connect to remote hosts and browse remote filesystems
- **Git integration**: Full git operations directly in the browser
- **Color-coded display**: Files colored by type and git status
- **Vim-style keybindings** for efficient navigation

#### Navigation
- Arrow keys and vim keys (j/k) for movement
- Tab/Shift+Tab for pane switching
- Enter to open directories
- Backspace to go to parent directory
- PgUp/PgDn for scrolling (5 lines at a time)

#### File Operations
- Copy files/directories between panes (`c`)
- Move files/directories between panes (`t`)
- Delete files/directories with confirmation (`d`)
- Rename files/directories interactively (`n`)
- Create new files (`f`) and directories (`F`)
- View files in $PAGER (`v`)
- Edit files in $EDITOR (`e`)
- Refresh directory contents (`s`)
- All operations work on both local and remote files

#### Git Operations
- Stage files (`a`)
- Unstage files (`u`)
- Restore files to HEAD with confirmation (`r`)
- View colored diffs in pager (`g`)
- Create commits with editor (`o`)
- View file history (`l`)
- View git blame (`b`)
- Git status shown inline in Git mode

#### SSH/Remote Features
- Connect to remote hosts via SSH (`S`)
- Disconnect from remote hosts (`x`)
- Password authentication support
- Browse remote filesystems like local
- Copy files between local and remote
- Copy files between two remote hosts
- Execute shell commands on remote hosts
- Edit remote files (automatic download/upload)
- View remote files in pager

#### Display & UI
- Unicode box-drawing characters for clean interface
- Dynamic column width adjustment
- Context-sensitive help overlay (`h`)
- Mode selection prompt (`m`)
- Confirmation dialogs for destructive operations
- Status messages and command output display
- Permanent help hints at bottom of screen
- All commands available in all modes

#### Documentation
- Comprehensive README.md with installation and usage
- Complete COMMANDS.md reference with all keybindings
- CLAUDE.md architecture documentation for developers
- VERSIONING.md with semantic versioning policy
- Inline help system accessible with `h` key

#### Architecture
- Mixin-based design for clean separation of concerns
- Modular rendering system (split into 3 modules)
- Type-annotated Python codebase
- Comprehensive test suite with pytest
- Support for both local and remote path types

### Technical Details

#### Dependencies
- Python 3.8+
- curses (standard library)
- paramiko (for SSH/SFTP)
- pytest (for testing)

#### Tested On
- Linux with 256-color terminal support
- Minimum terminal size: 80x24 characters

#### Known Limitations
- No progress indicator for large file copies
- Remote ownership shows numeric UIDs/GIDs (not resolved names)
- Git operations only work on local repositories
- No concurrent file operations

### Repository
- Initial GitHub repository: https://github.com/radek-zitek-cloud/nerdy-doorkey

---

## Release Notes Format

For future releases, each version will document:

### Added
New features and capabilities

### Changed
Changes to existing functionality

### Deprecated
Features that will be removed in future versions

### Removed
Features that have been removed

### Fixed
Bug fixes

### Security
Security-related changes

---

[0.2.0]: https://github.com/radek-zitek-cloud/nerdy-doorkey/releases/tag/v0.2.0
[0.1.0]: https://github.com/radek-zitek-cloud/nerdy-doorkey/releases/tag/v0.1.0
