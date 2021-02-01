#!/bin/bash
while true; do
    python3 parcels-web-app/manage.py makemigrations parcels
    python3 parcels-web-app/manage.py migrate
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Init command failed, retrying in 5 secs...
    sleep 5
done
python3 ./parcels-web-app/manage.py runserver 0.0.0.0:8000
