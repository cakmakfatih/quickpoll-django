from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(models.Model):
    ip = models.CharField(max_length=15)


class Poll(models.Model):
    class Duration(models.TextChoices):
        ONE_MIN = "1M", _("1 minute")
        FIVE_MIN = "5M", _("5 minutes")
        TEN_MIN = "10M", _("10 minutes")

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    title = models.CharField(max_length=255)
    is_open = models.BooleanField(default=True)
    duration = models.CharField(
        max_length=3, choices=Duration.choices, default=Duration.FIVE_MIN
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, blank=True)
    value = models.CharField(max_length=500)


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
