# Add Second EBS Volume to EC2

apt update
snap install docker
sleep 10

mkfs.ext4 /dev/nvme1n1
mkdir -p /data
mount /dev/nvme1n1 /data
echo "/dev/nvme1n1  /data   ext4    default,nofail  0   2" >> /etc/fstab

docker volume create --driver local --opt type=none --opt device=/data --opt o=bind jupyter-volume

docker run -d --restart always -p 80:8888 quay.io/jupyter/base-notebook start-notebook.py --NotebookApp.token='my-token'

echo "Completed bootstrapping"