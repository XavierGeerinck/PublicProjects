#!/bin/bash
# echo "[Ubuntu] Removing GUI"
# # Remove X11 by removing libx11 where everything depends on
# echo "[Ubuntu] Removing X11"
# sudo apt-get remove --auto-remove --purge 'libx11-.*' -y
# sudo apt-get autoremove --purge -y

# echo "[Ubuntu] Removing all oprhaned files"
# sudo apt-get install deborphan -y
# deborphan -sz
# sudo apt-get remove --purge $(deborphan)

# # Remove unnecessary packages
# sudo apt-get autoremove -y
# sudo apt autoclean

# In Ubuntu > 15.05 we have to change systemd from graphical to multi-user
echo "[Ubuntu] Changing to multi-user target"
sudo systemctl set-default multi-user.target

# Stop the display manager, note that lightdm.service is marked as "static"
# this means that we cannot disable it since there is no target in multi-user.targer or graphical.target
# the way to disable it is by masking it
# see: https://forums.developer.nvidia.com/t/how-to-disable-tx1s-desktop/50343/14
echo "[Ubuntu] Disabling the Display Manager"
sudo systemctl stop lightdm.service
sudo systemctl mask lightdm.service

# # Set Grub on text mode
# echo "[Grub] Setting Grub File to Console"
# cat << EOF > /etc/default/grub
# # Created on $(date)
# GRUB_CMDLINE_LINUX="text"
# GRUB_TERMINAL=console
# EOF

# Rebuild Grub
# echo "[Grub] Rebuilding Grub"
# sudo update-grub