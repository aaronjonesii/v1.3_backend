from .serializers import Movieserializer, PostSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import generics
from requests import get

from .models import Movie, Post


# Movie ViewSet below:
class MovieViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows movies to be viewed or edited.
    """
    queryset = Movie.objects.all().order_by('-released') # Newest first
    serializer_class = Movieserializer


# Blog Posts View below:
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')  # Newest first
    serializer_class = PostSerializer


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
