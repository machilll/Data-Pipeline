#! /bin/bash

_get_parent () {
    path=$1
    depth=$2
    for i in $(seq 1 $depth); do
        path=$(dirname $path)
    done
    echo $path
    return 0
}

_save_log () {
    echo "$(date +"%Y-%m-%d %H:%M:%S"): $1" >> $parent_path/log/info.log
}

_print_log () {
    size=${#1}
    
    for i in $(seq 1 $(($size+2))); do
        printf "+"
    done

    printf "\n"

    printf "|%s|" "$1"

    printf "\n"

    for i in $(seq 1 $(($size+2))); do
        printf "+"
    done

    printf "\n"
}

parent_path=$(_get_parent $(readlink -f $0) 2)

log_text=$1

shift

table=0

_save_log "$log_text"
_print_log "$log_text"