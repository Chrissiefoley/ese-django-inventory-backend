from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status, views
from rest_framework.permissions import AllowAny
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
                samesite='Lax' # Or 'Strict' depending on your needs
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                samesite='Lax' # Or 'Strict'
            )
            # The user serializer is added to the response so the frontend can
            # get user info without a separate request.
            username = request.data.get('username')
            user = User.objects.get(username=username)
            response.data = {
                'user': UserSerializer(user).data
            }

        return response

class RefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # By default, TokenRefreshView looks for the refresh token in the request body.
        # We override this to look in the cookies instead.
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found in cookies'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.data['refresh'] = refresh_token
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                samesite='Lax'
            )
            # We don't need to send the new access token in the body
            del response.data['access']

        return response

class LogoutView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
