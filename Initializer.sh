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

set -o allexport && source .env && set +o allexport

mkdir -p $dir_path/log
sudo mkdir -p $dir_path/Data/postgres
sudo mkdir -p $dir_path/Data/Nocodb
sudo mkdir -p $dir_path/NocoSettings

touch $parent_path/log/error.log
touch $parent_path/log/info.log

bash $parent_path/Logger/Log.sh "Initializing The Project"

_add_execute () {
	f_name=$1
	extension=$2

	if [ -f $f_name ]; then
		sudo chmod a+x $f_name
	
	elif [ -d "$parent_path/$f_name" ]; then
		find "$parent_path/$f_name" -type f -iname "*.$extension" | xargs chmod a+x
	fi
}

bash $parent_path/Logger/Log.sh "Making Essential Files Executable"

_add_execute logger sh
_permiter "$parent_path/Data/Backup.sh"
_add_execute "$parent_path/Runner.sh"
_add_execute "$parent_path/Data/GetData.py"
_add_execute "$parent_path/Stopper.sh"
_add_execute Cronjob sh
_add_execute Containers sh
_add_execute Topics sh


bash $parent_path/Logger/Log.sh "Dependecy Checking"

_check_dependency() {
	bash -c "$1 --version 1>/dev/null 2>/dev/null"
	if [ $? -ne 0 ]; then
		echo -e "$1 dependency not met.\t Visit $2 to install"
		exit 1
	fi
}

bash $parent_path/Logger/Log.sh "Checking [docker]"
_check_dependency docker "https://docs.docker.com/engine/install/"

bash $parent_path/Logger/Log.sh "Checking [python]"
_check_dependency python3 "https://www.python.org/"

apt_update=0

bash $parent_path/Logger/Log.sh "Checking [crontab]"
bash -c "crontab --version 1>/dev/null 2>/dev/null"
if [ $? -eq 127 ]; then
	echo "Installing Crontab:"
	sudo apt-get install -y cron
	if [ $? -ne 0 ]; then
		sudo apt-get update
		apt_update=1
		sudo apt-get install -y cron
		if [ $? -ne 0 ]; then
			echo "Cron installation failed"
			exit 1
		fi
	fi
fi

sudo service cron start 1>/dev/null 2>/dev/null
if [ $? -ne 0 ]; then
	sudo systemctl start cron 1>/dev/null 2>/dev/null 
	if [ $? -ne 0 ]; then
		echo "Crontab start failed"
		exit 1
	fi
fi

sudo apt-get install -y libpq-dev

if [ $? -ne 0 ]; then
	if [ $apt_update -ne 1 ]; then
		sudo apt-get update
	fi
	sudo apt-get install -y libpq-dev
	if [ $? -ne 0 ]; then
    	echo "Libpq-dev installation failed"
    	exit 1
	fi
fi

bash $parent_path/Logger/Log.sh "Creating Python Venv"

if ! [ -d "$parent_path/.venv" ]; then
	python3 -m venv $parent_path/.venv
	if [ $? -ne 0 ]; then
		echo "Installing python3-venv:"
		sudo rm -rf $parent_path/.venv
		sudo apt-get install -y python3-venv

		if [ $? -ne 0 ]; then
			echo "Installation failed"
			exit 1
		fi
	fi

	source $parent_path/.venv/bin/activate
	if [ $? -ne 0 ]; then
		sudo chmod a+x $parent_path/.venv/bin/activate
		if [ $? -ne 0 ]; then
			echo "Adding execution permission failed"
			exit 1
		fi
		
		source $parent_path/.venv/bin/activate
		if [ $? -ne 0 ]; then
			echo "Venv activation failed"
			exit 1
		fi
	fi
	
	pip install poetry==1.8.2
	if [ $? -ne 0 ]; then
		echo "Poetry installation failed"
		exit 1
	fi
	
	poetry shell
	if [ $? -ne 0 ]; then
		echo "Poetry shell activation failed"
		exit 1
	fi
	bash $parent_path/Logger/Log.sh "Installing Required Packages:"
	poetry install --no-root
	if [ $? -ne 0 ]; then
		echo "Installation failed"
		exit 1
	fi
