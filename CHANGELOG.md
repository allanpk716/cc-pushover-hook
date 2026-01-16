# Changelog

## [Unreleased]

### Changed
- Hook scripts now located in `.claude/hooks/pushover-hook/` subdirectory for better isolation
- Updated `install.py` to create `pushover-hook/` subdirectory during installation
- All documentation updated with new paths

### Migration Notes
If you have an existing installation:
1. Run the new `install.py` script - it will automatically update your configuration
2. Or manually move files from `.claude/hooks/` to `.claude/hooks/pushover-hook/`
3. Update paths in `settings.json`
