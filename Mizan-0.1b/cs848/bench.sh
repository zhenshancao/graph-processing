#!/bin/bash
WORKERS=4

#./premizan.sh google.txt ${WORKERS} 1
./sssp.sh google.txt ${WORKERS} 1 0
./sssp.sh google.txt ${WORKERS} 1 0
./sssp.sh google.txt ${WORKERS} 1 0

./sssp.sh google.txt ${WORKERS} 2 0
./sssp.sh google.txt ${WORKERS} 2 0
./sssp.sh google.txt ${WORKERS} 2 0

./pagerank.sh google.txt ${WORKERS} 1
./pagerank.sh google.txt ${WORKERS} 1
./pagerank.sh google.txt ${WORKERS} 1

./pagerank.sh google.txt ${WORKERS} 2
./pagerank.sh google.txt ${WORKERS} 2
./pagerank.sh google.txt ${WORKERS} 2

#./premizan.sh amazon.txt ${WORKERS} 1
./sssp.sh amazon.txt ${WORKERS} 1 0
./sssp.sh amazon.txt ${WORKERS} 1 0
./sssp.sh amazon.txt ${WORKERS} 1 0

./sssp.sh amazon.txt ${WORKERS} 2 0
./sssp.sh amazon.txt ${WORKERS} 2 0
./sssp.sh amazon.txt ${WORKERS} 2 0

./pagerank.sh amazon.txt ${WORKERS} 1
./pagerank.sh amazon.txt ${WORKERS} 1
./pagerank.sh amazon.txt ${WORKERS} 1

./pagerank.sh amazon.txt ${WORKERS} 2
./pagerank.sh amazon.txt ${WORKERS} 2
./pagerank.sh amazon.txt ${WORKERS} 2

#./premizan.sh patents.txt ${WORKERS} 1
./sssp.sh patents.txt ${WORKERS} 1 3858241
./sssp.sh patents.txt ${WORKERS} 1 3858241
./sssp.sh patents.txt ${WORKERS} 1 3858241

./sssp.sh patents.txt ${WORKERS} 2 3858241
./sssp.sh patents.txt ${WORKERS} 2 3858241
./sssp.sh patents.txt ${WORKERS} 2 3858241

./pagerank.sh patents.txt ${WORKERS} 1
./pagerank.sh patents.txt ${WORKERS} 1
./pagerank.sh patents.txt ${WORKERS} 1

./pagerank.sh patents.txt ${WORKERS} 2
./pagerank.sh patents.txt ${WORKERS} 2
./pagerank.sh patents.txt ${WORKERS} 2