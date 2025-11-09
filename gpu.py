import subprocess
import logging
import os

def run_command(command, capture_output=True, text=True, check=False, env=None):
    """A wrapper around subprocess.run to handle command execution and logging."""
    logging.info(f"Executing command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=text,
            check=check,
            env=env
        )
        if result.returncode != 0:
            logging.error(f"Command failed with exit code {result.returncode}")
            logging.error(f"Stderr: {result.stderr.strip()}")
            logging.error(f"Stdout: {result.stdout.strip()}")
        return result
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}. Please ensure it is installed and in your PATH.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while running command: {' '.join(command)}. Error: {e}")
        return None

def get_gpu_name():
    """Gets the GPU product name."""
    result = run_command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    return result.stdout.strip() if result and result.returncode == 0 else "N/A"

def get_gpu_temperature():
    """Gets the GPU temperature."""
    result = run_command(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"])
    return result.stdout.strip() if result and result.returncode == 0 else "N/A"

def get_gpu_utilization():
    """Gets the GPU utilization percentage."""
    result = run_command(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader"])
    return result.stdout.strip().replace(" %", "") if result and result.returncode == 0 else "N/A"

def get_core_clock():
    """Gets the current GPU core clock speed."""
    result = run_command(["nvidia-smi", "--query-gpu=clocks.gr", "--format=csv,noheader"])
    return result.stdout.strip().replace(" MHz", "") if result and result.returncode == 0 else "N/A"

def get_memory_clock():
    """Gets the current GPU memory clock speed."""
    result = run_command(["nvidia-smi", "--query-gpu=clocks.mem", "--format=csv,noheader"])
    return result.stdout.strip().replace(" MHz", "") if result and result.returncode == 0 else "N/A"

def get_power_usage():
    """Gets the GPU power usage."""
    result = run_command(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader"])
    if result and result.returncode == 0:
        power = result.stdout.strip()
        return power.replace(" W", "") if "[N/A]" not in power else "N/A"
    return "N/A"

def get_fan_speed_from_settings():
    """
    Gets the target fan speed from nvidia-settings.
    This reflects the value set by the user, not the physical speed.
    """
    # This command reads the value. It doesn't require root.
    # The attribute is [fan:0] for the first fan.
    result = run_command([
        "nvidia-settings",
        "-q", "[fan:0]/GPUTargetFanSpeed",
        "-t" # Terse output
    ])
    return result.stdout.strip() if result and result.returncode == 0 else "N/A"

def get_all_stats():
    """Returns a dictionary with all GPU stats."""
    stats = {
        "name": get_gpu_name(),
        "temperature": get_gpu_temperature(),
        "utilization": get_gpu_utilization(),
        "core_clock": get_core_clock(),
        "memory_clock": get_memory_clock(),
        "power_usage": get_power_usage(),
        "fan_speed": get_fan_speed_from_settings(),
    }
    return stats

def get_xauthority_path():
    """Finds the path to the .Xauthority file."""
    xauth_path = os.environ.get("XAUTHORITY")
    if xauth_path and os.path.exists(xauth_path):
        logging.info(f"Found XAUTHORITY path in environment variable: {xauth_path}")
        return xauth_path

    # Fallback for environments where XAUTHORITY is not set (e.g. GDM on Wayland)
    user_id = os.getuid()
    run_user_dir = f"/run/user/{user_id}"
    if os.path.isdir(run_user_dir):
        for item in os.listdir(run_user_dir):
            if "xauth" in item.lower():
                path = os.path.join(run_user_dir, item)
                logging.info(f"Found potential XAUTHORITY file at: {path}")
                return path
    
    logging.warning("Could not automatically determine XAUTHORITY path. Privileged commands may fail.")
    return None

def manage_xhost_permissions(action: str):
    """
    Adds or removes xhost permissions for root to connect to the X server.
    :param action: "add" or "remove"
    """
    if action not in ["add", "remove"]:
        logging.error(f"Invalid action for manage_xhost_permissions: {action}")
        return

    command_map = {
        "add": "xhost +SI:localuser:root",
        "remove": "xhost -SI:localuser:root"
    }
    command = command_map[action].split()
    
    # Pass the current user's environment to ensure DISPLAY is set
    user_env = os.environ.copy()
    
    logging.info(f"Running xhost command: {' '.join(command)}")
    result = run_command(command, env=user_env)
    if result and result.returncode != 0:
        logging.warning(f"xhost command failed. This might be okay if permissions were already set/unset.")
        logging.warning(f"xhost stderr: {result.stderr.strip()}")

def run_privileged_command(command: list):
    """
    Executes a command that requires root privileges (e.g., nvidia-settings -a)
    using the pkexec wrapper script and managing xhost permissions.
    """
    xauth_path = get_xauthority_path()
    display = os.environ.get("DISPLAY")

    if not xauth_path or not display:
        logging.error(f"Cannot execute privileged command without XAUTHORITY ({xauth_path}) or DISPLAY ({display}).")
        return None

    wrapper_path = os.path.join(os.path.dirname(__file__), "pkexec_wrapper.sh")
    if not os.path.exists(wrapper_path):
        logging.error(f"pkexec wrapper not found at {wrapper_path}")
        return None

    full_command = [
        "pkexec",
        wrapper_path,
        display,
        xauth_path,
    ] + command

    manage_xhost_permissions("add")
    try:
        result = run_command(full_command, check=False) # check=False to handle errors manually
        if result and result.returncode == 0:
            logging.info(f"Privileged command successful: {' '.join(command)}")
        else:
            logging.error(f"Privileged command failed: {' '.join(command)}")
        return result
    finally:
        manage_xhost_permissions("remove")


# --- Functions for setting values (will be expanded later) ---

def set_fan_control_state(enable: bool):
    """Enables or disables manual fan control in a single call."""
    value = 1 if enable else 0
    logging.info(f"Setting GPUFanControlState to {value}")
    return run_privileged_command(["nvidia-settings", "-a", f"[gpu:0]/GPUFanControlState={value}"])

def apply_all_settings(fan_speed: int, core_offset: int, mem_offset: int):
    """Applies all overclock settings in a single command to avoid multiple password prompts."""
    logging.info("Constructing single command for all settings.")
    command = [
        "nvidia-settings",
        "-a", f"[gpu:0]/GPUFanControlState=1",
        "-a", f"[fan:0]/GPUTargetFanSpeed={fan_speed}",
        "-a", f"[gpu:0]/GPUGraphicsClockOffset[3]={core_offset}",
        "-a", f"[gpu:0]/GPUMemoryTransferRateOffset[3]={mem_offset}",
    ]
    return run_privileged_command(command)

def reset_all_settings():
    """Resets all overclock settings in a single command."""
    logging.info("Constructing single command to reset all settings.")
    command = [
        "nvidia-settings",
        "-a", f"[gpu:0]/GPUGraphicsClockOffset[3]=0",
        "-a", f"[gpu:0]/GPUMemoryTransferRateOffset[3]=0",
        "-a", f"[gpu:0]/GPUFanControlState=0", # Set to auto
    ]
    return run_privileged_command(command)


