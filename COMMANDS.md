# Command Reference

Complete documentation of all commands, keybindings, git status symbols, and color schemes for the dual-pane browser.

## Quick Start

- **Launch:** `python main.py [left_dir] [right_dir]`
- **Help:** Press `h` to toggle help overlay
- **Mode Switch:** Press `m` to switch between File and Git modes
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
| `→` / `l` / `Tab` | Switch to right pane |
| `←` / `Shift+Tab` | Switch to left pane |

## File Operations (Available in Both Modes)

| Key | Command | Description |
|-----|---------|-------------|
| `c` | Copy | Copy selected file/directory to the other pane |
| `t` | Move | Move selected file/directory to the other pane |
| `d` | Delete | Delete selected file/directory (requires confirmation) |
| `n` | Rename | Rename selected file/directory (interactive input) |
| `f` | Create File | Create a new file in current directory (interactive input) |
| `F` | Create Directory | Create a new directory in current directory (interactive input) |
| `v` | View | View selected file in $PAGER (default: less) |
| `e` | Edit | Edit selected file in $EDITOR (default: vi) |
| `s` | Refresh | Reload directory contents of active pane |

## Git Operations (Available in Both Modes)

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

| Key | Mode | Description |
|-----|------|-------------|
| `m` | Both | Open mode selection prompt |
| `f` | Prompt | Switch to File mode |
| `g` | Prompt | Switch to Git mode |

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
Edit:           v)iew  e)dit  s)ync
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

## See Also

- `CLAUDE.md` - Architecture and development documentation
- `README.md` - Project overview and installation
- `main.py` - Entry point and CLI arguments
