# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/radek-zitek-cloud/nerdy-doorkey/releases/tag/v0.1.0