fi

docker compose -f $parent_path/docker-compose.yml --profile=nocodb down
docker compose -f $parent_path/docker-compose.yml --profile=nocodb up -d

bash $parent_path/logger/log.sh "Initializing Nocodb"

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
	bash $parent_path/logger/log.sh "Nocodb connection failed"
	exit 1
fi

bash $parent_path/logger/log.sh "Nocodb Connection Successful"

python3 "$parent_path/Nocodb/CreateBase.py" 1>/dev/null 2>/dev/null

if [ $? -ne 0 ]; then
	echo "Nocodb base creation failed"
	docker compose -f $parent_path/docker-compose.yml --profile=nocodb down
	exit 1
fi

python3 "$parent_path/nocodb/create_table.py" 1>/dev/null 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Nocodb table creation failed"
	docker compose -f $parent_path/docker-compose.yml --profile=nocodb down
	exit 1
fi

docker compose -f $parent_path/docker-compose.yml --profile=nocodb down

deactivate

bash $parent_path/Logger/Log.sh "Libraries Were Installed Successfully"

bash $parent_path/Logger/Log.sh "Building Container"

docker compose -f $parent_path/docker-compose.yml --profile db down
docker compose -f $parent_path/docker-compose.yml --profile db up -d

bash $parent_path/Logger/Log.sh "Checking Database"

count=0
ready=0
while [ $count -lt 30 ]; do
	bash -c "docker exec mahsa_postgres pg_isready -U ${POSTGRES_USER:-mahsa} -d ${POSTGRES_DB:-postgres} -h ${POSTGRES_HOST:-localhost} -q" 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ]; then
		count=$(($count + 1))
		bash $parent_path/Logger/Log.sh 'PostgreSQL is not ready'
		sleep 1
		continue
	fi

	bash $parent_path/Logger/Log.sh 'PostgreSQL is ready'
	ready=1
	break
done

if [ $ready -eq 0 ]; then
	bash $parent_path/Logger/Log.sh "Database connection failed"
	exit 1
fi

bash $parent_path/Logger/Log.sh "Database Is Ready"


bash $parent_path/Logger/Log.sh "Checking Database Schema"

count=0
flag=0
while [ $count -lt 30 ]; do	
	if [ $(docker exec mahsa_postgres bash -c "psql -U mahsa -d postgres -h localhost -c \"
		SELECT 1 AS flag
		FROM information_schema.TABLES AS t
		WHERE t.table_name = 'users' AND
		t.table_schema = 'mahsa';\" | grep -c '(1 row)'") -lt 1 ]; then
		docker exec mahsa_postgres bash -c "psql -U ${POSTGRES_USER:-mahsa} -d ${POSTGRES_DB:-postgres} -h ${POSTGRES_HOST:-localhost} < /code/init.sql 1>/dev/null 2>/dev/null"
		sleep 1
	else
		flag=1
		break
	fi
	count=$(($count + 1))
done

if [ $flag -eq 0 ]; then
	bash $parent_path/Logger/Log.sh "[${POSTGRES_SCHEMA:-mahsa}] schema and/or [users] table creation failed"
	exit 1
fi

bash $parent_path/Logger/Log.sh "Database Schema Is Correct"

bash $parent_path/Logger/Log.sh "Creating Backup"

bash $parent_path/Data/Backup.sh

if [ $? -ne 0 ]; then
	bash $parent_path/logger/log.sh "Backup creation failed"
	exit 1
fi

bash $parent_path/logger/log.sh "Enabaling Archive"

if ! [ $(
	docker exec postgres_project bash -c "cat /var/lib/postgresql/data/postgresql.conf" | 
	grep -c "^archive_mode = on$") -ge 1 ]; then

	docker exec postgres_project bash -c " echo -e \"
	wal_level = replica
	archive_mode = on
	archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'\" >> /var/lib/postgresql/data/postgresql.conf"

	if [ $? -ne 0 ]; then
		bash $parent_path/logger/log.sh "Archive failed"
		exit 1
	fi
else
	bash $parent_path/logger/log.sh "Archive already enabled"
fi

docker compose -f $parent_path/docker-compose.yml --profile db down