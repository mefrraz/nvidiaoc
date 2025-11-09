import json
import logging
import os

PROFILES_FILE = "profiles.json"

def get_default_profile():
    """Returns the default profile settings."""
    return {
        "Default": {
            "fan_speed": 60,
            "core_clock": 150,
            "mem_clock": 750
        }
    }

def load_profiles():
    """
    Loads profiles from profiles.json.
    If the file doesn't exist, it creates it with a default profile.
    """
    if not os.path.exists(PROFILES_FILE):
        logging.info(f"'{PROFILES_FILE}' not found. Creating with default profile.")
        profiles = get_default_profile()
        save_profiles(profiles)
        return profiles
    
    try:
        with open(PROFILES_FILE, 'r') as f:
            profiles = json.load(f)
            # Ensure the default profile is always present
            if "Default" not in profiles:
                profiles["Default"] = get_default_profile()["Default"]
            logging.info(f"Successfully loaded profiles from '{PROFILES_FILE}'.")
            return profiles
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error reading '{PROFILES_FILE}': {e}. Loading default profile.")
        return get_default_profile()

def save_profiles(profiles):
    """Saves the profiles dictionary to profiles.json."""
    try:
        with open(PROFILES_FILE, 'w') as f:
            json.dump(profiles, f, indent=4)
        logging.info(f"Profiles saved to '{PROFILES_FILE}'.")
        return True
    except IOError as e:
        logging.error(f"Error writing to '{PROFILES_FILE}': {e}.")
        return False
