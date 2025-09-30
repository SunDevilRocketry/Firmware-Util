# Firmware-Util

## Overview
A Windows desktop application for flashing Sun Devil Rocketry Flight Computer firmware to ST-Link compatible boards. The tool provides an automated setup wizard, fetches firmware releases from GitHub, and handles the complete flashing process.

## Project Details
- **Language**: Python 3.11
- **Target Platform**: Windows x86_64/AMD64
- **GUI Framework**: tkinter
- **Purpose**: Simplify firmware flashing for SDR flight computers

## Architecture

### Main Components
1. **firmware_flasher.py** - Main application with GUI
   - First-run setup wizard
   - ST-Link toolkit installation
   - GitHub release fetching with semantic versioning filter
   - Firmware selection and flashing interface
   - Board detection and error handling

2. **build.py** - PyInstaller build script
   - Creates standalone .exe with no dependencies
   - Packages everything into single distributable file

3. **run_test.py** - Development environment test
   - Validates dependencies
   - Provides usage instructions

### Key Features
- Intelligent setup detection (skips wizard if ST-Link already working)
- Automated ST-Link toolkit installation
- PATH variable configuration
- libusb-1.0.dll setup assistance
- STSW-009 driver installation guidance
- Settings menu for re-running setup wizard when needed
- GitHub API integration (public access)
- Semantic version filtering (excludes non-semver releases)
- Binary file filtering (only shows releases with .bin files)
- Pre-release version support
- Board connection verification
- One-click firmware flashing
- Error display and logging

## Configuration
User configuration stored in: `~/.sdr_flasher_config.json`
Contains ST-Link installation path and setup status.

## Recent Changes
- 2025-09-30: Initial implementation
  - Created Windows desktop application
  - Implemented first-run setup wizard
  - Added GitHub API integration for Flight-Computer-Firmware repo
  - Implemented semantic versioning filter
  - Added board detection and flashing functionality
  - Created build script for standalone executable
  - Enhanced setup detection to skip wizard if ST-Link already working
  - Added Settings menu for accessing setup wizard later
  - Added setup status checking to show current installation state

## Windows Requirements
- Windows 10/11 (x86_64/AMD64)
- Python 3.11+ (for development/building)
- ST-Link compatible hardware
- USB connection to board

## Note
This application is Windows-specific and cannot run on the Linux Replit environment. It must be deployed and run on Windows machines where ST-Link hardware is connected.
