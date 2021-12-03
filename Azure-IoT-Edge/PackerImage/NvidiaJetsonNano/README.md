# Nvidia Jetson Nano

## Building

```bash
sudo packer build -var 'dps_scope_id=DPS_SCOPE' -var 'dps_group_enrollment_key=DPS_GROUP_ENROLLMENT_KEY' jetson-azure-iot-edge.json
```

## Help

```bash
# On error building packer, run the below
sudo apt install --reinstall qemu-user-static 
```

### Resizing Image 

You can resize the image: sudo fdisk <DEV> -> d -> 1 -> n -> 1 -> use defaults -> No -> w -> q -> reboot -> sudo resize2fs /dev/mmcblk0p1

https://www.youtube.com/watch?v=UxX-qHQXQ4Q&ab_channel=RobocarStore
