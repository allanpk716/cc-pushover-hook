# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-02-02

### Added

- **Multi-instance support**: Multiple Claude Code instances can now run concurrently without conflicts
- **PID isolation**: Cache and log files are now isolated by process ID
- **Automatic cleanup**: Expired cache files (older than 7 days) are automatically cleaned up
- **Completion markers**: Stop events now mark session completion instead of deleting cache

### Changed

- Cache file naming: `session-{id}-pid-{pid}.jsonl` (was: `session-{id}.jsonl`)
- Log file naming: `debug.{date}-pid-{pid}.log` (was: `debug.{date}.log`)
- Stop event behavior: Adds completion marker instead of deleting cache file

### Technical Details

- Each Claude Code instance now has its own:
  - Cache file: `session-{session_id}-pid-{process_id}.jsonl`
  - Log file: `debug.{date}-pid-{process_id}.log`

- Cache files are retained for 7 days then automatically cleaned up
- Backward compatible with existing integrations

## [1.0.0] - Previous Release

- Initial release with single-instance support
- Pushover notifications for task completion
- Windows desktop notifications
- Session caching and summarization
