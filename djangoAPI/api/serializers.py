from .models import Movie, Task
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


def getFields(model):
    """ Dynamic way of adding all fields manually instead of '__all__' """
    immutable_list = model._meta.get_fields()
    fields_list = []
    for field in immutable_list:
        fields_list.append(field.attname)
    return fields_list


class MovieSerializer(serializers.HyperlinkedModelSerializer):
    """ Movie Serializer """
    class Meta:
        model = Movie
        fields = getFields(Movie)


class Ipserializer(serializers.Serializer):
    """ IP Lookup Serializer """
    ip = serializers.IPAddressField()
    response = serializers.JSONField()


class UserSerializer(serializers.ModelSerializer):
    """ User Serializer """
    # Never should be able to read passwords
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError('Passwords must match.')
        return data

    def create(self, validated_data):
        data = {
            key: value for key, value in validated_data.items()
            if key not in ('password1', 'password2')
        }
        data['password'] = validated_data['password1']
        return self.Meta.model.objects.create_user(**data)

    class Meta:
        model = get_user_model()
        # fields = getFields(User)
        # fields = ('id', 'username', 'posts')

        # Below is from testdriven.io tutorial
        fields = (
            'id', 'username', 'password1', 'password2',
            'first_name', 'last_name', 'email',
        )
        read_only_fields = ('id',)


class TaskSerializer(serializers.ModelSerializer):
    """ Task Serializer """
    # owner = serializers.ReadOnlyField(source='owner.username') # Show username instead of User ID
    class Meta:
        # ordering = ['-id'
        model = Task
        fields = '__all__'
        read_only_fields = ('id', 'ident', 'created', 'updated',)


class ReadOnlyTaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = Task
        fields = '__all__'
