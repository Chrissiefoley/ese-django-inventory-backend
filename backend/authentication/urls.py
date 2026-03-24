from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .cookie_views import LoginView, RefreshView, LogoutView
from .views import RegisterView, UserInfoView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserInfoView.as_view(), name='user_info'),
    path('', include(router.urls)),
]