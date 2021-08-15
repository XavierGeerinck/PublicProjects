#!/usr/bin/env bash
#
# Configure required ssh server options
set -o errexit

# Packer logging
echo "Configuring ssh..."

# Location of sshd configuration file
sshd_conf="/etc/ssh/sshd_config"

# # Set not to perform reverse hostname lookups for connecting hosts
# sed -i -e "/^#*UseDNS/ s/ .*/ no/" \
#        -e "s/^#\(UseDNS*\)/\1/" ${sshd_conf}


# Disallow ssh based logins for root
sed -i -e "/^#*PermitRootLogin/ s/ .*/ no/" \
       -e "s/^#\(PermitRootLogin*\)/\1/" ${sshd_conf}


# # Set to disable password based authentication
# sed -i -e "/^#*PasswordAuthentication/ s/ .*/ no/" \
#        -e "s/^#\(PasswordAuthentication*\)/\1/" ${sshd_conf}

exit 0