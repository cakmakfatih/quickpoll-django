from django.db import models
import uuid


class User(models.Model):
    ip = models.CharField(max_length=15)


class Poll(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    title = models.CharField(max_length=255)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, blank=True)
    value = models.CharField(max_length=500)


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, blank=True, null=True)
