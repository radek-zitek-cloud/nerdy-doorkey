# Nerdy Doorkey

A powerful dual-pane terminal file browser with SSH support, Git integration, and comprehensive file operations.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

## Features

### 🎯 Core Features

- **Dual-Pane Interface**: Browse two directories side-by-side with independent navigation
- **Remote SSH Support**: Connect to remote hosts via SSH and browse remote filesystems seamlessly
- **Git Integration**: View git status, stage/unstage files, commit, diff, log, and blame directly in the browser
- **Three Display Modes**:
  - **File Mode**: Shows file size and modification time
  - **Git Mode**: Shows git status codes inline
  - **Owner Mode**: Shows file ownership (user:group)
- **Comprehensive File Operations**: Copy, move, delete, rename, create files/directories
- **Cross-System Operations**: Copy files between local and remote systems, or between two remote hosts
- **Color-Coded Display**: Files colored by type (directories, executables, symlinks, hidden files) and git status
- **Keyboard-Driven**: Fast, efficient navigation with vim-style keybindings

### 📁 File Operations

All operations work on both local and remote files:

- **Copy** (`c`): Copy files between panes (local↔remote supported)
- **Move** (`t`): Move files between panes
- **Delete** (`d`): Delete files/directories with confirmation
- **Rename** (`n`): Rename files interactively
- **Create** (`f`/`F`): Create new files or directories
- **View** (`v`): View files in your `$PAGER`
- **Edit** (`e`): Edit files in your `$EDITOR` (remote files downloaded/uploaded automatically)

### 🔧 Git Operations

Work with git repositories directly from the browser:

- **Stage** (`a`): Add files to git staging area
- **Unstage** (`u`): Remove files from staging
- **Restore** (`r`): Restore files to HEAD state
- **Diff** (`g`): View colored diffs in pager
- **Commit** (`o`): Create commits with your editor
- **Log** (`l`): View file history
- **Blame** (`b`): View line-by-line authorship

### 🌐 SSH/Remote Features

- **Connect** (`S`): Connect pane to remote host via SSH
- **Disconnect** (`x`): Disconnect from remote and return to local
- Password authentication supported
- All file operations work transparently on remote files
- Browse local and remote simultaneously
- Copy between two remote hosts via local intermediary

## Installation

### Requirements

- Python 3.8 or higher
- Unix-like terminal with curses support
- Git (optional, for git integration)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/nerdy-doorkey.git
   cd nerdy-doorkey
   ```

2. **Install dependencies (Poetry manages the virtual environment automatically)**:
   ```bash
   poetry install
   ```

3. *(Optional)* **Enter the Poetry shell**:
   ```bash
   poetry shell
   ```

### Package Layout

The runtime Python package lives in `src/nedok` (formerly `src/dual_pane_browser`). Import helpers such as `DualPaneBrowser` via `from src.nedok import DualPaneBrowser`.

## Usage

### Quick Start

Launch the browser:
```bash
python -m src.nedok.cli [left_dir] [right_dir]
```

If no directories are specified, both panes start in the current directory.

### Examples

```bash
# Browse current directory in both panes
python -m src.nedok.cli

# Browse two different directories
python -m src.nedok.cli ~/projects ~/documents

