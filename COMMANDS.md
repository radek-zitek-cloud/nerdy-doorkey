# Command Reference

Complete documentation of all commands, keybindings, git status symbols, and color schemes for the dual-pane browser.

## Quick Start

- **Launch:** `python -m src.nedok.cli [left_dir] [right_dir]`
- **Help:** Press `h` to toggle help overlay
- **Mode Switch:** Press `m` to switch between File, Tree, Git, and Owner modes
- **Quit:** Press `q` to exit

## Navigation Commands

| Key | Action |
|-----|--------|
| `↑` / `k` | Move cursor up |
| `↓` / `j` | Move cursor down |
| `PgUp` | Move cursor up by 5 lines |
| `PgDn` | Move cursor down by 5 lines |
| `Enter` | Enter selected directory |
| `Backspace` | Go to parent directory |
| `Tab` | Toggle between left/right pane |
| `→` | Switch to right pane |
| `←` / `Shift+Tab` | Switch to left pane |

### Tree Navigation (Left Pane)

Tree mode renders only the left pane as a recursive directory tree.

| Key | Action |
|-----|--------|
| `m` then `t` | Switch to Tree mode |
| `+` | Expand the selected directory in the tree |
| `-` | Collapse the selected directory, or the parent of a selected file |

## File Operations (Available in All Modes)

| Key | Command | Description |
|-----|---------|-------------|
| `c` | Copy | Copy selected file/directory to the other pane (works between local/remote) |
| `t` | Move | Move selected file/directory to the other pane (works between local/remote) |
| `d` | Delete | Delete selected file/directory (requires confirmation, works on remote) |
| `n` | Rename | Rename selected file/directory (interactive input, works on remote) |
| `f` | Create File | Create a new file in current directory (interactive input, works on remote) |
| `F` | Create Directory | Create a new directory in current directory (interactive input, works on remote) |
| `v` | View | View selected file in $PAGER (downloads remote files to temp) |
| `e` | Edit | Edit selected file in $EDITOR (remote files: download→edit→upload) |
| `s` | Refresh | Reload directory contents of active pane |
| `S` | SSH Connect | Connect active pane to remote host via SSH |
| `x` | SSH Disconnect | Disconnect active pane from remote host and return to local |

## Git Operations (Available in All Modes)

| Key | Command | Description |
|-----|---------|-------------|
| `a` | Stage | Add selected file to git staging area |
| `u` | Unstage | Remove selected file from git staging area |
| `r` | Restore | Restore selected file to HEAD state (requires confirmation) |
| `g` | Diff | View git diff of selected file in pager with colors |
| `o` | Commit | Create git commit using $EDITOR for commit message |
| `l` | Log | View git log for selected file in pager |
| `b` | Blame | View git blame for selected file in pager |

## Mode Commands

**Note:** All file and git operations are available in all modes. Modes only change what information is displayed in the columns.

| Key | Mode | Description |
|-----|------|-------------|
| `m` | All | Open mode selection prompt |
| `f` | Prompt | Switch to File mode (shows size and modification time) |
| `t` | Prompt | Switch to Tree mode (left pane recursive tree, +/- to expand/collapse) |
| `g` | Prompt | Switch to Git mode (shows git status) |
| `o` | Prompt | Switch to Owner mode (shows user:group ownership) |

## Other Commands

