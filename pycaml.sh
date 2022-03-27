#!/bin/sh

# ファイルの指定がある場合
if [ $# -ge 1 ]; then
    filename=$1
else
    filename="test"
fi
 
python3 py/join.py --file "${filename}"
./min-caml "intermediate/${filename}" -inline 100
python3 py/main.py --file "${filename}"
