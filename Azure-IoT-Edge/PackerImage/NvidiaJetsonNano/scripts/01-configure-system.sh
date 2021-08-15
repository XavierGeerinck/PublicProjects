#!/bin/bash
# Hostname Configuration
# Note: escape since EOF allows command substitution. We can turn this of by using 'EOF'
echo "Setting Hostname"
cat << EOF > /etc/init.d/configure-hostname.sh
#!/bin/bash
# Created on $(date)
MAC_ADDR=\$(ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | sed -En "s/:/-/gp")
echo \$MAC_ADDR > /etc/hostname
EOF

# DNS Configuration
echo "Setting DNS"
cat << EOF > /etc/resolv.conf
# Created on $(date)
nameserver 1.1.1.1
nameserver 1.0.0.1
EOF

# Dependencies
sudo apt-get update
# sudo apt-get upgrade -y
sudo apt-get -y -qq install curl wget git vim apt-transport-https ca-certificates