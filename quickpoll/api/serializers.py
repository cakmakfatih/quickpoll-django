from rest_framework import serializers
from .models import Poll, Option, User, Vote


class PollSerializer(serializers.ModelSerializer):
    remaining_seconds = serializers.ReadOnlyField()
    is_votable = serializers.ReadOnlyField()

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
        fields = ["option"]


class PollDetailSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)
    votes = VoteSerializer(many=True)
    remaining_seconds = serializers.IntegerField(default=0)
    user_vote = VoteSerializer(many=False)

    class Meta:
        model = Poll
        fields = "__all__"


class VotePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = "__all__"
