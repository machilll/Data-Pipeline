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
bash $parent_path/Cronjob/DeleteJob.sh
bash $parent_path/Logger/Log.sh "[GetData.py] is being added to crontab"

(
	crontab -l
	echo "* * * * *  $parent_path/.venv/bin/python3  $parent_path/Data/GetData.py 1>>/dev/null 2>>/dev/null"
    echo "5 * * * *  $parent_path/bin/bash  $parent_path/Data/Backup.sh 1>>/dev/null 2>>/dev/null"
) | crontab -
