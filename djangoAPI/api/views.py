from .serializers import MovieSerializer, UserSerializer, TaskSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import viewsets
from django.contrib.auth import get_user_model, login, logout # Channels
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from rest_framework import generics, permissions, status, views# ||
from requests import get # IP
# from .permissions import IsOwnerOrReadOnly # Custom Permission
from .models import Movie, Task
from rest_framework_tracking.mixins import LoggingMixin # Log Serializer Usage in DB

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken


# Movie ViewSet below:
class MovieViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows movies to be viewed or edited.
    """
    queryset = Movie.objects.all().order_by('-released')  # Newest first
    serializer_class = MovieSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)  # Read Only to public


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


class UserViewSet(LoggingMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class SignUpView(LoggingMixin, generics.CreateAPIView):
    """
    API endpoint that allows Users to Signup
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class LogInView(LoggingMixin, views.APIView):
    """
    API endpoint that allows Users to Login
    """
    def post(self, request):
        form = AuthenticationForm(data=request.data)
        if form.is_valid():
            user = form.get_user()
            login(request, user=form.get_user())
            return Response(UserSerializer(user).data)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class LogOutView(LoggingMixin, views.APIView):
    """
    API endpoint that allows signed in users to Logout
    """
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, *args, **kwargs):
        logout(self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskView(LoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows signed in users to view their tasks
    """
    lookup_field = 'ident'
    lookup_url_kwarg = 'task_ident'
    # queryset = Task.objects.all().order_by('updated')
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(owner=user)

    # Assign logged in user to created task
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username,
            'email': user.email
        })


class ViewUser(LoggingMixin, views.APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        user = self.request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomLoginJWTAuthToken(LoggingMixin, views.APIView):

    def post(self, request):
        form = AuthenticationForm(data=request.data)
        if form.is_valid():
            user = form.get_user()
            login(request, user=form.get_user())

            refresh = RefreshToken.for_user(request.user)
            return Response({
                'token': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
        })
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomSignUpJWTAuthToken(LoggingMixin, views.APIView):

    def post(self, request):
        data = request.data
        form = UserSerializer(data=data)
        if form.is_valid():
            new_user = form.save()
            login(request, user=new_user)


            refresh = RefreshToken.for_user(request.user)
            return Response({
                'token': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
        })
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
