#!/bin/bash
PREFIX="m18x"

sudo mkdir -p /etc/$PREFIX
sudo touch /etc/$PREFIX/firstboot

# The first boot service
# this will trigger our first boot script
echo "[System] Creating First Boot"
cat << EOF > /etc/systemd/system/$PREFIX-boot-first.service
[Unit]
Description=First Boot Script
Before=gdm3.service lightdm.service

[Service]
Type=oneshot
ExecStart=/etc/systemd/$PREFIX-boot-first.sh

[Install]
WantedBy=multi-user.target
EOF

# On first boot, execute this shell script
# it will trigger other scripts
cat << EOF > /etc/systemd/$PREFIX-boot-first.sh
#!/bin/bash
# Created on \$(date)

# Don't run if firstboot file doesn't exist
if [ ! -e /etc/${PREFIX}/firstboot ]; then
    echo "Not running ${PREFIX} first boot since it was already done"
	exit 0
fi

# Ensure scripts are executable
chmod u+x /etc/$PREFIX/files/*

# Scripts
/etc/$PREFIX/files/configure-nvidia-jetson.sh
/etc/$PREFIX/files/configure-hostname.sh $NETWORKING_HOST_PREFIX $NETWORKING_NET_DEVICE
/etc/$PREFIX/files/expand-disk-size.sh
/etc/$PREFIX/files/set-swap-file-size.sh -g 4

# Remove firstboot when we are done with configuration
rm -rf /etc/$PREFIX/firstboot

# Reboot the system
sudo reboot
EOF

sudo chmod +x /etc/systemd/$PREFIX-boot-first.sh
sudo systemctl enable $PREFIX-boot-first