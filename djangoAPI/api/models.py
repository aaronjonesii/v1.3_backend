from django.db import models
from requests import get

# Create your models here.

class Movie(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    imdb_id = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    year = models.CharField(max_length=4)
    slug = models.CharField(max_length=150)
    synopsis = models.TextField()
    runtime = models.CharField(max_length=4)
    country = models.CharField(max_length=4)
    last_updated = models.FloatField(max_length=16)
    released = models.IntegerField()
    certification = models.CharField(max_length=255)
    torrents = models.TextField()
    trailer = models.CharField(max_length=255)
    genres = models.CharField(max_length=255)
    images = models.TextField()
    rating = models.CharField(max_length=255)
    _v = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.title


class Post(models.Model):
    title = models.CharField(max_length=75)
    content = models.TextField()
    image = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey('auth.User', related_name='posts', on_delete=models.CASCADE)
    # To reset id: ALTER TABLE api_post AUTO_INCREMENT = 1;

    def __str__(self):
        return self.title


class Ip(object):
    def __init__(self, ip):
        self.ip = ip
        self.response = self.ipinfo(ip)

    def ipinfo(ip):
        url = "https://ipinfo.io/"
        resp = get(url + ip)
        return resp.json()

