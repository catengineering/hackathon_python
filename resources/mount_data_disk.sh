#!/bin/bash
echo -n 'Waiting for disk'
while [ ! -e /dev/xvdf ] && [ ! -e /dev/xvdf1 ]; do
  echo -n '.'
  sleep 1
done
echo ' done!'
sudo mkdir /datadisk
sudo mount /dev/xvdf1 /datadisk
if [ $? -eq 0 ]; then
  sudo chown -v -R ec2-user /datadisk/
  exit 0
fi
echo 'size=50M,type=83' | sudo sfdisk /dev/xvdf
sudo mkfs -t ext4 /dev/xvdf1
sudo mount /dev/xvdf1 /datadisk
sudo chown -v -R ec2-user /datadisk/
touch /datadisk/demo
fallocate -l 2k /datadisk/demo
exit 0