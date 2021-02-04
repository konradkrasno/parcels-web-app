from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "parcels"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path(
        "upload_data/<str:catalog>",
        csrf_exempt(views.UploadData.as_view()),
        name="upload_data",
    ),
    path("register", views.register, name="register"),
    path("activate/<str:uidb64>/<str:token>", views.activate, name="activate"),
    path("user_login", views.user_login, name="login"),
    path("user_logout", views.user_logout, name="logout"),
    path(
        "adverts",
        views.AdvertListView.as_view(),
        name="advert_list",
    ),
    path(
        "adverts/<int:pk>",
        views.AdvertDetailView.as_view(),
        name="advert_detail",
    ),
    path(
        "favourites",
        views.FavouriteListView.as_view(),
        name="favourite_list",
    ),
    path(
        "save_advert/<int:pk>",
        views.save_advert,
        name="save_advert",
    ),
    path(
        "delete_advert/<int:pk>",
        views.delete_advert,
        name="delete_advert",
    ),
    path(
        "save_all_adverts",
        views.save_all_adverts,
        name="save_all_adverts",
    ),
    path(
        "delete_all_adverts>",
        views.delete_all_adverts,
        name="delete_all_adverts",
    ),
    path("download_csv", views.streaming_csv, name="download_csv"),
    path(
        "send_csv",
        views.sending_csv,
        name="send_csv",
    ),
]
