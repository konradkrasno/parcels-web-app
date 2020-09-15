from parcels.models import Advert
from django.db.utils import OperationalError

try:
    Advert.download_adverts_from_json()
    Advert.delete_duplicates()
except OperationalError:
    print("You have to make migrations before add data to database. ")
