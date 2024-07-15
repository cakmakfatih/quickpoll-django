from django.contrib import admin
from .models import User, Vote, Poll, Option

admin.site.register([User, Vote, Poll, Option])
