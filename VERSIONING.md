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

1. Update `VERSION` file with new version number
2. Update `CHANGELOG.md` with release notes
3. Update version in `src/nedok/cli.py` and `__init__.py`
4. Commit changes: `git commit -m "Bump version to vX.Y.Z"`
5. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. Push changes: `git push origin main --tags`
7. Create GitHub release from tag with changelog notes

## Version History

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
