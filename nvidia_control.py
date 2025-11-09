import os
import sys
import subprocess
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, font, messagebox
import argparse
import shutil

import gpu
import profiles

# --- Global Configuration ---
LOG_FILE = "nvidiaoc.log"

# --- Logger Setup ---
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Dependency Checkers ---
def check_tkinter():
    """Checks for Tkinter and prompts for installation if not found."""
    try:
        import tkinter
        logging.info("Tkinter found.")
        return True
    except ImportError:
        # This part is kept for robustness for other users
        logging.error("Tkinter is not installed.")
        response = input("Tkinter is not installed. This is required for the GUI. Would you like to try and install it now? [y/N] ").lower()
        if response != 'y': return False
        distro = get_linux_distribution()
        if not distro:
            logging.error("Could not detect Linux distribution. Please install 'python3-tk' (or equivalent) manually.")
            return False
        install_commands = {
            "ubuntu": "sudo apt-get install -y python3-tk", "debian": "sudo apt-get install -y python3-tk",
            "fedora": "sudo dnf install -y python3-tkinter", "arch": "sudo pacman -S --noconfirm tk",
        }
        command = install_commands.get(distro)
        if not command:
            logging.error(f"Unsupported distribution '{distro}'. Please install 'python3-tk' (or equivalent) manually.")
            return False
        try:
            logging.info(f"Running installation command: {command}")
            subprocess.run(command.split(), check=True)
            logging.info("Tkinter installation successful. Please restart the application.")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            logging.error(f"Failed to install Tkinter: {e}. Please install it manually.")
            return False
    return True

def get_linux_distribution():
    """Detects the Linux distribution from /etc/os-release."""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.split("=")[1].strip().lower().replace('"', '')
    except FileNotFoundError:
        return None

def check_system_dependencies():
    """Checks for essential system commands like xhost."""
    if not shutil.which("xhost"):
        logging.error("'xhost' command not found. This is required for GUI operations that need admin rights.")
        print("\n--- Missing Dependency: xhost ---")
        print("The 'xhost' command is required to grant permissions for changing GPU settings.")
        print("Please install it using your system's package manager:")
        print("  - Debian/Ubuntu: sudo apt-get install x11-xserver-utils")
        print("  - Fedora/CentOS: sudo dnf install xorg-xhost")
        print("  - Arch Linux:    sudo pacman -S xorg-xhost")
        print("After installation, please restart the application.")
        return False
    logging.info("System dependency 'xhost' found.")
    return True

