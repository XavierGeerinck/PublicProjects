#!/bin/bash

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
echo "* $NETWORKING_NET_DEVICE: \4{$NETWORKING_NET_DEVICE}" >> /etc/issue
echo "* $NETWORKING_NET_DEVICE: \6{$NETWORKING_NET_DEVICE}" >> /etc/issue
echo "==============================================" >> /etc/issue
echo "" >> /etc/issue