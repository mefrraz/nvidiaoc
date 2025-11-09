#!/bin/bash
# Wrapper script to preserve environment variables for pkexec

# The first argument is the DISPLAY
# The second argument is the path to the Xauthority file
export DISPLAY=$1
export XAUTHORITY=$2
shift 2 # Remove the first two arguments

# Check if the Xauthority file exists
if [ -z "$XAUTHORITY" ] || [ ! -f "$XAUTHORITY" ]; then
    echo "Error: Xauthority file not found or not specified in '$XAUTHORITY'" >&2
    exit 1
fi

# Execute the real command
exec "$@"