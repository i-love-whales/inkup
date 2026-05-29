from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from auth import views


urlpatterns = [
    path("token/", TokenObtainPairView.as_view()),
    path("verify/", TokenVerifyView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("register/", views.register),
]
