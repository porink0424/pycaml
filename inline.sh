#!/bin/sh

# min-camlにおけるinlineの最適値を求めるためのshellscript

for i in `seq 1 150`
do
    python3 py/join.py --file minrt
    ./min-caml intermediate/minrt -inline "${i}"
    python3 py/main.py --file minrt

    cd ..

    cd simulator
    cd asm
    python3 asm.py ../../compiler/asm/minrt.s -b
    cd ..

    echo $i >> inline.txt
    ./sim-lite minrt --sld asm/test-codes/contest.sld >> inline.txt
    cd ..
    cd compiler
done
