#!/bin/bash
while true; do
    python3 manage.py makemigrations parcels
    python3 manage.py migrate
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Init command failed, retrying in 5 secs...
    sleep 5
done
python3 manage.py runserver 0.0.0.0:8000
