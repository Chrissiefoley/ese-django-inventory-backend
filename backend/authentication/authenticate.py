from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        if 'access_token' in request.COOKIES:
            request.META['HTTP_AUTHORIZATION'] = f"Bearer {request.COOKIES['access_token']}"
        return super().authenticate(request)
