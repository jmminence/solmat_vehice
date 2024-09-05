from utils import functions as fn
from accounts.models import UserProfile
class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # LUEGO SETEAR AL VALOR A PARTIR DEL USER
        language = 'es' 
        if request.user.id:
            usuario = UserProfile.objects.get(user=request.user)
            language = 'es' if usuario and usuario.language == 1 else 'en'
        request.lang = fn.translation(language)

        response = self.get_response(request)

        return response