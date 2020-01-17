from django.urls import path
from . import views


app_name = 'parcels'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),

    path('register', views.register, name='register'),

    path('user_login', views.user_login, name='login'),
    path('user_logout', views.user_logout, name='logout'),

    path('form/<user_id>', views.SearchAdvertLoginView.as_view(), name='form_when_login'),
    path('form', views.SearchAdvertLogoutView.as_view(), name='form_when_logout'),

    path('form/<place>/<price>/<area>/<int:user_id>', views.AdvertListLoginView.as_view(),
         name='advert_list_when_login'),
    path('form/logout/<place>/<price>/<area>', views.AdvertListLogoutView.as_view(), name='advert_list_when_logout'),

    path('form/<place>/<price>/<area>/<int:pk>/<int:user_id>', views.AdvertDetailLoginView.as_view(),
         name='advert_detail_when_login'),
    path('form/logout/<place>/<price>/<area>/<int:pk>', views.AdvertDetailLogoutView.as_view(),
         name='advert_detail_when_logout'),

    path('form/<place>/<price>/<area>/<int:pk>/<int:user_id>/add', views.make_favourite, name='make_favourite'),
    path('form/<place>/<price>/<area>/<int:pk>/<int:user_id>/remove', views.remove_favourite, name='remove_favourite'),

    path('form/<place>/<price>/<area>/<int:pk>/<int:user_id>/list/add', views.make_favourite_list,
         name='make_favourite_list'),
    path('form/<place>/<price>/<area>/<int:pk>/<int:user_id>/list/remove', views.remove_favourite_list,
         name='remove_favourite_list'),

    path('form/<place>/<price>/<area>/<int:user_id>/add_all', views.make_all_favourite, name='make_all_favourite'),
    path('form/<place>/<price>/<area>/<int:user_id>/remove_all', views.remove_all_favourite,
         name='remove_all_favourite'),

    path('favourites/<int:user_id>', views.FavouriteListView.as_view(), name='favourite_list'),
    path('favourites/<int:pk>/<int:user_id>', views.FavouriteDetailView.as_view(), name='fav_advert_detail'),

    path('favourites/<int:pk>/<int:user_id>/add', views.make_favourite_from_fav, name='make_favourite_from_fav'),
    path('favourites/<int:pk>/<int:user_id>/remove', views.remove_favourite_from_fav, name='remove_favourite_from_fav'),

    path('favourite/<int:pk>/<int:user_id>/list/add', views.make_favourite_from_fav_list,
         name='make_favourite_from_fav_list'),
    path('favourite/<int:pk>/<int:user_id>/list/remove', views.remove_favourite_from_fav_list,
         name='remove_favourite_from_fav_list'),

    path('favourite/<int:user_id>/remove_all', views.remove_all_favourite_from_fav,
         name='remove_all_favourite_from_fav'),

]
