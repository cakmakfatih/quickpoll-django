import datetime
from typing import List
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    PollSerializer,
    OptionSerializer,
    UserSerializer,
    PollDetailSerializer,
    VotePostSerializer,
    VoteSerializer,
)
from .models import Option, Poll, User, Vote
from .functions import get_client_ip


def get_user_from_ip(ip: str):
    try:
        return User.objects.get(ip=ip)
    except User.DoesNotExist:
        return None


def get_poll(pk) -> Poll:
    try:
        return Poll.objects.get(pk=pk)
    except Poll.DoesNotExist:
        raise Http404


def get_options(poll_id) -> List[Option]:
    try:
        return Option.objects.filter(poll=poll_id)
    except Option.DoesNotExist:
        raise Http404


def get_votes(poll_id) -> List[Vote]:
    try:
        return Vote.objects.filter(poll=poll_id)
    except Vote.DoesNotExist:
        return []


class PollList(APIView):
    def post(self, request, format=None):
        poll_serializer = PollSerializer(data=request.data)

        if not poll_serializer.is_valid():
            return Response(
                data={"message": "Provide required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "options" not in request.data:
            return Response(
                data={"message": "Provide required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = request.data["options"]

        if not type(options) is list:
            return Response(
                data={"message": "Options should be an array."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(options) < 2 or len(options) > 10:
            return Response(
                data={"message": "Option count should be between 2 and 10."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for opt in options:
            option_serializer = OptionSerializer(data=opt)

            if not option_serializer.is_valid():
                return Response(
                    data={"message": "Option(s) are not valid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        poll = poll_serializer.save()

        for opt in options:
            Option(poll=poll, value=opt["value"]).save()

        return Response(data=poll_serializer.data, status=status.HTTP_200_OK)


class PollDetails(APIView):
    def get(self, request, pk, format=None):
        poll = get_poll(pk)
        options = get_options(pk)
        votes = get_votes(pk)

        serializer = PollDetailSerializer(
            {
                "id": poll.id,
                "title": poll.title,
                "created_at": poll.created_at,
                "remaining_seconds": poll.remaining_seconds,
                "options": options,
                "votes": votes,
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UserList(APIView):
    def post(self, request, format=None):
        ip = get_client_ip(request)
        user = get_user_from_ip(ip)

        if user is not None:
            serializer = UserSerializer(user)

            return Response(serializer.data, status=status.HTTP_409_CONFLICT)

        user = User(ip=ip)
        user.save()

        serializer = UserSerializer(user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VoteList(APIView):
    def get_vote_for_existing_poll(
        self,
        user: User,
        poll_id: str,
    ) -> Vote:
        try:
            return Vote.objects.get(user=user.id, poll=poll_id)
        except Vote.DoesNotExist:
            return None

    def post(self, request, format=None):
        serializer = VotePostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ip = get_client_ip(request)
        user = get_user_from_ip(ip)
        poll = get_poll(request.data["poll"])

        if not poll.is_votable:
            return Response(
                {"message": "Poll is already closed."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        if user is None:
            user = User(ip=ip)
            user.save()

        vote = None
        status_code = None
        existing_vote = self.get_vote_for_existing_poll(user, request.data["poll"])

        if existing_vote is None:
            vote = VotePostSerializer(
                data={
                    "user": user.id,
                    "poll": request.data["poll"],
                    "option": request.data["option"],
                }
            )
            status_code = status.HTTP_201_CREATED
        elif existing_vote.option.id == request.data["option"]:
            return Response(
                {"message": "Already voted for this option."},
                status=status.HTTP_208_ALREADY_REPORTED,
            )
        else:
            existing_vote.delete()

            vote = VotePostSerializer(
                data={
                    "user": user.id,
                    "poll": request.data["poll"],
                    "option": request.data["option"],
                }
            )
            status_code = status.HTTP_200_OK

        if vote.is_valid():
            vote.save()

        return Response(vote.data, status=status_code)
