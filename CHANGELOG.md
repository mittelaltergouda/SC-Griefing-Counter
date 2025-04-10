# Changelog

All significant changes to the SC-Griefing-Counter project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.7.11] - 2025-04-09
### Added
- Automatic extraction of the changelog for versions in the release process
- Improved instructions for updating the changelog for new versions
- Additional hidden imports for correct compilation with PyInstaller

### Changed
- Improved maintainability through updated configuration structure
- Optimized directory management for application data
- Updated security policies

### Fixed
- Fixed error in the function for creating temporary directories

## [0.7.12] - 2025-04-10
### Added
- New function for improved Star Citizen path validation.

### Changed
- Enhanced user interface for initial setup.

### Fixed
- Resolved syntax errors in the configuration file.

## [0.7.13] - 2025-04-10
### Fixed
- Auto-update mechanism now works correctly in protected directories like Program Files
- Improved logging for the update process
- Enhanced error handling during update installation

## [0.7.14] - 2025-04-10
### Added
- Cross-platform support for the update mechanism

### Changed
- Optimized startup routine for different operating systems
- More robust error handling when cleaning AppData after updates

### Fixed
- Removed unreachable code in the update checker
- Replaced Windows-specific implementations with platform-independent code