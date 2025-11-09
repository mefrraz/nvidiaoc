# NVIDIA GPU Control & Monitor

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A graphical application for Linux to monitor and control NVIDIA GPU settings, including fan speed, core clock, and memory clock offsets.

This project was built from scratch as a Python application using the Tkinter framework for the GUI. It provides a user-friendly interface for common overclocking and monitoring tasks that typically require complex command-line operations.

---

## Features

*   **Real-Time Monitoring:** A dashboard displaying key GPU statistics, updated every two seconds:
    *   GPU Name
    *   Temperature
    *   Fan Speed
    *   GPU Utilization
    *   Core & Memory Clock Speeds
    *   Power Usage
*   **GPU Controls:** Simple sliders to adjust:
    *   **Fan Speed:** Set a manual fan speed percentage.
    *   **Core Clock Offset:** Apply a positive offset to the GPU core clock.
    *   **Memory Clock Offset:** Apply a positive offset to the GPU memory clock.
*   **Profile Management:**
    *   Save your favorite settings as named profiles.
    *   Quickly load and apply profiles from a dropdown menu.
    *   Delete profiles you no longer need.
*   **Command-Line Interface (CLI):**
    *   Apply settings without launching the GUI, perfect for scripting.
    *   Supports `--fan`, `--core`, `--mem`, and `--reset` arguments.
*   **Secure & Robust:**
    *   Does not require running the entire application as root.
    *   Uses `pkexec` and a granular Polkit rule for securely running privileged commands.
    *   Includes dependency checks on startup to guide the user.

---

## Screenshot

*(Placeholder for you to add a screenshot of the application)*

![App Screenshot](placeholder.png)

---

## Installation

This application is for **Linux only** and requires NVIDIA's proprietary drivers to be installed.

### Step 1: Clone the Repository

First, clone this repository to your local machine.

```bash
git clone https://github.com/mefrraz/nvidiaoc.git
cd nvidiaoc
```

### Step 2: Install Dependencies

The application requires Python's Tkinter library for the GUI and `xhost` for handling display server permissions.

**On Debian / Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y python3-tk x11-xserver-utils
```

**On Arch Linux / Cachy OS / Manjaro:**
```bash
sudo pacman -Syu --noconfirm tk xorg-xhost
```

**On Fedora / CentOS / RHEL:**
```bash
sudo dnf install -y python3-tkinter xorg-xhost
```

### Step 3: Configure Polkit Permissions (Crucial Step!)

To allow the application to change GPU settings without running the entire program as root, you must create a Polkit rule.

1.  **Create the rule file** with a text editor (e.g., `nano`):

    ```bash
    sudo nano /etc/polkit-1/rules.d/90-nvidiaoc.rules
    ```

2.  **Paste the following content** into the file. The path is already configured for your current directory.

    ```javascript
    // /etc/polkit-1/rules.d/90-nvidiaoc.rules
    polkit.addRule(function(action, subject) {
        if (action.id == "org.freedesktop.policykit.exec" &&
            action.lookup("program") == "/home/veezus/gemini/nvidiaoc2/pkexec_wrapper.sh") {
            
            // Require administrator authentication for this specific action
            return polkit.Result.AUTH_ADMIN;
        }
    });
    ```
    
    > **⚠️ Aviso Importante:** O caminho no ficheiro da regra acima (`/home/veezus/gemini/nvidiaoc2/pkexec_wrapper.sh`) está configurado para a sua pasta atual. Se mover o projeto para outro diretório, **terá de editar este ficheiro de regra** com o novo caminho.

3.  **Restart the Polkit service** to apply the new rule:
    ```bash
    sudo systemctl restart polkit.service
    ```

---

## Usage

### GUI Mode

To run the graphical application, simply execute the main Python script:

```bash
python3 nvidia_control.py
```

### Command-Line Mode

You can apply settings directly from the terminal.

**Examples:**
*   Set fan speed to 75%:
    ```bash
    python3 nvidia_control.py --fan 75
    ```
*   Set core and memory offsets:
    ```bash
    python3 nvidia_control.py --core 150 --mem 500
    ```
*   Reset all settings to default (puts fan back on auto):
    ```bash
    python3 nvidia_control.py --reset
    ```

---

## Development Story & Challenges

This project was an interesting journey into the complexities of desktop application development on Linux, particularly concerning system permissions.

The core challenge was that `nvidia-settings`, the tool used to control the GPU, requires root privileges to modify hardware state. However, it *also* requires access to the user's active graphical session (the X11 display server) to function. This creates a classic permissions conflict:
*   Running the app with `sudo` is a major security risk and often fails because the `root` user is denied access to the regular user's display.
*   Running as a regular user works for monitoring but fails when trying to apply settings.

The solution involved a multi-layered approach to securely elevate privileges for *only* the specific commands that needed them:

1.  **`pkexec`:** Instead of `sudo`, we use `pkexec` from Polkit (PolicyKit). It is the modern, standard way to handle privilege escalation for specific commands in graphical environments.

2.  **Polkit Rule:** A custom rule was created in `/etc/polkit-1/rules.d/`. This rule explicitly allows the execution of *only* our `pkexec_wrapper.sh` script, and only after authenticating as an administrator. This is far more secure than a broad `sudo` rule, as it strictly limits what can be run as root.

3.  **`xhost`:** To solve the display access issue, the `xhost` command is used to temporarily grant the `root` user permission to connect to the user's display server. This permission is added right before the `pkexec` command runs and is immediately removed afterward in a `try...finally` block to ensure the system is not left in an insecure state.

4.  **Wrapper Script (`pkexec_wrapper.sh`):** When `pkexec` runs a command as root, it does so in a highly sanitized environment, stripping crucial variables like `DISPLAY` and `XAUTHORITY`. The wrapper script's job is to receive these variables as arguments from the main Python application and export them, recreating the necessary graphical environment for `nvidia-settings` to run successfully as root.

Through an iterative process of debugging and refinement, this combination of tools provided a robust and secure solution, allowing the application to function as intended without compromising system security.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.# nvidiaoc
