#!/bin/bash

set -e

echo ">>> Creating virtual environment at ~/tollmachter-env..."
python3 -m venv ~/tollmachter-env
source ~/tollmachter-env/bin/activate

echo ">>> Installing dependencies from requirements.txt..."
pip install -r "$(dirname "$0")/requirements.txt"

echo ">>> Copying systemd service file..."
sudo cp "$(dirname "$0")/system/offline_translator.service" /etc/systemd/system/offline_translator.service

echo ">>> Reloading systemd..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo ">>> Enabling and starting the service..."
sudo systemctl enable offline_translator.service
sudo systemctl start offline_translator.service

echo "Setup complete. The service is now running."
