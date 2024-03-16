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

for file_name in T2_LA.py T1_TS.py T3_DB.py; do
	for pid in $(
		ps -ax -o pid,command | 
		grep "$parent_path/Topics/$file_name" | 
		grep -v "grep" | 
		awk '{print $1}'
	); do
		sudo kill -9 $pid
		bash $parent_path/Logger/Log.sh "[$pid] has been killed"
	done
done