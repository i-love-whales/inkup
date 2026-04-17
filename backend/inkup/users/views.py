from django.contrib.auth.models import User
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def register(request):
    username, password = request.data.values()
    user = User(username=username, password=password)
    user.save()

    token = RefreshToken.for_user(user)

    return Response({"access": str(token.access_token)})


# @api_view(["GET"])
# def get_username(request):
#     return Response({"username": User.objects.get(

