import datetime
import hashlib

from django.db import models
from requests import get
from django.db import models # new
from django.shortcuts import reverse # new
from django.contrib.auth.models import AbstractUser
from django_mysql.models import ListCharField
from django.conf import settings

# Create your models here.
from rest_framework import serializers


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



class Ip(object):
    def __init__(self, ip):
        self.ip = ip
        self.response = self.ipinfo(ip)

    def ipinfo(ip):
        url = "https://ipinfo.io/"
        resp = get(url + ip)
        return resp.json()


class User(AbstractUser):
    pass


class Task(models.Model):
    BACKLOG = 'BACKLOG'
    UP_NEXT = 'UP_NEXT'
    TODO = 'TODO'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    STATUSES = (
        (BACKLOG, BACKLOG),
        (UP_NEXT, UP_NEXT),
        (TODO, TODO),
        (IN_PROGRESS, IN_PROGRESS),
        (COMPLETED, COMPLETED)
    )

    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    PRIORITIES = (
        (LOW, LOW),
        (MEDIUM, MEDIUM),
        (HIGH, HIGH)
    )

    ident = models.CharField(max_length=32, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=400)
    priority = models.CharField(max_length=15, choices=PRIORITIES, default=LOW)
    status = models.CharField(max_length=30, choices=STATUSES, default=BACKLOG)
    tags = ListCharField(
        base_field=models.CharField(max_length=10),
        size=6,
        max_length=(6 * 11)
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null = False,
        blank=False,
        on_delete=models.DO_NOTHING,
        related_name='tasks_as_owner'
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('task:task_detail', kwargs={'task_ident': self.ident})

    def save(self, **kwargs):
        if not self.ident:
            now = datetime.datetime.now()
            secure_hash = hashlib.md5()
            secure_hash.update(f'{now}:{self.title}'.encode('utf-8'))
            self.ident = secure_hash.hexdigest()
        super().save(**kwargs)

