import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(models.Model):
    ip = models.CharField(max_length=15)


class Poll(models.Model):
    class Duration(models.TextChoices):
        ENDLESS = "EM", _("E minute")
        ONE_MIN = "1M", _("1 minute")
        FIVE_MIN = "5M", _("5 minutes")
        TEN_MIN = "10M", _("10 minutes")

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    title = models.CharField(max_length=255)
    duration = models.CharField(
        max_length=3, choices=Duration.choices, default=Duration.FIVE_MIN
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_seconds(self):
        if self.duration == "EM":
            return -1

        now = datetime.datetime.now(datetime.UTC)
        difference_in_seconds = int(((now) - self.created_at).total_seconds())
        remaining_seconds = 0

        if self.duration == "1M":
            remaining_seconds = (1 * 60) - difference_in_seconds
        elif self.duration == "5M":
            remaining_seconds = (5 * 60) - difference_in_seconds
        elif self.duration == "10M":
            remaining_seconds = (10 * 60) - difference_in_seconds

        if remaining_seconds < 0:
            return 0

        return remaining_seconds

    @property
    def is_votable(self):
        if self.remaining_seconds == -1:
            return True

        return self.remaining_seconds > 0


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, blank=True)
    value = models.CharField(max_length=500)


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
