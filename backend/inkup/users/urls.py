from django.urls import path

from users import views


urlpatterns = [
    path("me/", views.get_username),
]
