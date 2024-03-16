#!/bin/bash

_get_parent () {
    path=$1
    depth=${2:-1}
    while [ $depth -ne 0 ]; do
        path=$(dirname $path)
        depth=$(($depth - 1))
    done
    echo $path
    return 0
}

parent_path=$(_get_parent $(readlink -f $0) 2)

set -o allexport && source $parent_path/.env && set +o allexport

docker exec mahsa_postgres bash -c "pg_basebackup -U ${POSTGRES_USER:-mahsa} -w -D /backup/standalone-"$(date +%Y-%m-%d_%T%H-%M)" -c fast -P -R"