| Key | Command | Description |
|-----|---------|-------------|
| `:` | Command Mode | Enter shell command (executed in active pane's directory) |
| `h` | Help | Toggle help overlay |
| `q` | Quit | Exit the browser |
| `Esc` | Cancel | Cancel current input mode (command, rename, create, mode prompt) |

## Interactive Input Modes

### Command Mode (`:`)
- Type shell command and press `Enter` to execute
- Output appears in bottom pane (last 200 lines)
- Press `Esc` to cancel
- Press `Backspace` to delete characters

### Rename Mode (`n`)
- Enter new name for selected file/directory
- Press `Enter` to confirm rename
- Press `Esc` to cancel
- Press `Backspace` to delete characters

### Create Mode (`f` / `F`)
- Enter name for new file or directory
- Press `Enter` to create
- Press `Esc` to cancel
- Press `Backspace` to delete characters

### SSH Connection Mode (`S`)
- Enter host address (e.g., `server.example.com` or `192.168.1.100`)
- Press `Enter` or `Tab` to move to next field
- Enter username (defaults to current user)
- Press `Enter` or `Tab` to move to password field
- Enter password (displayed as `***`)
- Press `Enter` to connect
- Press `Esc` to cancel at any time
- Connected pane shows `user@host:path` in title
- Shell commands (`:`) execute on remote host
- File operations work transparently on remote files

### Confirmation Dialogs
Some destructive operations require confirmation:
- Delete (`d`)
- Git restore (`r`)

Respond with:
- `y` or `Y` to confirm
- `n` or `N` or `Esc` to cancel

## Git Mode Status Symbols

When in Git mode (press `m` then `g`), files show git status in the Mode column:

| Symbol | Status | Description |
|--------|--------|-------------|
| `??` | Untracked | File not tracked by git |
| `M ` | Modified (staged) | File modified and staged for commit |
| ` M` | Modified (unstaged) | File modified but not staged |
| `MM` | Modified (both) | File has both staged and unstaged changes |
| `A ` | Added | New file staged for commit |
| `D ` | Deleted (staged) | File deleted and staged |
| ` D` | Deleted (unstaged) | File deleted but not staged |
| `R ` | Renamed | File renamed |
| `C ` | Copied | File copied |
| `U ` | Updated (unmerged) | File has merge conflicts |
| `  ` | Clean | File is tracked and unmodified |

### Git Status Symbol Format

Git uses a two-character status format `XY`:
- **Left character (X):** Status in staging area (index)
- **Right character (Y):** Status in working tree

**Examples:**
- `M ` = Modified in index, unchanged in working tree
- ` M` = Unchanged in index, modified in working tree
- `MM` = Modified in index, also modified in working tree
- `A ` = New file added to index
- `??` = Untracked file (not in index or working tree)

## Color Schemes

### File Mode Colors

Colors in File mode help identify file types and permissions:

| Color | Style | File Type | Description |
|-------|-------|-----------|-------------|
| **Blue** | Bold | Directories | Folders and directory entries |
| **Green** | Bold | Executables | Files with execute permission (x bit set) |
| **Cyan** | Normal | Symlinks | Symbolic links |
| **Gray** | Dim | Hidden files | Files starting with `.` (dotfiles) |
| **Yellow** | Normal | Readonly | Files without write permission for user |
| White | Normal | Regular files | Standard files with write permission |

**Selection:** Current cursor position shown with reverse video (inverted colors)

### Git Mode Colors

Colors in Git mode indicate git status:

| Color | Style | Git Status | Description |
|-------|-------|------------|-------------|
| **Red** | Bold | Untracked (`??`) | Files not in git repository |
| **Red** | Normal | Deleted (`D`) | Files deleted from working tree |
| **Yellow** | Normal | Modified unstaged (` M`) | Files changed but not staged |
| **Green** | Bold | Staged (`M `, `A `) | Files staged for commit |
| **Cyan** | Normal | Renamed (`R `) | Files that were renamed |
| **Gray** | Dim | Clean (`  `) | Tracked files with no changes |
| **Blue** | Bold | Directories | Folders (always shown in blue) |

**Selection:** Current cursor position shown with reverse video (inverted colors)

### Parent Directory (`..`)

The parent directory entry is always shown in **bold blue** in both modes.

## Display Layout

```
┌─────────────────────────────────┬─────────────────────────────────┐
│ Left Pane                       │ Right Pane                      │
│                                 │                                 │
│ Name            Mode  Size  Mod │ Name            Mode  Size  Mod │
│ ..                              │ ..                              │
│ directory/      drwxr-xr-x      │ file.txt        -rw-r--r--  1KB │
│                                 │                                 │
├─────────────────────────────────┴─────────────────────────────────┤
│ Command Area / Status / Output                                    │
│                                                                    │
│ > Command output appears here...                                  │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Column Headers

**File Mode:**
- **Name:** Filename (directories end with `/`)
- **Mode:** Unix file permissions (e.g., `drwxr-xr-x`)
- **Size:** File size in human-readable format (B, KB, MB, GB)
- **Modified:** Last modification timestamp

**Git Mode:**
- **Name:** Filename (directories end with `/`)
- **Git:** Git status code (e.g., `M `, `??`, `A `)
- **Size:** File size in human-readable format
- **Modified:** Last modification timestamp

**Owner Mode:**
- **Name:** Filename (directories end with `/`)
- **Mode:** Unix file permissions (e.g., `drwxr-xr-x`)
- **User:** File owner username (or UID for remote)
- **Group:** File owner group name (or GID for remote)

## Remote (SSH) Operations

### Connecting to Remote Host

Press `S` (Shift+s) to initiate SSH connection in active pane:

1. **Host:** Enter hostname or IP address
   - If credentials are saved for this host, they will be auto-loaded
2. **User:** Enter username (default: current user or saved username)
3. **Password:** Enter password (shown as `***`, auto-loaded if saved)
4. **Connect:** Press Enter to establish connection
5. **Save:** After successful connection, you'll be prompted to save credentials

**Saved Credentials:**
- Automatically loaded when you enter a known hostname
- Stored in `~/.nedok.toml` configuration file
- **WARNING:** Passwords stored in plaintext - use SSH keys for production!

Once connected:
- Pane title shows: `user@host:/remote/path`
- Browse remote filesystem like local
- All file operations work transparently

### Disconnecting from Remote Host

Press `x` to disconnect the active pane from SSH:
- Closes the SSH connection
- Returns pane to local home directory
- All file operations revert to local filesystem

### Remote File Operations Support

All operations work seamlessly on remote files:

| Operation | How It Works |
|-----------|-------------|
| **Browse** | Navigate remote directories with arrow keys/Enter |
| **Copy** | `c` - Copy local↔remote, remote↔local, remote↔remote |
| **Move** | `t` - Move local↔remote (copy + delete source) |
| **Delete** | `d` - Delete remote files/directories (recursive) |
| **Rename** | `n` - Rename remote files/directories |
| **Create** | `f`/`F` - Create remote files/directories |
| **View** | `v` - Download to temp, open in $PAGER, clean up |
| **Edit** | `e` - Download to temp, edit, upload changes back |
| **Commands** | `:` - Execute shell commands on remote host |

### Mixed Local/Remote Workflows

You can browse local and remote simultaneously:

**Uploading Files to Server:**
1. Left pane: Local directory
2. Right pane: Press `S` and connect to server
3. Navigate both panes to desired locations
4. Select files in left pane, press `c` to copy to remote

**Downloading Files from Server:**
1. Left pane: Connect to server with `S`
2. Right pane: Local destination directory
3. Select files in left pane, press `c` to copy to local

**Copying Between Servers:**
1. Left pane: Connect to server1
2. Right pane: Connect to server2
3. Select files, press `c` to copy (via local temp)

**Editing Remote Config:**
1. Connect to server with `S`
2. Navigate to config file
3. Press `e` to edit
4. Changes automatically uploaded on save

## Tips & Tricks

### Workflow Examples

**Staging Files for Commit:**
1. Press `m` → `g` to enter Git mode
2. Navigate to modified files (shown in yellow or red)
3. Press `a` on each file to stage
4. Staged files turn green
5. Press `o` to commit with editor

**Comparing File Changes:**
1. Navigate to modified file
2. Press `g` to view colored diff in pager
3. Use pager controls to browse (Space, arrows, q to quit)

**Copying Files Between Directories:**
1. Navigate to source file in one pane
2. Navigate to destination directory in other pane
3. Press `c` to copy

**Renaming Multiple Files:**
1. Navigate to first file
2. Press `n`, enter new name, press Enter
3. Navigate to next file
4. Repeat

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `$EDITOR` | `vi` | Editor for file editing (`e`) and git commits (`o`) |
| `$PAGER` | `less -R` | Pager for viewing files (`v`) and git output (`g`, `l`, `b`) |

### Command Output

- Shell command output (`:`) is displayed in bottom pane
- Last 200 lines retained
- Both stdout and stderr captured
- Exit code shown in status message

### Confirmation Dialogs

Destructive operations show confirmation prompts:
```
Delete /path/to/file? (y/n)
```

Respond with `y` to proceed or `n`/`Esc` to cancel.

## Keyboard Shortcuts Reference Card

### Quick Reference
```
Navigation:     ↑↓/jk  PgUp/PgDn  Enter  Backspace  Tab/←→
Files:          c)opy  t)ransfer  d)elete  n)ame  f)ile  F)older
Edit:           v)iew  e)dit  s)ync  S)sh
Git:            a)dd  u)nstage  r)estore  g)diff  o)commit  l)og  b)lame
Other:          :cmd  m)ode  h)elp  q)uit
```

## Error Messages

| Message | Cause | Solution |
|---------|-------|----------|
| `Permission denied reading directory` | No read permission | Change directory permissions or run as different user |
| `Directory not found` | Directory was deleted | Navigate to parent directory |
| `Cannot run external command` | Failed to suspend curses | Restart application |
| `Command failed: ...` | Shell command error | Check command syntax and permissions |
| `Not in a git repository` | Git operation outside repo | Navigate to git repository |
| `File not found` | File was deleted | Refresh with `s` or navigate away |
| `SSH connection failed: ...` | Cannot connect to remote | Check hostname, credentials, network connectivity |
| `No SSH connection` | Operation requires connection | Connect first with `S` |
| `Copy failed: ...` | Transfer error | Check permissions, disk space, network connection |

## Platform Notes

### Terminal Requirements
- Terminal with curses support required
- Color support recommended (256-color terminal ideal)
- Minimum terminal size: 80x24 characters
- Unicode support recommended for box-drawing characters

### Git Integration
- Requires git command-line tools installed
- Git operations only work inside git repositories
- Git status cached per directory (refresh with `s` to update)

### File Operations
- Copy/move operations preserve permissions
- Symbolic links preserved during copy
- Hidden files (dotfiles) fully supported
- Large files may take time to copy (no progress indicator)

### SSH/Remote Operations
- Requires `paramiko` Python library (managed via Poetry)
- Password authentication supported (key-based auth available via SSH agent)
- Remote paths use POSIX format (forward slashes)
- Each pane can connect to different remote hosts
- Remote-to-remote copies use local system as intermediary
- Temp files used for view/edit operations (cleaned up automatically)
- Remote operations work over SFTP protocol
- Connection details: hostname, username, password (optional: port 22 default)

## See Also

- `ARCHITECTURE.md` - Architecture and development documentation
- `README.md` - Project overview and installation
- `src/nedok/cli.py` - Entry point and CLI arguments
