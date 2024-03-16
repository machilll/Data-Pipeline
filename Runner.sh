#!/bin/bash

if [ "$EUID" -eq 0 ];then
	echo -e "Do not run the script using [sudo] or [root] user"
    exit 1
fi

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

if [ -f "$parent_path/.env" ]; then
	set -o allexport && source "$parent_path/.env" && set +o allexport
fi


bash $parent_path/Stopper.sh
bash $parent_path/Cronjob/AddJob.sh
bash $parent_path/Containers/ContainerUp.sh

bash $parent_path/Logger/Log.sh "Testing Kafka"
source $parent_path/.venv/bin/activate
python3 $parent_path/Containers/CheckKafka.py 1>/dev/null 2>/dev/null

if [ "$?" -ne "0" ]; then
    bash $parent_path/Logger/Log.sh "Kafka Connection Failed"
    bash $parent_path/Stopper.sh
    exit 1
fi

bash $parent_path/Logger/Log.sh "Kafka Is Healthy"
deactivate

bash $parent_path/Logger/Log.sh "Testing Nocodb"
count=0
flag=0
while [ $count -lt 30 ]; do
	if [ "$(curl -LIs -o /dev/null -w "%{http_code}" -X GET "http://localhost:${NOCODB_HOST_PORT:-8080}" 2>/dev/null)" -eq "200" ]; then
		sleep 1
		flag=1
		break
	fi
	count=$(($count + 1))
	sleep 1
done

if [ $flag -eq 0 ]; then
	bash $parent_path/Logger/Log.sh "Nocodb connection failed"
	exit 1
fi
bash $parent_path/Logger/Log.sh "Nocodb Connection Successful"
bash $parent_path/Logger/Log.sh "Starting Scripts..."
nohup bash $parent_path/Topics/TopicsRunner.sh 1>/dev/null 2>/dev/null