# --- Main Application Class (Simplified) ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA GPU Control & Monitor")
        self.root.geometry("850x650")
        self.root.minsize(700, 550)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.monitoring_paused = False
        self.profiles = {}

        main_paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        controls_frame = ttk.Frame(main_paned_window, width=400)
        main_paned_window.add(controls_frame, weight=1)
        right_panel_frame = ttk.Frame(main_paned_window)
        main_paned_window.add(right_panel_frame, weight=1)

        self._create_controls_ui(controls_frame)
        self._create_monitoring_ui(right_panel_frame)
        self._create_profiles_ui(right_panel_frame)
        
        self.load_and_initialize_profiles()
        
        logging.info("Application GUI initialized.")
        self.update_stats()

    def _create_controls_ui(self, parent):
        frame = ttk.LabelFrame(parent, text="GPU Controls", padding=(10, 10))
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Fan Speed - Always visible and enabled
        fan_frame = ttk.Frame(frame)
        fan_frame.pack(fill=tk.X, pady=5)
        ttk.Label(fan_frame, text="Fan Speed (%):").pack(side=tk.LEFT, anchor="w")
        self.fan_speed_label = ttk.Label(fan_frame, text="30%", width=8, anchor="e")
        self.fan_speed_label.pack(side=tk.RIGHT, padx=5)
        self.fan_speed = tk.IntVar(value=30)
        self.fan_slider = ttk.Scale(fan_frame, from_=30, to=100, orient=tk.HORIZONTAL, variable=self.fan_speed, command=lambda v: self.fan_speed_label.config(text=f"{int(float(v))}"))
        self.fan_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Core Clock
        core_frame = ttk.Frame(frame)
        core_frame.pack(fill=tk.X, pady=5)
        ttk.Label(core_frame, text="Core Clock (MHz):").pack(side=tk.LEFT, anchor="w")
        self.core_clock_label = ttk.Label(core_frame, text="+0 MHz", width=8, anchor="e")
        self.core_clock_label.pack(side=tk.RIGHT, padx=5)
        self.core_clock = tk.IntVar(value=0)
        core_slider = ttk.Scale(core_frame, from_=0, to=250, orient=tk.HORIZONTAL, variable=self.core_clock, command=lambda v: self.core_clock_label.config(text=f"+{int(float(v))} MHz"))
        core_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Memory Clock
        mem_frame = ttk.Frame(frame)
        mem_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mem_frame, text="Memory Clock (MHz):").pack(side=tk.LEFT, anchor="w")
        self.mem_clock_label = ttk.Label(mem_frame, text="+0 MHz", width=8, anchor="e")
        self.mem_clock_label.pack(side=tk.RIGHT, padx=5)
        self.mem_clock = tk.IntVar(value=0)
        mem_slider = ttk.Scale(mem_frame, from_=0, to=1000, orient=tk.HORIZONTAL, variable=self.mem_clock, command=lambda v: self.mem_clock_label.config(text=f"+{int(float(v))} MHz"))
        mem_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Action Buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        self.apply_button = ttk.Button(buttons_frame, text="Apply Changes", command=self.apply_settings)
        self.apply_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.reset_button = ttk.Button(buttons_frame, text="Reset to Defaults", command=self.reset_defaults)
        self.reset_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    def _create_monitoring_ui(self, parent):
        frame = ttk.LabelFrame(parent, text="Real-Time Monitoring", padding=(10, 10))
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        warning_label = ttk.Label(frame, text="Warning: Overclocking can be risky. Proceed with caution.", style="Warning.TLabel")
        self.style.configure("Warning.TLabel", foreground="red")
        warning_label.pack(fill=tk.X)
        mono_font = font.Font(family="monospace", size=10)
        self.stats_text = tk.Text(frame, height=10, wrap="word", state=tk.DISABLED, font=mono_font, bg="#f0f0f0")
        self.stats_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.pause_button = ttk.Button(frame, text="Pause Monitor", command=self.toggle_monitoring)
        self.pause_button.pack(fill=tk.X)

    def _create_profiles_ui(self, parent):
        frame = ttk.LabelFrame(parent, text="Profiles", padding=(10, 10))
        frame.pack(fill=tk.X, padx=5, pady=5)
        load_frame = ttk.Frame(frame)
        load_frame.pack(fill=tk.X, pady=5)
        ttk.Label(load_frame, text="Load Profile:").pack(side=tk.LEFT, padx=(0, 5))
        self.profile_combobox = ttk.Combobox(load_frame, values=["Default"], state="readonly")
        self.profile_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.profile_combobox.bind("<<ComboboxSelected>>", self.load_profile)
        save_frame = ttk.Frame(frame)
        save_frame.pack(fill=tk.X, pady=5)
        self.profile_name_entry = ttk.Entry(save_frame)
        self.profile_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.save_profile_button = ttk.Button(save_frame, text="Save", command=self.save_profile)
        self.save_profile_button.pack(side=tk.LEFT)
        self.delete_profile_button = ttk.Button(frame, text="Delete Selected Profile", command=self.delete_profile)
        self.delete_profile_button.pack(fill=tk.X, pady=5)

    def set_ui_busy(self, is_busy):
        state = tk.DISABLED if is_busy else tk.NORMAL
        for widget in [self.apply_button, self.reset_button, self.save_profile_button, self.delete_profile_button, self.fan_slider, self.profile_combobox]:
            widget.config(state=state)
        self.root.config(cursor="watch" if is_busy else "")

    def apply_settings(self, profile_name=None):
        logging.info(f"Applying settings from {'sliders' if not profile_name else f'profile: {profile_name}'}...")
        self.set_ui_busy(True)
        self.root.after(100, self._execute_apply_settings)

    def _execute_apply_settings(self):
        try:
            gpu.apply_all_settings(self.fan_speed.get(), self.core_clock.get(), self.mem_clock.get())
            logging.info("Settings applied. Verifying values in 2 seconds...")
            self.root.after(2000, self.verify_settings)
        except Exception as e:
            logging.error(f"An error occurred while applying settings: {e}")
        finally:
            self.set_ui_busy(False)

    def reset_defaults(self):
        logging.info("Resetting to default settings...")
        self.set_ui_busy(True)
        self.root.after(100, self._execute_reset_defaults)

    def _execute_reset_defaults(self):
        try:
            gpu.reset_all_settings()
            self.set_sliders_from_profile("Default")
            logging.info("Defaults restored. Verifying values in 2 seconds...")
            self.root.after(2000, self.verify_settings)
        except Exception as e:
            logging.error(f"An error occurred while resetting defaults: {e}")
        finally:
            self.set_ui_busy(False)

    def verify_settings(self):
        logging.info("--- Verification Check ---")
        stats = gpu.get_all_stats()
        logging.info(f"Post-change Target Fan Speed: {stats.get('fan_speed', 'N/A')}%")
        logging.info("--- End Verification ---")
        if self.monitoring_paused: self.update_stats_display()
        
    def toggle_monitoring(self):
        self.monitoring_paused = not self.monitoring_paused
        self.pause_button.config(text="Resume Monitor" if self.monitoring_paused else "Pause Monitor")
        logging.info(f"Monitoring {'paused' if self.monitoring_paused else 'resumed'}.")
        if not self.monitoring_paused: self.update_stats()

    def update_stats_display(self):
        stats = gpu.get_all_stats()
        stats_str = (
            f"{'GPU Name':<18}: {stats.get('name', 'N/A')}\n"
            f"{'Temperature':<18}: {stats.get('temperature', 'N/A')} °C\n"
            f"{'GPU Usage':<18}: {stats.get('utilization', 'N/A')} %\n"
            f"{'Core Clock':<18}: {stats.get('core_clock', 'N/A')} MHz\n"
            f"{'Memory Clock':<18}: {stats.get('memory_clock', 'N/A')} MHz\n"
            f"{'Power Usage':<18}: {stats.get('power_usage', 'N/A')} W\n"
            f"{'Target Fan Speed':<18}: {stats.get('fan_speed', 'N/A')} %"
        )
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", stats_str)
        self.stats_text.config(state=tk.DISABLED)

    def update_stats(self):
        if self.monitoring_paused: return
        self.update_stats_display()
        self.root.after(2000, self.update_stats)

    def load_and_initialize_profiles(self):
        self.profiles = profiles.load_profiles()
        self.update_profile_combobox()
        self.profile_combobox.set("Default")
        self.set_sliders_from_profile("Default")

    def update_profile_combobox(self):
        self.profile_combobox['values'] = sorted(self.profiles.keys())

    def set_sliders_from_profile(self, profile_name):
        if profile_name not in self.profiles: return
        settings = self.profiles[profile_name]
        self.fan_speed.set(settings.get("fan_speed", 30))
        self.core_clock.set(settings.get("core_clock", 0))
        self.mem_clock.set(settings.get("mem_clock", 0))
        self.fan_speed_label.config(text=f"{self.fan_speed.get()}%")
        self.core_clock_label.config(text=f"+{self.core_clock.get()} MHz")
        self.mem_clock_label.config(text=f"+{self.mem_clock.get()} MHz")

    def save_profile(self):
        profile_name = self.profile_name_entry.get().strip()
        if not profile_name:
            messagebox.showwarning("Invalid Name", "Profile name cannot be empty.")
            return
        if profile_name == "Default":
            messagebox.showwarning("Invalid Name", "Cannot overwrite the Default profile.")
            return
        new_profile = {
            "fan_speed": self.fan_speed.get(), "core_clock": self.core_clock.get(), "mem_clock": self.mem_clock.get()
        }
        self.profiles[profile_name] = new_profile
        if profiles.save_profiles(self.profiles):
            self.update_profile_combobox()
            self.profile_combobox.set(profile_name)
            self.profile_name_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")
        else:
            messagebox.showerror("Error", "Failed to save profiles to file.")

    def load_profile(self, event=None):
        profile_name = self.profile_combobox.get()
        logging.info(f"Loading and applying profile '{profile_name}'...")
        self.set_sliders_from_profile(profile_name)
        self.apply_settings(profile_name=profile_name)

    def delete_profile(self):
        profile_name = self.profile_combobox.get()
        if profile_name == "Default":
            messagebox.showwarning("Cannot Delete", "The Default profile cannot be deleted.")
            return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the profile '{profile_name}'?"):
            if profile_name in self.profiles:
                del self.profiles[profile_name]
                if profiles.save_profiles(self.profiles):
                    self.update_profile_combobox()
                    self.profile_combobox.set("Default")
                    self.set_sliders_from_profile("Default")
                    messagebox.showinfo("Success", f"Profile '{profile_name}' deleted.")
                else:
                    messagebox.showerror("Error", "Failed to save changes after deleting profile.")

