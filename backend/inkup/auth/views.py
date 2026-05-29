from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from django.contrib.auth.forms import UserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def register(request):
    username, password = request.data.values()
    data = {"username": username, "password1": password, "password2": password}
    register_form = UserCreationForm(data)
    print("Credentials are delivered")

    if register_form.is_valid():
        token = RefreshToken.for_user(register_form.save())
        return Response({"access": str(token.access_token)})
    else:
        return Response({"message": register_form.errors}, status=401)
