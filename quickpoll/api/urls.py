from django.urls import path
from .views import PollList, PollDetails, UserList

urlpatterns = [
    path("polls/", PollList.as_view(), name="polls"),
    path("polls/<uuid:pk>", PollDetails.as_view(), name="poll_details"),
    path("users/", UserList.as_view(), name="users"),
]
