from channels.routing import ProtocolTypeRouter

application = ProtocolTypeRouter({})

from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from .api.consumers import TaskConsumer

from channels.auth import AuthMiddlewareStack
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from rest_framework_simplejwt.exceptions import TokenError
import jwt
from djangoAPI import settings
from django.contrib.auth import get_user_model


class TokenAuthMiddleware:
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        # TODO: Pass token in from query string amd use TokenVerifySerializer to verify validity
        # TODO: Get User ID from payload of JWT token
        if scope['query_string']:
            try:
                request_query_string = scope['query_string'].decode('utf-8').split('=')
                access_token = request_query_string[1]
                decoded_token = jwt.decode(jwt=access_token, key=settings.SECRET_KEY)
                user_id = decoded_token.get('user_id')
                user = get_user_model().objects.get(id__contains=user_id)
                if TokenVerifySerializer().validate(attrs={"token": access_token}) == {} : # If token is valid
                    scope['user'] = user
            except TokenError as tokenerror: # Catch invalid/expired token from TokenVerifySerializer()
                print('TokenError occurred => ', tokenerror)
                pass
            except jwt.exceptions.ExpiredSignatureError as expirederror: # Catch invalid/expired token from TokenVerifySerializer()
                print('[!] Need to handle this error [!] ExpiredSignatureError occurred => ', expirederror)
                pass
            except Exception as unknownError:
                print('Unkonwn Error occured in Token Validation #routing => ', unknownError)
        return self.inner(scope)

TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))


application = ProtocolTypeRouter({
    'websocket': TokenAuthMiddlewareStack(
        URLRouter([
            path('ws/tasks/', TaskConsumer),
        ])
    )
})
