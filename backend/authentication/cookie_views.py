from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from django.conf import settings
from .serializers import UserSerializer
from .models import User


class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',
                max_age=7200  # (2 hours to match the ACCESS_TOKEN_LIFETIME)
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',
                max_age=604800  # (7 days to match REFRESH_TOKEN_LIFETIME)
            )
            username = request.data.get('username')
            user = User.objects.get(username=username)
            response.data = {
                'user': UserSerializer(user).data
            }

        return response


class RefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found in cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['refresh'] = refresh_token
        request._full_data = data

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',
                max_age=7200  # (2 hours to match ACCESS_TOKEN_LIFETIME)
            )
            del response.data['access']

        return response


class LogoutView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token', samesite='Lax')
        response.delete_cookie('refresh_token', samesite='Lax')
        return response
