import django
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def register(request):
    print("Enter to register")
    username, password = request.data.values()
    data = {"username": username,
            "password1": password,
            "password2": password}
    register_form = UserCreationForm(data)
    print("Credentials are delivered")
    if register_form.is_valid():
        print("Valid")
        token = RefreshToken.for_user(register_form.save())
        return Response({"access": str(token.access_token)})
    else:
        return Response({"message": register_form.errors}, status=401)


# @api_view(["GET"])
# def get_username(request):
#     return Response({"username": User.objects.get(

