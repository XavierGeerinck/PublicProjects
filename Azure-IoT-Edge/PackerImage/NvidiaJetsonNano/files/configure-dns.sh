#!/bin/bash

# DNS Configuration
echo "[System] Setting DNS"
cat << EOF > /etc/resolv.conf
# Created on $(date)
nameserver 1.1.1.1
nameserver 1.0.0.1
EOF