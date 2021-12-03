#!/bin/bash

##################################################################################
# Configure Dependencies
##################################################################################
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
