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

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start

Launch the browser:
```bash
python main.py [left_dir] [right_dir]
```

If no directories are specified, both panes start in the current directory.

### Examples

```bash
# Browse current directory in both panes
python main.py

# Browse two different directories
python main.py ~/projects ~/documents

# Browse home directory and /tmp
python main.py ~ /tmp
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

### Getting Help

- Press **h** to toggle help overlay with all commands
- See [COMMANDS.md](COMMANDS.md) for complete command reference
- See [CLAUDE.md](CLAUDE.md) for architecture documentation

## Documentation

- **[COMMANDS.md](COMMANDS.md)**: Complete command reference with examples
- **[CLAUDE.md](CLAUDE.md)**: Architecture and development documentation
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

Nerdy Doorkey automatically saves your session when you exit:
- **Last directories**: Both pane locations are saved to `~/.nedok.toml`
- **Auto-restore**: Launch without arguments to resume from your last session
- **Manual override**: Specify directories as arguments to start fresh

**Example:**
```bash
# First session - browse specific directories
python main.py ~/projects ~/documents

# Exit and later restart - resumes from last location
python main.py

# Start fresh with new directories
python main.py /tmp /var/log
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
python main.py
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
python main.py
```

## Development

### Running Tests

```bash
source .venv/bin/activate
python -m pytest -q
```

### Project Structure

```
nerdy-doorkey/
├── main.py                           # Entry point
├── src/dual_pane_browser/
│   ├── browser.py                    # Core browser orchestration
│   ├── input_handlers.py            # Keyboard input handling
│   ├── file_operations.py           # File operation methods
│   ├── git_operations.py            # Git operation methods
│   ├── ssh_connection.py            # SSH/SFTP connection wrapper
│   ├── state.py                     # Pane state and entry models
│   ├── modes.py                     # Display mode definitions
│   ├── render.py                    # Main rendering logic
│   ├── render_dialogs.py            # Modal dialog rendering
│   ├── render_utils.py              # Rendering utilities
│   ├── colors.py                    # Color management
│   ├── git_status.py                # Git status collection
│   ├── help_text.py                 # Help text generation
│   └── formatting.py                # Display formatting
└── tests/                            # Test suite
```

### Architecture

The project uses a **mixin-based architecture** for clean separation of concerns:

- **`DualPaneBrowser`**: Core class that orchestrates the event loop
- **`InputHandlersMixin`**: All keyboard input handling
- **`FileOperationsMixin`**: All file operations
- **`GitOperationsMixin`**: All git operations

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

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
