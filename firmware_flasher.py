import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import subprocess
import os
import sys
import re
import json
import zipfile
import urllib.request
import time
import ssl
try:
    import certifi
except Exception:
    certifi = None
import winreg
import shutil
from pathlib import Path
from threading import Thread
import tempfile
try:
    import py7zr
except ImportError:
    py7zr = None

class FirmwareFlasher:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmware-Util")
        self.root.geometry("800x600")
        
        try:
            if os.path.exists('icon.png'):
                self.root.iconphoto(True, tk.PhotoImage(file='icon.png'))
        except:
            pass
        
        self.maroon = "#8B0000"
        self.white = "#FFFFFF"
        self.black = "#000000"
        self.light_gray = "#F5F5F5"
        self.font_family = "Helvetica"
        
        self.root.configure(bg=self.white)
        
        self.config_file = Path.home() / ".sdr_flasher_config.json"
        self.config = self.load_config()
        
        self.releases = []
        self.selected_release = None
        self.bin_files = []
        
        if not self.check_dependencies():
            self.show_setup_wizard()
        else:
            self.create_main_ui()
    
    def _resource_path(self, relative_path):
        """Get absolute path to resource, works for PyInstaller and dev.
        Looks for files inside bundled resources directory.
        """
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path:
            candidate = Path(base_path) / 'resources' / relative_path
            if candidate.exists():
                return str(candidate)
        # Dev mode fallback
        candidate = Path('resources') / relative_path
        if candidate.exists():
            return str(candidate)
        return None
    
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {"stlink_path": "", "setup_complete": False}
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
    
    def get_stflash_executable(self):
        st_flash_path = shutil.which('st-flash')
        if st_flash_path:
            return st_flash_path
        
        stlink_path = self.config.get("stlink_path", "")
        if stlink_path:
            st_flash = os.path.join(stlink_path, "bin", "st-flash.exe")
            if os.path.exists(st_flash):
                return st_flash
        
        return None
    
    def check_dependencies(self):
        try:
            result = subprocess.run(['st-flash', '--version'], 
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                st_flash_path = shutil.which('st-flash')
                if st_flash_path:
                    bin_dir = os.path.dirname(st_flash_path)
                    stlink_path = os.path.dirname(bin_dir)
                    self.config["stlink_path"] = stlink_path
                    self.config["setup_complete"] = True
                    self.save_config()
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        if self.config.get("setup_complete"):
            stlink_path = self.config.get("stlink_path", "")
            if stlink_path and os.path.exists(stlink_path):
                st_flash = os.path.join(stlink_path, "bin", "st-flash.exe")
                if os.path.exists(st_flash):
                    return True
        
        return False
    
    def show_setup_wizard(self):
        self.setup_window = tk.Toplevel(self.root)
        self.setup_window.title("Firmware-Util Setup")
        self.setup_window.geometry("700x500")
        self.setup_window.grab_set()
        self.setup_window.configure(bg=self.white)
        
        tk.Label(self.setup_window, text="Welcome to Firmware-Util", 
                 font=(self.font_family, 16, "bold"), bg=self.white, fg=self.black).pack(pady=20)
        
        tk.Label(self.setup_window, text="This tool requires ST-Link utilities to flash firmware.\n"
                 "The setup wizard will guide you through the installation process.",
                 justify=tk.LEFT, bg=self.white, fg=self.black, font=(self.font_family, 10)).pack(pady=10, padx=20)
        
        self.setup_log = scrolledtext.ScrolledText(self.setup_window, height=15, width=80, 
                                                   bg=self.light_gray, font=(self.font_family, 9))
        self.setup_log.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.check_current_setup_status()
        
        button_frame = tk.Frame(self.setup_window, bg=self.white)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Install ST-Link Toolkit", 
                  command=self.install_stlink, width=25, bg=self.white, 
                  font=(self.font_family, 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Install STSW-009 Driver", 
                  command=self.install_driver, width=25, bg=self.white, 
                  font=(self.font_family, 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Complete Setup", 
                  command=self.complete_setup, width=25, bg="#FFD700", fg="#000000", 
                  font=(self.font_family, 9, "bold")).pack(side=tk.LEFT, padx=5)
    
    def log_setup(self, message):
        self.setup_log.insert(tk.END, message + "\n")
        self.setup_log.see(tk.END)
        self.setup_window.update()
    
    def check_current_setup_status(self):
        self.log_setup("Checking current setup status...")
        self.log_setup("=" * 60)
        
        try:
            result = subprocess.run(['st-flash', '--version'], 
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.log_setup("✓ ST-Link toolkit detected in PATH")
                self.log_setup(f"  Version: {result.stdout.strip()}")
                self.log_setup("")
                self.log_setup("ST-Link is already working! You can:")
                self.log_setup("  - Click 'Complete Setup' to proceed to the main application")
                self.log_setup("  - Or reinstall/update ST-Link using the buttons below")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.log_setup("✗ ST-Link toolkit not found in PATH")
        
        stlink_path = self.config.get("stlink_path", "")
        if stlink_path and os.path.exists(stlink_path):
            self.log_setup(f"✓ Previous installation found at: {stlink_path}")
        else:
            self.log_setup("✗ No previous installation found")
        
        self.log_setup("")
        self.log_setup("Please use the buttons below to install ST-Link and drivers.")
        self.log_setup("=" * 60)
    
    def install_stlink(self):
        self.log_setup("Starting ST-Link toolkit installation...")
        
        try:
            stlink_url = "https://github.com/stlink-org/stlink/releases/download/v1.8.0/stlink-1.8.0-win32.zip"
            install_dir = Path.home() / "STLink"
            zip_path = install_dir / "stlink.zip"
            
            install_dir.mkdir(exist_ok=True)
            self.log_setup(f"Downloading ST-Link toolkit to {install_dir}...")
            
            bundled_zip = self._resource_path('stlink-1.8.0-win32.zip')
            if bundled_zip and os.path.exists(bundled_zip):
                self.log_setup("Using bundled ST-Link archive")
                shutil.copy2(bundled_zip, zip_path)
            else:
                self.log_setup("Bundled ST-Link not found, downloading...")
                self._download_with_requests(stlink_url, zip_path)
            self.log_setup("Download complete. Extracting...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)
            
            zip_path.unlink()
            
            extracted_folder = list(install_dir.glob("stlink-*"))[0]
            self.config["stlink_path"] = str(extracted_folder)
            self.log_setup(f"ST-Link extracted to: {extracted_folder}")
            
            self.log_setup("Installing libusb-1.0.dll...")
            dll_dest = extracted_folder / "bin" / "libusb-1.0.dll"
            bundled_dll = self._resource_path('libusb-1.0.dll')
            if bundled_dll and os.path.exists(bundled_dll):
                shutil.copy2(bundled_dll, dll_dest)
                self.log_setup(f"✓ libusb-1.0.dll installed to: {dll_dest}")
            else:
                self.log_setup("✗ Bundled libusb-1.0.dll not found. Please provide it in resources.")
            
            self.log_setup("Adding ST-Link to PATH...")
            self.add_to_path(str(extracted_folder / "bin"))
            
            self.log_setup("ST-Link installation complete!")
            self.save_config()
            
        except Exception as e:
            self.log_setup(f"Error during installation: {str(e)}")
            messagebox.showerror("Installation Error", str(e))

    def _download_with_requests(self, url, dest_path, retries=3, timeout=60):
        """Download a file using requests with certifi CA bundle and retries.
        Falls back to urllib with unverified SSL context only if absolutely necessary.
        """
        last_err = None
        headers = {"User-Agent": "Firmware-Util/1.0 (+requests)"}
        for attempt in range(1, retries + 1):
            try:
                kwargs = {"headers": headers, "stream": True, "timeout": timeout}
                if certifi is not None:
                    kwargs["verify"] = certifi.where()
                with requests.get(url, **kwargs) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("Content-Length", 0))
                    downloaded = 0
                    with open(dest_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 128):
                            if not chunk:
                                continue
                            f.write(chunk)
                            downloaded += len(chunk)
                            # Optionally log progress every ~5 MB
                            if total and downloaded % (5 * 1024 * 1024) < 128 * 1024:
                                self.log_setup(f"  Downloaded {downloaded // (1024*1024)} / {total // (1024*1024)} MB...")
                return
            except Exception as e:
                last_err = e
                self.log_setup(f"  Attempt {attempt} failed: {e}")
                time.sleep(min(2 ** attempt, 10))
        # Final fallback: urllib with unverified SSL if cert chain problems persist
        try:
            self.log_setup("Falling back to urllib download (SSL unverified)...")
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(url, context=context, timeout=timeout) as resp, open(dest_path, "wb") as out:
                shutil.copyfileobj(resp, out)
        except Exception:
            raise last_err
    
    def add_to_path(self, new_path):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS)
            current_path, _ = winreg.QueryValueEx(key, 'PATH')
            
            if new_path not in current_path:
                new_path_value = current_path + ';' + new_path
                winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path_value)
                self.log_setup(f"Added {new_path} to PATH")
            else:
                self.log_setup(f"{new_path} already in PATH")
            
            winreg.CloseKey(key)
        except Exception as e:
            self.log_setup(f"Could not modify PATH: {str(e)}")
    
    def install_driver(self):
        self.log_setup("Installing STSW-LINK009 (AMD64) driver...")
        bundled_installer = self._resource_path('dpinst_amd64.exe')
        if bundled_installer and os.path.exists(bundled_installer):
            try:
                # Launch installer (user will likely need to approve UAC). Do not wait forever.
                subprocess.Popen([bundled_installer], shell=False)
                self.log_setup("Driver installer launched. Follow on-screen prompts.")
            except Exception as e:
                self.log_setup(f"✗ Failed to launch driver installer: {e}")
                messagebox.showerror("Driver Install Error", str(e))
        else:
            self.log_setup("Bundled driver installer not found. Opening download page...")
            driver_url = "https://www.st.com/en/development-tools/stsw-link009.html"
            import webbrowser
            webbrowser.open(driver_url)
            self.log_setup(f"Please download and install the driver from: {driver_url}")
        self.log_setup("After installation, click 'Complete Setup'")
    
    def complete_setup(self):
        if not self.config.get("stlink_path"):
            messagebox.showwarning("Setup Incomplete", 
                                   "Please install ST-Link toolkit first.")
            return
        
        self.config["setup_complete"] = True
        self.save_config()
        self.log_setup("Setup complete! Restarting application...")
        
        self.setup_window.destroy()
        self.create_main_ui()
    
    def create_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        menubar = tk.Menu(self.root, font=(self.font_family, 10))
        self.root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0, font=(self.font_family, 10))
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Run Setup Wizard", command=self.show_setup_wizard)
        settings_menu.add_separator()
        settings_menu.add_command(label="Exit", command=self.root.quit)
        
        main_frame = tk.Frame(self.root, padx=20, pady=20, bg=self.white)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Firmware-Util", 
                 font=(self.font_family, 24, "bold"), bg=self.white, fg=self.black).pack(pady=10)
        
        tk.Label(main_frame, text="SDR Flight Computer Firmware Flasher", 
                 font=(self.font_family, 12), bg=self.white, fg=self.black).pack(pady=(0, 10))
        
        tk.Button(main_frame, text="Refresh Releases", 
                  command=self.fetch_releases, width=20, bg=self.white, 
                  font=(self.font_family, 10)).pack(pady=5)
        
        tk.Label(main_frame, text="Select Firmware Version:", 
                 font=(self.font_family, 11, "bold"), bg=self.white, fg=self.black).pack(pady=(10, 5))
        
        self.release_var = tk.StringVar()
        style = ttk.Style()
        style.configure('TCombobox', font=(self.font_family, 10))
        self.release_combo = ttk.Combobox(main_frame, textvariable=self.release_var, 
                                          width=60, state="readonly", font=(self.font_family, 10))
        self.release_combo.pack(pady=5)
        self.release_combo.bind("<<ComboboxSelected>>", self.on_release_selected)
        
        tk.Label(main_frame, text="Select Binary File:", 
                 font=(self.font_family, 11, "bold"), bg=self.white, fg=self.black).pack(pady=(10, 5))
        
        self.bin_var = tk.StringVar()
        self.bin_combo = ttk.Combobox(main_frame, textvariable=self.bin_var, 
                                      width=60, state="readonly", font=(self.font_family, 10))
        self.bin_combo.pack(pady=5)
        
        button_frame = tk.Frame(main_frame, bg=self.white)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Check Board Connection", 
                  command=self.check_board, width=20, bg=self.white, 
                  font=(self.font_family, 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Flash Firmware", 
                  command=self.flash_firmware, width=20, bg="#FFD700", 
                  fg="#000000", font=(self.font_family, 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.status_text = scrolledtext.ScrolledText(main_frame, height=10, width=90, 
                                                     bg=self.light_gray, font=(self.font_family, 9))
        self.status_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.fetch_releases()
    
    def log_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def fetch_releases(self):
        self.log_status("Fetching releases from GitHub...")
        
        try:
            url = "https://api.github.com/repos/SunDevilRocketry/Flight-Computer-Firmware/releases"
            response = requests.get(url)
            response.raise_for_status()
            
            all_releases = response.json()
            self.releases = []
            # Updated regex to match vX.X.X and vX.X.X-XXX
            semver_pattern = re.compile(r'^v?\d+\.\d+\.\d+(?:-\d+)?$')
            releases = []
            prereleases = []
            for release in all_releases:
                tag = release.get('tag_name', '')
                
                if not semver_pattern.match(tag):
                    self.log_status(f"Skipping {tag} (not semantic versioning)")
                    continue
                
                bin_assets = [asset for asset in release.get('assets', []) 
                              if asset['name'].endswith('.bin')]
                
                if not bin_assets:
                    self.log_status(f"Skipping {tag} (no .bin files)")
                    continue
                
                release['bin_assets'] = bin_assets
                if release.get('prerelease') or '-' in tag:
                    prereleases.append(release)
                else:
                    releases.append(release)
            
            # Sort releases and prereleases by version (descending)
            def version_key(r):
                # Remove 'v' and split by '-' for prerelease
                base = r['tag_name'].lstrip('v')
                parts = base.split('-')
                nums = tuple(map(int, parts[0].split('.')))
                pre = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                return (*nums, -pre)  # prerelease comes after release
            
            releases.sort(key=version_key, reverse=True)
            prereleases.sort(key=version_key, reverse=True)
            
            # Insert latest prerelease right after latest release
            combined = releases[:1] + prereleases[:1] + releases[1:] + prereleases[1:]
            self.releases = combined
            
            release_names = [f"{r['tag_name']} - {r['name']}" + 
                           (" (Pre-release)" if r.get('prerelease') or '-' in r['tag_name'] else "") 
                           for r in self.releases]
            
            self.release_combo['values'] = release_names
            
            if release_names:
                self.release_combo.current(0)
                self.on_release_selected(None)
                self.log_status(f"Loaded {len(self.releases)} releases")
            else:
                self.log_status("No valid releases found")
                
        except Exception as e:
            self.log_status(f"Error fetching releases: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch releases: {str(e)}")
    
    def on_release_selected(self, event):
        index = self.release_combo.current()
        if index >= 0:
            self.selected_release = self.releases[index]
            bin_names = [asset['name'] for asset in self.selected_release['bin_assets']]
            self.bin_combo['values'] = bin_names
            
            if bin_names:
                self.bin_combo.current(0)
                self.log_status(f"Selected: {self.selected_release['tag_name']}")
    
    def check_board(self):
        self.log_status("Checking for connected ST-Link board...")
        
        try:
            st_flash = self.get_stflash_executable()
            if not st_flash:
                self.log_status("✗ st-flash not found. Please run setup from Settings menu.")
                return
            
            result = subprocess.run([st_flash, "--version"], 
                                    capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log_status(f"ST-Flash version: {result.stdout.strip()}")
            
            result = subprocess.run([st_flash, "--probe"], 
                                    capture_output=True, text=True, timeout=10)
            
            if "Flash size" in result.stdout or "Flash size" in result.stderr:
                self.log_status("✓ Board detected successfully!")
                self.log_status(result.stdout + result.stderr)
            else:
                self.log_status("✗ No board detected")
                self.log_status(result.stdout + result.stderr)
                
        except subprocess.TimeoutExpired:
            self.log_status("✗ Command timed out")
        except FileNotFoundError:
            self.log_status("✗ st-flash.exe not found. Please complete setup.")
        except Exception as e:
            self.log_status(f"✗ Error: {str(e)}")
    
    def flash_firmware(self):
        if not self.selected_release:
            messagebox.showwarning("No Release Selected", 
                                   "Please select a firmware version first.")
            return
        
        bin_index = self.bin_combo.current()
        if bin_index < 0:
            messagebox.showwarning("No Binary Selected", 
                                   "Please select a binary file first.")
            return
        
        bin_asset = self.selected_release['bin_assets'][bin_index]
        
        Thread(target=self._flash_firmware_thread, args=(bin_asset,), daemon=True).start()
    
    def _flash_firmware_thread(self, bin_asset):
        try:
            self.log_status(f"Downloading {bin_asset['name']}...")
            
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)
            
            bin_path = download_dir / bin_asset['name']
            
            response = requests.get(bin_asset['browser_download_url'], stream=True)
            response.raise_for_status()
            
            with open(bin_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.log_status(f"Downloaded to {bin_path}")
            self.log_status("Flashing firmware to board...")
            
            st_flash = self.get_stflash_executable()
            if not st_flash:
                self.log_status("✗ st-flash not found. Please run setup from Settings menu.")
                messagebox.showerror("Error", "st-flash not found. Please complete setup.")
                return
            
            result = subprocess.run([st_flash, "write", str(bin_path), "0x08000000"],
                                    capture_output=True, text=True, timeout=60)
            
            self.log_status(result.stdout)
            
            if result.returncode == 0:
                self.log_status("✓ Firmware flashed successfully!")
                messagebox.showinfo("Success", "Firmware flashed successfully!")
            else:
                self.log_status(f"✗ Flash failed with code {result.returncode}")
                self.log_status(result.stderr)
                messagebox.showerror("Flash Failed", result.stderr)
                
        except subprocess.TimeoutExpired:
            self.log_status("✗ Flash operation timed out")
            messagebox.showerror("Timeout", "Flash operation timed out")
        except Exception as e:
            self.log_status(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", str(e))

def main():
    root = tk.Tk()
    app = FirmwareFlasher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
