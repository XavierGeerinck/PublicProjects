#!/bin/bash

# We configure firstboot on network-pre.target which sets up before any network is set up
# https://unix.stackexchange.com/questions/353597/set-hostname-on-first-boot-before-network-service
echo "[System] Creating First Boot"
cat << EOF > /etc/systemd/system/boot-first.service
[Unit]
Description=First Boot Wizard
DefaultDependencies=no
Conflicts=shutdown.target
After=systemd-remount-fs.service
Before=systemd-sysusers.service sysinit.target shutdown.target
ConditionPathIsReadWrite=/etc
ConditionFirstBoot=yes

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/boot-first.sh
StandardOutput=tty
StandardInput=tty
StandardError=tty

[Install]
WantedBy=sysinit.target
EOF

cat << EOF > /usr/local/sbin/boot-first.sh
#!/bin/bash
# Created on \$(date)

# ================================================
# Configure Hostname
# ================================================
echo "[Systemd] Configuring Hostname"

HOST_PREFIX=${NETWORKING_HOST_PREFIX:-"node"}
NET_DEVICE=${NETWORKING_NET_DEVICE:="eth0"}
MAC_LAST4=\$(sed -rn "s/^.*([0-9A-F:]{5})$/\1/gi;s/://p" /sys/class/net/\${NET_DEVICE}/address)
MAC_FULL=\$(sed -r "s/://g" /sys/class/net/\${NET_DEVICE}/address)
NEW_HOSTNAME=\${HOST_PREFIX}-\${MAC_FULL:-0000}

# Set hostname that persists across reboot
sudo hostnamectl --static set-hostname \$NEW_HOSTNAME
EOF

sudo chmod +x /usr/local/sbin/boot-first.sh
sudo systemctl enable boot-first

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

# Issue File to show IP on login
# See the following for the hook: https://netplan.io/faq/#use-pre-up%2C-post-up%2C-etc.-hook-scripts
echo "[System] Changing /etc/issue"
# /etc/network/if-up.d/mod-etc-issue worked but the below doesn't IP doesn't get assigned
# /etc/networkd-dispatcher/routable.d/add-ip-to-login-screen was old one

echo "[System] Creating Boot Info"
cat << EOF > /etc/systemd/system/boot-info.service
[Unit]
Description=Add IP address to /etc/issue
# After=network-online.target
Wants=sys-devices-virtual-net-${NETWORKING_NET_DEVICE:="eth0"}.device
After=sys-devices-virtual-net-${NETWORKING_NET_DEVICE:="eth0"}.device

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/boot-info.sh
RemainAfterExit=yes
StandardOutput=tty
StandardInput=tty
StandardError=tty

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /usr/local/sbin/boot-info.sh
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
echo "======================================" >> /etc/issue
echo "" >> /etc/issue
EOF

sudo chmod +x /usr/local/sbin/boot-info.sh
sudo systemctl enable boot-info

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
