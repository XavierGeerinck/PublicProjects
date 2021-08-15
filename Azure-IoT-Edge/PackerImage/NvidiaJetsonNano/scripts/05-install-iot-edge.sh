#!/bin/bash
# Configure IoT Edge
set -o errexit

# Set verbose/quiet output based on env var configured in Packer template
[ "${DEBUG:-false}" = true ] && redirect="/dev/stdout" || redirect="/dev/null"

# Logging
echo "Installing Azure IoT Edge"

# Installation
# Note: escape since EOF allows command substitution. We can turn this of by using 'EOF'
# however in this case we use it since we need to inject our key
cat << EOF > /etc/init.d/configure-iot-edge.sh
#!/bin/bash
# Created on $(date)
# DPS Enrollment Group Key
DPS_GROUP_ENROLLMENT_KEY="$DPS_GROUP_ENROLLMENT_KEY"
DPS_SCOPE_ID="$DPS_SCOPE_ID"

if [[ \$DPS_GROUP_ENROLLMENT_KEY == "NOT_SET_PASS_BY_CLI" || \$DPS_SCOPE_ID == "NOT_SET_PASS_BY_CLI" ]]; then
    echo "Error: DPS Group enrollment key or DPS Scope ID was not set correctly"
    exit 1
fi

# If azure IoT Hub config exists, do not run anymore
if [[ -f "/etc/aziot/config.toml" ]]; then
    echo "Azure IoT is already configured, continuing"
    exit 0
fi


# Get the MAC Address
MAC_ADDR=\$(ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | sed -En "s/:/-/gp")

# Specify the Registration ID
# Note: in our case we utilize the Mac Address
REG_ID=\$MAC_ADDR

# Compute a Derived key
keybytes=\$(echo \$DPS_GROUP_ENROLLMENT_KEY | base64 --decode | xxd -p -u -c 1000)
DERIVED_KEY=\$(echo -n \$REG_ID | openssl sha256 -mac HMAC -macopt hexkey:\$keybytes -binary | base64)

# Configure
wget https://github.com/Azure/iot-edge-config/releases/latest/download/azure-iot-edge-installer.sh -O azure-iot-edge-installer.sh 
chmod +x azure-iot-edge-installer.sh 
sudo -H ./azure-iot-edge-installer.sh -s \$DPS_SCOPE_ID -r \$MAC_ADDR -k \$DERIVED_KEY
rm -rf azure-iot-edge-installer.sh
EOF