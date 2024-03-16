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

parent_path=$(_get_parent $(readlink -f $0) 1)
bash $parent_path/Cronjob/DeleteJob.sh
bash $parent_path/Containers/ContainerDown.sh
bash $parent_path/Topics/TopicsStopper.sh