# --- CLI and Main Execution ---
def cli_main(args):
    logging.info("Running in Command-Line Interface mode.")
    if not check_system_dependencies(): sys.exit(1)
    if args.reset:
        logging.info("Resetting GPU settings to defaults.")
        gpu.reset_all_settings()
        logging.info("GPU settings have been reset.")
        return
    if args.fan is not None or args.core is not None or args.mem is not None:
        # Get current values for any unset arguments to avoid resetting them
        # This is a bit complex, so for now we just apply what's given
        # and the fan will be set to manual.
        fan = args.fan if args.fan is not None else 30 # A safe default
        core = args.core if args.core is not None else 0
        mem = args.mem if args.mem is not None else 0
        gpu.apply_all_settings(fan, core, mem)
    logging.info("CLI operations complete.")

def main():
    logging.info("Starting NVIDIA GPU Control & Monitor.")
    parser = argparse.ArgumentParser(description="Control and monitor NVIDIA GPUs.")
    parser.add_argument("--fan", type=int, help="Set fan speed in percent (e.g., 75).")
    parser.add_argument("--core", type=int, help="Set core clock offset in MHz (e.g., 150).")
    parser.add_argument("--mem", type=int, help="Set memory clock offset in MHz (e.g., 750).")
    parser.add_argument("--reset", action="store_true", help="Reset all settings to default.")
    args = parser.parse_args()

    is_cli_mode = any(arg is not None for arg in [args.fan, args.core, args.mem]) or args.reset

    if not is_cli_mode:
        if not check_tkinter() or not check_system_dependencies():
            logging.error("Cannot start GUI due to missing dependencies. Exiting.")
            sys.exit(1)
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    else:
        cli_main(args)
        sys.exit(0)

if __name__ == "__main__":
    main()