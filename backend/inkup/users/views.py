from rest_framework import permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User

from posts.models import Post
from posts.serializers import PostsSerializer


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_username(request):
    return Response({"username": request.user.username})


@api_view(["GET"])
def get_profile(request, username):
    user = User.objects.filter(username=username).first()

    if user is None:
        return Response(status=404)

    user_data = {
        "username": user.username,
        "date_joined": user.date_joined.strftime("%B %d, %Y"),
        "posts_total": Post.objects.filter(author=user.pk).count(),
    }

    return Response(user_data)


class PostListFromUserAPIView(generics.ListAPIView):
    queryset = Post.objects.select_related("author").values(
        "pk", "content", "time_created", "author__username"
    )
    serializer_class = PostsSerializer

    def list(self, request, username):
        queryset = self.get_queryset().filter(author__username=username)
        queryset = queryset.order_by("-time_created")
        serializer = PostsSerializer(queryset, many=True)

        return Response(serializer.data) 
