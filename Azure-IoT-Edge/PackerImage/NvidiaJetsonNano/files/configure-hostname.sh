#!/bin/bash
# ================================================
# Configure Hostname
# ================================================
echo "[System] Configuring Hostname"

NETWORKING_HOST_PREFIX=$1
NETWORKING_NET_DEVICE=$21

HOST_PREFIX=${NETWORKING_HOST_PREFIX:-"node"}
NET_DEVICE=${NETWORKING_NET_DEVICE:="eth0"}
MAC_LAST4=$(sed -rn "s/^.*([0-9A-F:]{5})$/\1/gi;s/://p" /sys/class/net/${NET_DEVICE}/address)
MAC_FULL=$(sed -r "s/://g" /sys/class/net/${NET_DEVICE}/address)
NEW_HOSTNAME=${HOST_PREFIX}-${MAC_FULL:-0000}

# Set hostname that persists across reboot
sudo hostnamectl set-hostname $NEW_HOSTNAME
sudo hostnamectl --static set-hostname $NEW_HOSTNAME

# Restart avahi daemon to ensure hostname is updated on network
sudo systemctl restart avahi-daemon