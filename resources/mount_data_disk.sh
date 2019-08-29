#!/bin/bash
echo -n 'Waiting for disk'
while [ ! -e /dev/sdc ] && [ ! -e /dev/sdc1 ]; do
  echo -n '.'
  sleep 1
done
echo ' done!'
sudo mkdir /datadisk
sudo mount /dev/sdc1 /datadisk
if [ $? -eq 0 ]; then
  sudo chown -v -R localadmin /datadisk/
  exit 0
fi
#echo 'size=50M,type=83' | sudo sfdisk /dev/sdc
sudo mkfs -t ext4 /dev/sdc1
sudo mount /dev/sdc1 /datadisk
sudo chown -v -R localadmin /datadisk/
touch /datadisk/demo
fallocate -l 2k /datadisk/demo
exit 0