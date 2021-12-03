#!/bin/bash

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