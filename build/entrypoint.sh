#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print all executed commands
set -x

source /root/.local/share/virtualenvs/*/bin/activate

# Set PYTHONPATH to include the parent directory of src
export PYTHONPATH=/app

# Print PYTHONPATH for verification
echo "PYTHONPATH is set to: $PYTHONPATH"

# Pass the correct path to the configuration file
exec python /app/src/app.py "$@"
