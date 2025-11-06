# Versioning Policy

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

## Semantic Versioning Format

Version numbers follow the format: **MAJOR.MINOR.PATCH**

Example: `1.2.3`
- `1` = Major version
- `2` = Minor version
- `3` = Patch version

## Version Increment Rules

### MAJOR version (X.0.0)
Increment when making **incompatible API changes** or major breaking changes:
- Removing or renaming command-line arguments
- Removing or changing key bindings in incompatible ways
- Removing or changing configuration file formats
- Major architectural changes that affect user workflows

### MINOR version (0.X.0)
Increment when adding **functionality in a backward-compatible manner**:
- Adding new commands or features
- Adding new display modes
- Adding new keybindings (without removing old ones)
- Adding new configuration options
- Performance improvements

### PATCH version (0.0.X)
Increment when making **backward-compatible bug fixes**:
- Fixing crashes or errors
- Fixing display issues
- Fixing documentation errors
- Security patches that don't change functionality

## Pre-1.0 Development Versions (0.x.x)

Versions **0.x.x** indicate pre-release/beta software where:
- The API is not yet stable
- Breaking changes may occur in minor versions
- The software is functional but still evolving
- Not recommended for production use

**Current Status**: The project is in 0.x.x phase, indicating active development toward a stable 1.0.0 release.

## Version 1.0.0

Version **1.0.0** will be released when:
- Core functionality is stable and well-tested
- API/keybindings are finalized
- Documentation is complete
- No major bugs or crashes
- Ready for production use

After 1.0.0, all version increments will follow strict semantic versioning.

## Release Process

**IMPORTANT**: All version locations must be updated together to avoid mismatches between pip installation version and runtime `__version__`.

### Version Bump Checklist

1. **Update version in ALL locations** (critical - avoid version mismatch):
   - `pyproject.toml` - Line 3: `version = "X.Y.Z"`
   - `VERSION` file - Single line with version number
   - `src/nedok/__init__.py` - `__version__ = "X.Y.Z"`
   - `src/nedok/cli.py` - `__version__ = "X.Y.Z"`

2. **Update CHANGELOG.md** with release notes:
   - Add new `## [X.Y.Z] - YYYY-MM-DD` section
   - List all changes, features, and fixes

3. **Update VERSIONING.md**:
   - Add entry to Version History section with date and description

4. **Commit all changes together**:
   ```bash
   git add pyproject.toml VERSION src/nedok/__init__.py src/nedok/cli.py CHANGELOG.md VERSIONING.md
   git commit -m "Bump version to X.Y.Z

   - Brief description of release
   - Major changes listed here

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

5. **Create git tag**:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   ```

6. **Push changes and tag**:
   ```bash
   git push origin <branch> && git push origin vX.Y.Z
   ```

7. **Create GitHub release** from tag with changelog notes

### Why Update All Locations?

- **pyproject.toml**: Controls what version pip installs
- **VERSION**: Used by build scripts and documentation
- **__init__.py**: Exported as `nedok.__version__` for programmatic access
- **cli.py**: Displayed in `--version` flag and error messages

**Failure to update all locations causes confusion** where `pip show nedok` shows one version but the running code reports another.

## Version History

- **v0.5.0** (2025-01-06): Documentation overhaul and comprehensive test suite
  - Renamed CLAUDE.md to ARCHITECTURE.md for better discoverability
  - Updated all documentation with accurate line counts and module descriptions
  - Added 38 new test cases across 3 new test files (test_modes.py, test_colors.py, test_state.py)
  - Enhanced test_config.py with 10 additional comprehensive tests
  - Total test suite: 79 tests covering all core modules
  - Fixed version synchronization across all files (pyproject.toml, VERSION, __init__.py, cli.py)
  - Updated VERSIONING.md with improved release process checklist

- **v0.4.4** (2025-11-06): Fix workflow permissions for releases
  - Added permissions: contents: write to workflow
  - Fixes 403 error when creating GitHub releases
  - Binaries successfully built and attached to releases

- **v0.4.3** (2025-11-06): Add missing spec file to repository
  - Added nedok.spec to git (was previously ignored by .gitignore)
  - Fixes GitHub Actions workflow build failures
  - Spec file required for PyInstaller builds in CI/CD

- **v0.4.2** (2025-11-06): Build system fixes
  - Fixed GitHub Actions workflow to use nedok.spec file
  - Fixed PyInstaller builds to handle absolute imports correctly
  - Fixed build.sh typos and updated to use spec file
  - Workflow trigger verified for v* tags

- **v0.4.1** (2025-11-06): Absolute imports and tooling improvements
  - Converted all relative imports to absolute nedok.* imports
  - Python version constraint updated (>=3.8,<3.15)
  - Added pyinstaller for binary distribution support
  - Improved compatibility with Python tooling and IDEs

- **v0.4.0** (2025-11-06): Poetry build system migration
  - Migrated to Poetry for dependency and build management
  - Added pyproject.toml with Poetry configuration
  - Formalized src-layout package structure
  - Modern Python packaging for future PyPI distribution

- **v0.3.1** (2025-11-07): Package rename and SSH credential workflow prompt
  - Runtime package moved to `src/nedok`
  - CLI now auto-detects saved/agent credentials after entering a host
  - Documentation updated to reference the new package name

- **v0.3.0** (2025-11-06): Security and reliability improvements
  - SSH agent integration for key-based authentication
  - Host key verification (MITM protection)
  - Security warnings throughout UI
  - Command output truncation indicators
  - Enhanced remote error handling
  - Config mutation regression tests

- **v0.2.1** (2025-11-06): Critical bug fixes
  - Fixed remote navigation crash (backspace on SSH panes)
  - Fixed configuration mutation bug (deep copy issue)
  - Added error feedback for config save failures

- **v0.2.0** (2025-01-05): Configuration and session management
  - TOML configuration file support
  - SSH credential auto-save and auto-load
  - Session persistence (save/restore directories)
  - Keypress wait after external commands
  - Color customization framework

- **v0.1.0** (2025-01-05): Initial working release
  - Dual-pane file browser
  - SSH/remote support
  - Git integration
  - Three display modes (File, Git, Owner)
  - Comprehensive file operations

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
