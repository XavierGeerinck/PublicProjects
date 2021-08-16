#!/bin/bash

# Hostname Configuration
# Note: escape since EOF allows command substitution. We can turn this of by using 'EOF'
echo "[System] Setting Hostname"
cat << EOF > /etc/init.d/configure-hostname.sh
#!/bin/bash
# Created on $(date)
MAC_ADDR=\$(ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | sed -En "s/:/-/gp")
echo \$MAC_ADDR > /etc/hostname
EOF

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
  renderer: networkd
  ethernets:
    eth0:
      addresses: []
      nameservers:
        addresses: [1.1.1.1, 1.0.0.1]
      dhcp4: true
      optional: true
EOF

sudo netplan apply

# Issue File to show IP on login
# See the following for the hook: https://netplan.io/faq/#use-pre-up%2C-post-up%2C-etc.-hook-scripts
echo "[System] Changing /etc/issue"
cat << EOF > /etc/networkd-dispatcher/routable.d/add-ip-to-login-screen
#!/bin/sh
# Created on $(date)
if [ "\$METHOD" = loopback ]; then
    exit 0
fi

# Only run from ifup.
if [ "\$MODE" != start ]; then
    exit 0
fi

HOSTINFO=\$(/usr/bin/lsb_release -a 2>&1 | grep Description | /usr/bin/cut -d ":" -f2 | /usr/bin/tr -d [:blank:])
MACADDR=\$(ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | sed -En "s/:/-/gp")
IPADDRS=\$(/usr/sbin/ip -4 -br a)

# First time, back up /etc/issue
if [ ! -f /etc/issue.orig ]
then
  cp /etc/issue /etc/issue.orig
fi

# "Reset" /etc/issue to original state
cp /etc/issue.orig /etc/issue


# Append IP address to /etc/issue
echo "======================================" >> /etc/issue
echo "    Welcome to Nvidia Jetson Nano!    " >> /etc/issue
echo "======================================" >> /etc/issue
echo "HOST Info:" >> /etc/issue
echo "\$HOSTINFO" >> /etc/issue
echo "" >> /etc/issue
echo "MAC address:" >> /etc/issue
echo "\$MACADDR" >> /etc/issue
echo "" >> /etc/issue
echo "Network Interfaces:" >> /etc/issue
echo "\$IPADDRS" >> /etc/issue
echo "======================================" >> /etc/issue
echo "" >> /etc/issue
EOF

# Make the files executable
sudo chmod +x /etc/init.d/configure-hostname.sh
sudo chmod +x /etc/networkd-dispatcher/routable.d/add-ip-to-login-screen

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
