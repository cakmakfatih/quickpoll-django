from rest_framework import serializers
from .models import Poll, Option, User, Vote


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = "__all__"


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "value"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id"]


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ["id"]


class PollDetailSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)
    votes = VoteSerializer(many=True)

    class Meta:
        model = Poll
        fields = "__all__"
