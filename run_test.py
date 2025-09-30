import sys
import os

print("=" * 70)
print("Firmware-Util - Development Environment Check")
print("=" * 70)
print()

try:
    import tkinter as tk
    print("✓ tkinter available")
except ImportError:
    print("✗ tkinter not available (expected on headless Linux)")

try:
    import requests
    print("✓ requests library installed")
except ImportError:
    print("✗ requests library not found")

try:
    import PyInstaller
    print("✓ PyInstaller installed")
except ImportError:
    print("✗ PyInstaller not found")

print()
print("Platform:", sys.platform)
print("Python version:", sys.version)
print()

if sys.platform == "win32":
    print("Running on Windows - attempting to start the application...")
    print()
    try:
        import firmware_flasher
        firmware_flasher.main()
    except Exception as e:
        print(f"Error starting application: {e}")
else:
    print("=" * 70)
    print("IMPORTANT: Firmware-Util is a Windows desktop application")
    print("=" * 70)
    print()
    print("Firmware-Util is designed to run on Windows only.")
    print("It requires:")
    print("  - Windows OS (x86_64/AMD64)")
    print("  - ST-Link toolkit (installed via the app)")
    print("  - USB connection to ST-Link hardware")
    print()
    print("TO USE THIS APPLICATION:")
    print("  1. Download all project files to a Windows machine")
    print("  2. Install Python 3.11+ on Windows")
    print("  3. Install dependencies: pip install requests pyinstaller")
    print("  4. Run: python firmware_flasher.py")
    print()
    print("TO BUILD STANDALONE EXECUTABLE:")
    print("  1. On Windows, run: python build.py")
    print("  2. Distribute: dist/Firmware-Util.exe")
    print()
    print("=" * 70)
    
    try:
        print("Performing import test...")
        import firmware_flasher
        print("✓ Application code imports successfully")
        print("✓ No syntax errors detected")
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