# Browse home directory and /tmp
python -m src.nedok.cli ~ /tmp
```

### Basic Navigation

- **↑↓** or **j/k**: Move cursor up/down
- **Enter**: Enter selected directory
- **Backspace**: Go to parent directory
- **Tab**: Toggle between left/right pane
- **→**: Switch to right pane
- **←** or **Shift+Tab**: Switch to left pane
- **PgUp/PgDn**: Scroll by 5 lines

### Display Modes

Press **m** to open mode selection, then:
- **f**: File mode (shows size and modification time)
- **g**: Git mode (shows git status)
- **o**: Owner mode (shows user:group ownership)

**Note**: All commands are available in all modes. Modes only change what information is displayed.

### SSH Connection

1. Press **S** to initiate connection
2. Enter hostname (e.g., `server.example.com` or `192.168.1.100`)
3. Tab to username field (default: current user)
4. Tab to password field
5. Press Enter to connect
6. Press **x** to disconnect and return to local

When you leave the host field, Nerdy Doorkey automatically checks for saved credentials or SSH-agent support. If credentials are available, you'll be prompted to reuse them or override with new details before connecting.

### Getting Help

- Press **h** to toggle help overlay with all commands
- See [COMMANDS.md](COMMANDS.md) for complete command reference
- See [ARCHITECTURE.md](ARCHITECTURE.md) for architecture documentation

## Documentation

- **[COMMANDS.md](COMMANDS.md)**: Complete command reference with examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Architecture and development documentation
- **[AGENTS.md](AGENTS.md)**: AI agent documentation

## Keyboard Shortcuts

### Quick Reference

```
Navigation:     ↑↓/jk  PgUp/PgDn  Enter  Backspace  Tab/←→
Files:          c)opy  t)ransfer  d)elete  n)ame  f)ile  F)older
Edit:           v)iew  e)dit  s)ync  S)sh  x)disconnect
Git:            a)dd  u)nstage  r)estore  g)diff  o)commit  l)og  b)lame
Other:          :cmd  m)ode  h)elp  q)uit
```

## Color Scheme

### File Mode
- **Blue (bold)**: Directories
- **Green (bold)**: Executable files
- **Cyan**: Symbolic links
- **Gray (dim)**: Hidden files (dotfiles)
- **Yellow**: Read-only files
- **White**: Regular files

### Git Mode
- **Red (bold)**: Untracked files (`??`)
- **Red**: Deleted files
- **Yellow**: Modified unstaged files
- **Green (bold)**: Staged files
- **Cyan**: Renamed files
- **Gray (dim)**: Clean files

### Selection
- Current selection shown with **reverse video** (inverted colors)

## Configuration

### Configuration File

Nerdy Doorkey supports a configuration file at `~/.nedok.toml` for customizing:
- Color schemes for File and Git modes
- Saved SSH credentials
- Session state (last used directories)

**Example configuration:**
```bash
# Copy example config to home directory
cp .nedok.toml.example ~/.nedok.toml

# Edit with your preferences
nano ~/.nedok.toml
```

See `.nedok.toml.example` in the repository for full configuration options.

### Session Management

Nerdy Doorkey automatically saves your complete session when you exit:
- **Last directories**: Both pane locations saved to `~/.nedok.toml`
- **SSH connections**: Remote connections automatically saved and restored
- **Auto-reconnect**: SSH sessions resume if credentials/keys available
- **Seamless workflow**: Exit and restart to continue exactly where you left off
- **Manual override**: Specify directories as arguments to start fresh

**Session Persistence:**
- Local directories always saved
- Remote SSH connections saved (hostname, username, remote directory)
- On restart: Auto-reconnect if credentials saved or SSH agent has keys
- Fallback: Uses local directory if reconnection fails

**Example:**
```bash
# First session - connect to remote server
python -m src.nedok.cli
# Press S, connect to server.example.com
# Browse remote files, then quit

# Exit and later restart - automatically reconnects!
python -m src.nedok.cli
# ✓ Reconnected left pane to user@server.example.com

# Start fresh with new directories (no auto-reconnect)
python -m src.nedok.cli /tmp /var/log
```

### SSH Credentials & Security

#### Authentication Methods

Nerdy Doorkey tries authentication methods in the following secure order:
1. **SSH Agent keys** (recommended) - Keys stored in memory, never on disk
2. **Key files** from `~/.ssh/` - Automatically discovered
3. **Password** (last resort) - Only if no keys available

**🔐 Recommendation:** Use SSH agent (`ssh-agent`) with key-based authentication for maximum security.

#### Host Key Verification

For security, unknown host keys require confirmation before connecting:
- **First connection**: You'll be prompted to accept the host key fingerprint
- **MITM protection**: Prevents man-in-the-middle attacks
- **Trust-on-first-use**: Accepted keys are stored in `~/.ssh/known_hosts`

**⚠️  Always verify the fingerprint** before accepting an unknown host key!

#### Credential Storage

After connecting to an SSH host, you'll be prompted to save credentials:
- **Automatic loading**: Enter a saved hostname to auto-populate username/password
- **⚠️  Security Warning**: Passwords are stored in **PLAINTEXT** in `~/.nedok.toml`
- **Best practice**: Only save username, use SSH agent for keys
- **For production**: Set up key-based authentication with `ssh-keygen` and `ssh-add`

**Example: Setting up SSH agent**
```bash
# Start SSH agent
eval "$(ssh-agent -s)"

