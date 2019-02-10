from .serializers import MovieSerializer, PostSerializer, UserSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework import permissions
from .permissions import IsOwnerOrReadOnly
from rest_framework import viewsets
from rest_framework import generics
from requests import get

from .models import Movie, Post

from rest_framework_tracking.mixins import LoggingMixin


# Movie ViewSet below:
class MovieViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows movies to be viewed or edited.
    """
    queryset = Movie.objects.all().order_by('-released') # Newest first
    serializer_class = MovieSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,) # Read Only to public


# Blog Posts View below:
class PostViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')  # Newest first
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly) # Read Only unless owner

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# IP View below:
@api_view()
def ipView(request):
    ip = get_client_ip(request)
    response = ipinfo(ip)
    return Response({'content': response})

# IP Search View below:
@api_view()
def searchIP(request, query_ip):
    response = ipinfo(query_ip)
    return Response({'content': response})


# Get information from IP Address
def ipinfo(query_ip):
    url = "https://ipinfo.io/"
    resp = get(url + query_ip)
    return resp.json()


# Get IP Address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_addr = x_forwarded_for.split(',')[0]
    else:
        ip_addr = request.META.get('REMOTE_ADDR')
    return ip_addr


class UserList(LoggingMixin, generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(LoggingMixin, generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
