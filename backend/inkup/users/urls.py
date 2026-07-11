from django.urls import path

from users import views


urlpatterns = [
    path("me/", views.get_current_user_data),
    path("profile/<str:username>/", views.get_profile),
    path('<str:username>/posts/', views.PostListFromUserAPIView.as_view()),
]
