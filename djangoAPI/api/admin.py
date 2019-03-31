from django.contrib import admin
from .models import Movie, Task, User


# Register your models here.

admin.site.register(Movie)
admin.site.register(Task)
admin.site.register(User)
