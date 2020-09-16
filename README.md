# parcels-web-app

This is django web application with which you can look for building plots advertisements and find the most attractive one.

## Design goals

Main goal of this application is collect data from another services with advertisements and filter it with particular parameters.

Application have features such us:
* saving filtered adverts
* downloading csv file with favourite adverts
* sending email with csv file with favourite adverts

#### Starting page
![start_page](images/start.png)
#### Searching page
![searching_page](images/search.png)
#### Register page
![register_page](images/register.png)
#### Login page
![login_page](images/login.png)
#### Favourite adverts list page
![favourites_page](images/favourites.png)

### Uploading data

Data is uploading to database from json file. Json file should be named adverts.json and looks like example below:
```
parcels-web-app/adverts.json
[
	{
		"store_id": 1,
		"place": "example_place",
		"county": "example_county",
		"price": "200000",
		"price_per_m2": "200",
		"area": "1000",
		"link": "example_link",
		"date_added": "14/09/2020",
		"description": "example_description"
	},
	{
		"store_id": 1,
		"place": "example_place",
		"county": "example_county",
		"price": "400000",
		"price_per_m2": "400",
		"area": "1000",
		"link": "example_link",
		"date_added": "14/09/2020",
		"description": "example_description"
	}
]

```
We can use scrapy to crawl data from popular services.

## Installation

Clone the repository:
```bash
git clone https://github.com/konradkrasno/parcels-web-app.git
```
Initialize virtual environment and install requirements:
```bash
cd parcels-web-app
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```
To enjoy all features you have to create json file with information about email account which you will use to send messages to users. Name it secure.json:
```
parcels-web-app/secure.json
{
 "EMAIL_HOST": "your_email_host", 
 "EMAIL_HOST_USER": "your_email_address", 
 "EMAIL_HOST_PASSWORD": "your_email_password", 
 "EMAIL_PORT": "your_email_port"
}
```
Don't forget about create adverts.json file (info about it above in Uploading data section).

Make migrations and run django server:
```bash
python3 manage.py makemigrations parcels
python3 manage.py migrate
python3 manage.py runserver
```

## Unit tests

To run unit tests write in command prompt:

```bash
python manage.py test parcels.tests
```
