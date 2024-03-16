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
bash $parent_path/Logger/Log.sh "Stoppong The Containers"
docker compose -f $parent_path/docker-compose.yml --profile app down