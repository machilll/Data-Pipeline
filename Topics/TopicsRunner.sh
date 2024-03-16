#!/bin/bash

_get_parent () {
    path=$1
    depth=$2
    for i in $(seq 1 $depth); do
        path=$(dirname $path)
    done
    echo $path
    return 0
}

parent_path=$(_get_parent $(readlink -f $0) 2)
source "$parent_path/.venv/bin/activate"
bash $parent_path/Logger/Log.sh "Running Python Files"
nohup python3 "$parent_path/topics/T1_TS.py" 1>/dev/null 2>/dev/null &
nohup python3 "$parent_path/topics/T2_LA.py" 1>/dev/null 2>/dev/null &
nohup python3 "$parent_path/topics/T3_DB.py" 1>/dev/null 2>/dev/null &
bash $parent_path/Logger/Log.sh "Run Successful"