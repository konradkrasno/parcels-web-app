web: python manage.py makemigrations parcels; python manage.py migrate; gunicorn parcels_web_app.wsgi
worker: celery -A parcels_web_app worker -l info
beat: celery -A parcels_web_app beat -l info
