import os
import sys
import subprocess

def build_executable():
    print("Building Firmware-Util executable...")
    
    pyinstaller_args = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--noupx',
        '--name=Firmware-Util',
        '--add-data=icon.png;.',
        '--add-data=resources;resources',
        'firmware_flasher.py'
    ]
    
    if os.path.exists('icon.png'):
        print("✓ Icon found, including in build")
    else:
        print("⚠ Icon not found, building without icon")
    
    # Include version info if present
    if os.path.exists('version_info.txt'):
        pyinstaller_args.insert(-1, '--version-file=version_info.txt')

    try:
        subprocess.run(pyinstaller_args, check=True)
        print("\n✓ Build complete!")
        print("Executable location: dist/Firmware-Util.exe")
        print("\nYou can now distribute the .exe file to Windows users.")
        print("No Python installation required on target machines.")
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("✗ PyInstaller not found. Please install it first:")
        print("  pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Warning: This should ideally be built on Windows for best compatibility.")
        print("Building on non-Windows platform may have issues.")
        input("Press Enter to continue anyway, or Ctrl+C to cancel...")
    
    build_executable()
