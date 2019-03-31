"""djangoAPI URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import url, include
from rest_framework import routers
from djangoAPI.api import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'movies', views.MovieViewSet, base_name="movie")
router.register(r'users', views.UserViewSet, base_name='user')
router.register(r'tasks', views.TaskView, base_name='task')

ipv4pattern = '(?:(?:0|1[\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:0|1[\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?'
ipv6pattern = '(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('api-login/', views.CustomLoginJWTAuthToken.as_view(), name='login'),
    url(r'^api-refresh/$', TokenRefreshView.as_view(), name='refresh'),  # TODO: Create Custom Refresh View for wrapping token in token JSON key
    # url(r'^api/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api-task/', include('djangoAPI.api.urls', 'task')),
    path('api-user/', views.ViewUser.as_view(), name='user'),
    path('admin/', admin.site.urls),
    path('ip/', views.ipView, name='ip'), # Get IP info from requestor
    re_path(rf'^ip/(?P<query_ip>{ipv4pattern}))/$', views.searchIP, name='search_ip'),  # Get IPv4 info from query_ip
    re_path(rf'^ip/(?P<query_ip>{ipv6pattern})/$', views.searchIP, name='search_ip'),  # Get IPv6 info from query_ip
    path('api-signup/', views.CustomSignUpJWTAuthToken.as_view(), name='signup'),
    # path('api-login/', views.CustomAuthToken.as_view(), name='login'),
    path('api-logout/', views.LogOutView.as_view(), name='logout'),
    url(r'^', include(router.urls)) # Default view
    # path('api-login/', include('rest_framework.urls', namespace='rest_framework')), # Admin Panel (Login/Logout)
]