# Add your SSH key
ssh-add ~/.ssh/id_rsa

# Now connect without password!
python -m src.nedok.cli
# Press Ctrl+S to connect to SSH host
```

### Environment Variables

- **`$EDITOR`**: Editor for file editing (`e`) and git commits (`o`). Default: `vi`
- **`$PAGER`**: Pager for viewing files (`v`) and git output. Default: `less -R`

### Examples

```bash
# Use nano as editor
export EDITOR=nano

# Use bat as pager
export PAGER="bat --style=plain"

# Then launch
python -m src.nedok.cli
```

## Development

### Running Tests

```bash
poetry run python -m pytest -q
```

### Project Structure

```
nerdy-doorkey/
├── src/nedok/cli.py                  # Entry point (python -m src.nedok.cli) - 182 lines
├── src/nedok/
│   ├── browser.py                    # Core browser orchestration - 280 lines
│   ├── input_handlers.py            # Keyboard input handling - 674 lines
│   ├── file_operations.py           # File operation methods - 527 lines
│   ├── git_operations.py            # Git operation methods - 378 lines
│   ├── ssh_connection.py            # SSH/SFTP connection wrapper - 325 lines
│   ├── state.py                     # Pane state and entry models - 404 lines
│   ├── modes.py                     # Display mode definitions (File/Git/Owner) - 26 lines
│   ├── config.py                    # Configuration file management - 231 lines
│   ├── render.py                    # Main rendering logic - 369 lines
│   ├── render_dialogs.py            # Modal dialog rendering - 283 lines
│   ├── render_utils.py              # Rendering utilities - 138 lines
│   ├── colors.py                    # Color management - 158 lines
│   ├── git_status.py                # Git status collection - 68 lines
│   ├── help_text.py                 # Help text generation - 18 lines
│   └── formatting.py                # Display formatting - 28 lines
├── tests/                            # Test suite (pytest)
│   ├── test_browser_git_operations.py
│   ├── test_config.py
│   ├── test_formatting.py
│   ├── test_git_status.py
│   ├── test_help_text.py
│   ├── test_main.py
│   └── test_new_features.py
├── .nedok.toml.example              # Example configuration file
└── pyproject.toml                    # Poetry configuration
```

### Architecture

The project uses a **mixin-based architecture** for clean separation of concerns:

- **`DualPaneBrowser`**: Core class that orchestrates the event loop
- **`InputHandlersMixin`**: All keyboard input handling
- **`FileOperationsMixin`**: All file operations
- **`GitOperationsMixin`**: All git operations

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- Python [curses](https://docs.python.org/3/library/curses.html) for terminal UI
- [paramiko](https://www.paramiko.org/) for SSH/SFTP support
- Love for keyboard-driven workflows ⌨️

## Troubleshooting

### Terminal Too Small
Minimum terminal size: 80x24 characters. Increase terminal size if you see "Terminal too small" error.

### Colors Not Working
Enable 256-color support in your terminal. Most modern terminals support this by default.

### SSH Connection Failed
- Check hostname and credentials
- Ensure SSH server is running on remote host
- Verify network connectivity
- Check firewall settings

### Git Commands Not Working
- Ensure you're inside a git repository
- Install git command-line tools
- Check git is in your PATH

## See Also

- [Midnight Commander](https://midnight-commander.org/) - Classic dual-pane file manager
- [ranger](https://github.com/ranger/ranger) - Console file manager with vim keybindings
- [vifm](https://vifm.info/) - Vim-like file manager

---

**Happy browsing!** 🚀
