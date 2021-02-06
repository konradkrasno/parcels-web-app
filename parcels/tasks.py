from typing import *

from celery import shared_task
from django.core.mail import EmailMessage


@shared_task
def send_email(subject: str, body: str, to: List, attachments: List = None):
    email = EmailMessage(
        subject=subject,
        body=body,
        to=to,
        attachments=attachments
    )
    email.send()
