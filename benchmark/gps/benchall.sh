#!/bin/bash

if [ $# -ne 2 ]; then
    echo "usage: $0 workers runs"
    echo ""
    echo "workers: 4, 8, 16, 32, 64, or 128"
    exit -1
fi

WORKERS=$1
RUNS=$2

case ${WORKERS} in
    4)   GRAPHS=(amazon google patents);
         SRC=(0 0 6009554);;  # for SSSP
    8)   GRAPHS=(amazon google patents);
         SRC=(0 0 6009554);;
    16)  GRAPHS=(livejournal orkut arabic twitter uk0705);
         SRC=(0 1 3 0 0);;
    32)  GRAPHS=(livejournal orkut arabic twitter uk0705);
         SRC=(0 1 3 0 0);;
    64)  GRAPHS=(livejournal orkut arabic twitter uk0705);
         SRC=(0 1 3 0 0);;
    128) GRAPHS=(livejournal orkut arabic twitter uk0705);
         SRC=(0 1 3 0 0);;
    *) "Invalid workers"; exit -1;;
esac

#################
# Normal run
#################
# we split the algs up for simplicity
for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./pagerank.sh "${graph}-adj.txt" ${WORKERS} 0
    done
done

for ((j = 0; j <= ${#GRAPHS[@]}; j++)); do
    for ((i = 1; i <= RUNS; i++)); do
        ./sssp.sh "${GRAPHS[j]}-adj.txt" ${WORKERS} 0 ${SRC[j]}
    done
done

for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./wcc.sh "${graph}-adj.txt" ${WORKERS} 0
    done
done

for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./mst.sh "${graph}-mst-adj.txt" ${WORKERS}
    done
done

#./enable-dimest-fix.sh
#for graph in "${GRAPHS[@]}"; do
#    for ((i = 1; i <= RUNS; i++)); do
#        ./dimest.sh "${graph}-adj.txt" ${WORKERS} 0
#    done
#done
#./disable-dimest-fix.sh

#################
# LALP Run
#################
for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./pagerank.sh "${graph}-adj.txt" ${WORKERS} 1
    done
done

for ((j = 0; j <= ${#GRAPHS[@]}; j++)); do
    for ((i = 1; i <= RUNS; i++)); do
        ./sssp.sh "${GRAPHS[j]}-adj.txt" ${WORKERS} 1 ${SRC[j]}
    done
done

for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./wcc.sh "${graph}-adj.txt" ${WORKERS} 1
    done
done

# no MST

#./enable-dimest-fix.sh
#for graph in "${GRAPHS[@]}"; do
#    for ((i = 1; i <= RUNS; i++)); do
#        ./dimest.sh "${graph}-adj.txt" ${WORKERS} 0
#    done
#done
#./disable-dimest-fix.sh

#################
# Dynamic Run
#################
for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./pagerank.sh "${graph}-adj.txt" ${WORKERS} 2
    done
done

for ((j = 0; j <= ${#GRAPHS[@]}; j++)); do
    for ((i = 1; i <= RUNS; i++)); do
        ./sssp.sh "${GRAPHS[j]}-adj.txt" ${WORKERS} 2 ${SRC[j]}
    done
done

for graph in "${GRAPHS[@]}"; do
    for ((i = 1; i <= RUNS; i++)); do
        ./wcc.sh "${graph}-adj.txt" ${WORKERS} 2
    done
done

# no MST

#./enable-dimest-fix.sh
#for graph in "${GRAPHS[@]}"; do
#    for ((i = 1; i <= RUNS; i++)); do
#        ./dimest.sh "${graph}-adj.txt" ${WORKERS} 0
#    done
#done
#./disable-dimest-fix.sh