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
crontab -l | grep -v "$parent_path/Data/GetData.py" | grep -v "$parent_path/Data/Backup.sh" | crontab -