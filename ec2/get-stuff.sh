#!/bin/bash

echo "Get stuff from:"
echo "  1) cloud0 (4)"
echo "  2) cld0 (8)"
echo "  3) cw0 (16)"
echo "  4) cx0 (32)"
echo "  5) cy0 (64)"
echo "  6) cz0 (128)"

read -p ">> " response

case ${response} in
    1) name=cloud; nodes=4;;
    2) name=cld; nodes=8;;
    3) name=cw; nodes=16;;
    4) name=cx; nodes=32;;
    5) name=cy; nodes=64;;
    6) name=cz; nodes=128;;
    *) echo "Invalid option!"; exit -1;;
esac

cd "$(dirname "${BASH_SOURCE[0]}")"
source ./get-pem.sh

MASTER_IP=$(aws ec2 describe-instances --filter "Name=tag:Name,Values=${name}0" \
             | grep 'PublicIpAddress\":' | awk '{print $2}' | sed -e 's/",*//g')

#scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "$PEM_KEY" ubuntu@${MASTER_IP}:~/benchmark/giraph/logs/cw*.tar.gz ../results/giraph/${nodes} &
scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "$PEM_KEY" ubuntu@${MASTER_IP}:~/benchmark/giraph/logs/*.tar.gz ../results/giraph/${nodes} &
#scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "$PEM_KEY" ubuntu@${MASTER_IP}:~/benchmark/gps/logs/*.tar.gz ../results/gps/${nodes} &
#scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "$PEM_KEY" ubuntu@${MASTER_IP}:~/benchmark/graphlab/logs/*.tar.gz  ../results/graphlab/${nodes} &
scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "$PEM_KEY" ubuntu@${MASTER_IP}:~/benchmark/mizan/logs/*.tar.gz ../results/mizan/${nodes} &
wait