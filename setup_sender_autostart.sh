#!/bin/bash

#To Run this script: first change the username and path of the file and run the below two commands
# chmod +x setup_sender_autostart.sh
# ./setup_sender_autostart.sh


# Constants
USER_HOME="/home/URSC"
SCRIPT_PATH="$USER_HOME/sender.py"
START_SCRIPT="$USER_HOME/start_sender.sh"
SERVICE_FILE="/etc/systemd/system/sender.service"
LOG_FILE="$USER_HOME/sender_output.log"
USERNAME="URSC"

# Step 1: Create start_sender.sh
echo "Creating $START_SCRIPT..."
cat <<EOF > "$START_SCRIPT"
#!/bin/bash
cd $USER_HOME
nohup /usr/bin/python3 sender.py > $LOG_FILE 2>&1 &
EOF

chmod +x "$START_SCRIPT"
echo "✅ Created and made executable: $START_SCRIPT"

# Step 2: Create systemd service file
echo "Creating systemd service at $SERVICE_FILE..."
sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=Auto Start Sender Script on Boot
After=network.target

[Service]
ExecStart=$START_SCRIPT
WorkingDirectory=$USER_HOME
User=$USERNAME
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

echo "✅ Created systemd service: sender.service"

# Step 3: Enable and start the service
echo "Reloading systemd, enabling and starting the service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable sender.service
sudo systemctl start sender.service

# Step 4: Show status
echo "✅ Service started. Here's the status:"
sudo systemctl status sender.service --no-pager
