from celery import shared_task
from time import sleep


@shared_task
def test_task():
    for i in range(30):
        print(i)
        sleep(0.5)
