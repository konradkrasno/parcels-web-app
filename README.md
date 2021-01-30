# parcels-web-app

This is django web application with which you can look for building plots advertisements and find the most attractive one.

### Design goals

Main goal of this application is collect data from services with advertisements and filter it with particular parameters.

Data is automatically scraped and loaded to database.

Application have features such us:
* saving filtered adverts
* downloading csv file with favourite adverts
* sending email with csv file with favourite adverts

### Working of application

Application consists of four services:
* django - handles business logic
* postgres - the database service
* crawler - service for scraping data from sites with advertisements and load scraped data to postres database
 via Django API
* task-manager - runs clawler in scheduled time

### Example View
![favourites_page](https://user-images.githubusercontent.com/55924004/93318427-fa40c200-f80e-11ea-9af1-5c6d8a0c90d9.PNG)

### Installation

Clone the repository:
```bash
git clone https://github.com/konradkrasno/parcels-web-app.git
cd parcels-web-app
```
To run the application and enjoy all features you have to create json file with django secret key and information about email account which you will use to send messages to users. Name it secure.json:
```
parcels-web-app/secure.json
{
 "SECRET_KEY": "django_server_key",
 "EMAIL_HOST": "your_email_host", 
 "EMAIL_HOST_USER": "your_email_address", 
 "EMAIL_HOST_PASSWORD": "your_email_password", 
 "EMAIL_PORT": "your_email_port"
}
```

Initialize docker containers:
```bash
docker-compose up -d
```

Get inside Django container to make migrations and run tests:
```bash
docker exec -it <django-container-name> bash
python3 parcels-web-app/manage.py makemigrations parcels
python3 parcels-web-app/manage.py migrate
```

To run unit tests write in command prompt:

```bash
pytest -v parcels-web-app/parcels/tests
```
