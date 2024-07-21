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
)
from rest_framework.settings import api_settings
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
        return Vote.objects.filter(poll=poll_id).order_by("-id")
    except Vote.DoesNotExist:
        return []


def get_vote_for_existing_poll(
    user: User,
    poll_id: str,
) -> Vote:
    try:
        return Vote.objects.get(user=user.id, poll=poll_id)
    except Vote.DoesNotExist:
        return None


class PollList(APIView):
    queryset = Poll.objects.all().order_by("-created_at")
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @property
    def paginator(self):
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)

    def get(self, request):
        page = self.paginate_queryset(self.queryset)

        if page is None:
            page = 1

        serializer = PollSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

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

        data = {
            "id": poll.id,
            "title": poll.title,
            "created_at": poll.created_at,
            "remaining_seconds": poll.remaining_seconds,
            "options": options,
        }

        ip = get_client_ip(request)
        user = get_user_from_ip(ip)
        existing_vote = get_vote_for_existing_poll(user, poll.id)

        data["user_has_voted"] = True if existing_vote != None else False

        if poll.votes_visible:
            data["votes"] = votes
        else:
            data["votes"] = votes if data["user_has_voted"] else None

        serializer = PollDetailSerializer(data)

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
        existing_vote = get_vote_for_existing_poll(user, request.data["poll"])

        if existing_vote is not None and not poll.votes_changable:
            return Response(
                {
                    "message": "This vote doesn't allow changing the selected option.",
                },
                status=status.HTTP_208_ALREADY_REPORTED,
            )

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
