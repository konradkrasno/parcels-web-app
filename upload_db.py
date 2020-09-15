from parcels.models import Advert

try:
    Advert.download_adverts_from_json()
    Advert.delete_duplicates()
except Exception as exc:
    print("You have to make migrations before add data to database.")
