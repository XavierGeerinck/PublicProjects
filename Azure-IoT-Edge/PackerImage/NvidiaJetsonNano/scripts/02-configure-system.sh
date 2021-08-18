#!/bin/bash
##################################################################################
# Config Files
##################################################################################
sudo mkdir -p /etc/rw
sudo touch /etc/rw/rwfirstboot

echo "[RW System] Creating First Boot"
cat << EOF > /etc/systemd/system/rw-boot-first.service
[Unit]
Description=RW First Boot Script
Before=gdm3.service lightdm.service

[Service]
Type=oneshot
ExecStart=/etc/systemd/rw-boot-first.sh

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /etc/systemd/rw-boot-first.sh
#!/bin/bash
# Created on \$(date)

if [ ! -e /etc/rw/rwfirstboot ]; then
	exit 0
fi

# ================================================
# Configure Hostname
# ================================================
echo "[RW System] Configuring Hostname"

HOST_PREFIX=${NETWORKING_HOST_PREFIX:-"node"}
NET_DEVICE=${NETWORKING_NET_DEVICE:="eth0"}
MAC_LAST4=\$(sed -rn "s/^.*([0-9A-F:]{5})$/\1/gi;s/://p" /sys/class/net/\${NET_DEVICE}/address)
MAC_FULL=\$(sed -r "s/://g" /sys/class/net/\${NET_DEVICE}/address)
NEW_HOSTNAME=\${HOST_PREFIX}-\${MAC_FULL:-0000}

# Set hostname that persists across reboot
sudo hostnamectl set-hostname \$NEW_HOSTNAME
sudo hostnamectl --static set-hostname \$NEW_HOSTNAME

# ================================================
# Remove FirstBoot, configuration is done
# ================================================
rm -rf /etc/rw/rwfirstboot
EOF

sudo chmod +x /etc/systemd/rw-boot-first.sh
sudo systemctl enable rw-boot-first

# Issue File to configure per boot information
echo "[System] Creating Boot Info"
cat << EOF > /etc/systemd/system/rw-boot-each.service
[Unit]
Description=Add IP address to /etc/issue
; Finish the first-boot script before the per-boot script
After=rw-boot-first.service
; This script affects state visible after login, so delay login of all kinds
Before=serial-getty@ttyS0.service
Before=graphical-session-pre.target
Before=gdm3.service lightdm.service

[Service]
Type=oneshot
ExecStart=/etc/systemd/rw-boot-each.sh

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /etc/systemd/rw-boot-each.sh
#!/bin/bash
# Created on \$(date)
echo "[System] Configuring /etc/issue"

# ================================================
# Configure /etc/issue
# ================================================
OS_INFO=\$(lsb_release -a 2>&1 | grep Description | cut -d ":" -f2 | sed -e 's/^[[:space:]]*//')
HOST_PREFIX=${NETWORKING_HOST_PREFIX:-"node"}
NET_DEVICE=${NETWORKING_NET_DEVICE:="eth0"}
MAC_FULL=\$(sed -r "s/://g" /sys/class/net/\${NET_DEVICE}/address)
NEW_HOSTNAME=\${HOST_PREFIX}-\${MAC_FULL:-0000}
IPADDRS=\$(ip -4 -br a)
IP=\$(ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')

# Append IP address to /etc/issue
echo "==============================================" > /etc/issue
echo "        Welcome to Nvidia Jetson Nano!        " >> /etc/issue
echo "==============================================" >> /etc/issue
echo "HOST Info:" >> /etc/issue
echo "\$OS_INFO" >> /etc/issue
echo "\$NEW_HOSTNAME" >> /etc/issue
echo "" >> /etc/issue
echo "MAC address:" >> /etc/issue
echo "\$MAC_FULL" >> /etc/issue
echo "" >> /etc/issue
echo "Network Interfaces:" >> /etc/issue
echo "\$IPADDRS" >> /etc/issue
echo "$NETWORKING_NET_DEVICE: \4{$NETWORKING_NET_DEVICE}" >> /etc/issue
echo "==============================================" >> /etc/issue
echo "" >> /etc/issue
EOF

sudo chmod +x /etc/systemd/rw-boot-each.sh
sudo systemctl enable rw-boot-each

##################################################################################
# Configure Network
# Note: this runs in Packer, not on the host
##################################################################################
# DNS Configuration
echo "[System] Setting DNS"
cat << EOF > /etc/resolv.conf
# Created on $(date)
nameserver 1.1.1.1
nameserver 1.0.0.1
EOF

echo "[System] Updating Packages"
sudo apt-get update

# DHCP and IP Configuration with Netplan (Ubuntu > 18.04)
echo "[System] Configuring Network"
sudo apt-get install netplan.io -y

cat << EOF > /etc/netplan/50-cloud-init.yaml
# Created on $(date)
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    ${NETWORKING_NET_DEVICE:="eth0"}:
      addresses: []
      nameservers:
        addresses: [1.1.1.1, 1.0.0.1]
      dhcp4: true
      optional: true
EOF

sudo netplan --debug generate
sudo netplan apply

##################################################################################
# Configure Dependencies
##################################################################################
# Dependencies
sudo apt-get update
# sudo apt-get upgrade -y
sudo apt-get -y -qq install curl wget git vim apt-transport-https ca-certificates

# Use multi-user target
sudo systemctl set-default multi-user.target

# Enable Multicast DNS (mDNS)
# this will allow us to discover our device on the local network
sudo apt install -y avahi-daemon
sudo systemctl enable avahi-daemon 
