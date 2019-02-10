from .models import Movie, Post
from rest_framework import serializers
from django.contrib.auth.models import User


def getFields(model):
    """ Dynamic way of adding all fields manually instead of '__all__' """
    immutable_list = model._meta.get_fields()
    fields_list = []
    for field in immutable_list:
        fields_list.append(field.attname)
    return fields_list


class MovieSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Movie
        fields = getFields(Movie)


class PostSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username') # Populate field with owner

    class Meta:
        model = Post
        fields = '__all__' # Provides url instead of id
        # fields = getFields(Post)

class Ipserializer(serializers.Serializer):
    ip = serializers.IPAddressField()
    response = serializers.JSONField()


class UserSerializer(serializers.ModelSerializer):
    posts = serializers.PrimaryKeyRelatedField(many=True, queryset=Post.objects.all())
    class Meta:
        model = User
        fields = ('id', 'username', 'posts')
