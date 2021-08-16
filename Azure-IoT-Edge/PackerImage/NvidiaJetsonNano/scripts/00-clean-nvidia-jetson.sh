#!/bin/bash
# # Set DNS first since else we can't apt update
# echo "Setting DNS"
# cat << EOF > /etc/resolv.conf
# # Created on $(date)
# nameserver 1.1.1.1
# nameserver 1.0.0.1
# EOF

echo "[Jetson Nano] Fixing Sources"
# # Fix sources list (t186 = TX2; t194 = AGX Xavier; t210 = Nano or TX1)
# # https://forums.developer.nvidia.com/t/upgrade-to-r32-4-not-possible-via-ota/125881
sed -i "s|https://repo.download.nvidia.com/jetson/<SOC>|https://repo.download.nvidia.com/jetson/t210|g" /etc/apt/sources.list.d/nvidia-l4t-apt-source.list
 
# echo "[Jetson Nano] Removing the Display Manager"
# sudo systemctl set-default multi-user.target

# echo "[Jetson Nano] Disable Splash Screen"
# sudo nvidia-xconfig --no-logo
# sed -i "s|    Driver      \"nvidia\"|    Driver      \"nvidia\"\n    Option      \"NoLogo\"|g" /etc/X11/xorg.conf

echo "[Jetson Nano] Removing unneeded dev libraries and samples"
sudo rm -rf /usr/local/cuda/samples \
    /usr/src/cudnn_samples_* \
    /usr/src/tensorrt/data \
    /usr/src/tensorrt/samples \
    /usr/share/visionworks* ~/VisionWorks-SFM*Samples \
    /opt/nvidia/deepstream/deepstream*/samples	

echo "[Jetson Nano] Removing Software"
sudo apt-get remove thunderbird libreoffice-* -y
