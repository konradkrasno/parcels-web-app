from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt


app_name = "parcels"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("upload_data/<str:catalog>", csrf_exempt(views.UploadData.as_view()), name="upload_data"),
    path("register", views.register, name="register"),
    path("activate/<uidb64>/<token>", views.activate, name="activate"),
    path("user_login", views.user_login, name="login"),
    path("user_logout", views.user_logout, name="logout"),
    path(
        "form/<user_id>", views.SearchAdvertsView.as_view(), name="search_adverts_form"
    ),
    path(
        "form/<place>/<price>/<area>/<int:user_id>",
        views.AdvertListView.as_view(),
        name="advert_list",
    ),
    path(
        "form/<place>/<price>/<area>/<int:pk>/<int:user_id>",
        views.AdvertDetailView.as_view(),
        name="advert_detail",
    ),
    path(
        "favourites/<int:user_id>",
        views.FavouriteListView.as_view(),
        name="favourite_list",
    ),
    path(
        "favourites/<int:pk>/<int:user_id>",
        views.FavouriteDetailView.as_view(),
        name="favourite_detail",
    ),
    path(
        "form/<place>/<price>/<area>/<int:pk>/<int:user_id>/add",
        views.make_favourite,
        name="make_favourite",
    ),
    path(
        "form/<place>/<price>/<area>/<int:pk>/<int:user_id>/remove",
        views.remove_favourite,
        name="remove_favourite",
    ),
    path(
        "form/<place>/<price>/<area>/<int:pk>/<int:user_id>/list/add",
        views.make_favourite_list,
        name="make_favourite_list",
    ),
    path(
        "form/<place>/<price>/<area>/<int:pk>/<int:user_id>/list/remove",
        views.remove_favourite_list,
        name="remove_favourite_list",
    ),
    path(
        "form/<place>/<price>/<area>/<int:user_id>/add_all",
        views.make_all_favourite,
        name="make_all_favourite",
    ),
    path(
        "form/<place>/<price>/<area>/<int:user_id>/remove_all",
        views.remove_all_favourite,
        name="remove_all_favourite",
    ),
    path(
        "favourites/<int:pk>/<int:user_id>/add",
        views.make_favourite_from_favourites,
        name="make_favourite_from_favourites",
    ),
    path(
        "favourites/<int:pk>/<int:user_id>/remove",
        views.remove_favourite_from_favourites,
        name="remove_favourite_from_favourites",
    ),
    path(
        "favourite/<int:pk>/<int:user_id>/list/remove",
        views.remove_favourite_from_favourites_list,
        name="remove_favourite_from_favourites_list",
    ),
    path(
        "favourite/<int:user_id>/remove_all",
        views.remove_all_favourite_from_favourites,
        name="remove_all_favourite_from_favourites",
    ),
    path("favourite/<int:user_id>/csv", views.streaming_csv, name="streaming_csv"),
    path(
        "favourite/<int:user_id>/sending_csv",
        views.sending_csv,
        name="sending_csv",
    ),
]
