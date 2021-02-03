from .models import Favourite


def get_saved_adverts(get_response):
    def process_view(request):
        if request.user.is_authenticated:
            request.saved_adverts = Favourite.get_favourites(user_id=request.user.id)
        response = get_response(request)
        return response

    return process_view
