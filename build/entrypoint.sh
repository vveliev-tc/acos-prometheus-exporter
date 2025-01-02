#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print all executed commands
set -x

source /root/.local/share/virtualenvs/*/bin/activate

exec python /app/acos_exporter.py "$@"
