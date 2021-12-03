#!/bin/bash

# Move backup GPT header to end of disk
sgdisk --move-second-header /dev/mmcblk0

# Get root partition name i.e partition No. 1
partition_name="$(sgdisk -i 1 /dev/mmcblk0 | grep "Partition name" | cut -d\' -f2)"
partition_type="$(sgdisk -i 1 /dev/mmcblk0 | grep "Partition GUID code:" | cut -d' ' -f4)"
partition_uuid="$(sgdisk -i 1 /dev/mmcblk0 | grep "Partition unique GUID:" | cut -d' ' -f4)"

# Get start sector of the root partition
start_sector="$(cat /sys/block/mmcblk0/mmcblk0p1/start)"

# Delete and re-create the root partition
# This will resize the root partition.
sgdisk -d 1 -n 1:"${start_sector}":0 -c 1:"${partition_name}" -t 1:"${partition_type}" -u 1:"${partition_uuid}" /dev/mmcblk0

# Inform kernel and OS about change in partitin table and root partition size
partprobe /dev/mmcblk0

# Resize filesystem on root partition to consume all un-allocated space on disk
resize2fs /dev/mmcblk0p1