#!/bin/bash
PREFIX="m18x"

# Issue File to configure per boot information
echo "[System] Creating Boot Info"
cat << EOF > /etc/systemd/system/$PREFIX-boot-each.service
[Unit]
Description=Add IP address to /etc/issue
; Finish the first-boot script before the per-boot script
After=$PREFIX-boot-first.service
; This script affects state visible after login, so delay login of all kinds
Before=serial-getty@ttyS0.service
Before=graphical-session-pre.target
Before=gdm3.service lightdm.service

[Service]
Type=oneshot
ExecStart=/etc/systemd/$PREFIX-boot-each.sh

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /etc/systemd/$PREFIX-boot-each.sh
#!/bin/bash
# Created on \$(date)
echo "[System] Configuring /etc/issue"

# Scripts
/etc/$PREFIX/files/configure-etc-issue.sh
EOF

sudo chmod +x /etc/systemd/$PREFIX-boot-each.sh
sudo systemctl enable $PREFIX-boot-each

