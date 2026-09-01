from django.urls import path
from .views import(RegisterView, ProfileView,ActivityListCreateView,JoinActivityView,LeaveActivityView,
                   ActivityDetailView,MyActivitiesView,JoinedActivitiesView,PublicProfileView,CommentListCreateView,CommentDetailView,ActivityLikeView,NotificationListView,NotificationDetailView,MarkAllNotificationsReadView,CurrentUserView,ChangePasswordView)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),

    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("activities/", ActivityListCreateView.as_view(), name="activities"),
    path(
    "activities/<int:pk>/join/",
    JoinActivityView.as_view(),
    name="join_activity",),
    path(
    "activities/<int:pk>/leave/",
    LeaveActivityView.as_view(),
    name="leave_activity",
),
    path(
    "activities/<int:pk>/",
    ActivityDetailView.as_view(),
    name="activity_detail",
),
    path(
    "my-activities/",
    MyActivitiesView.as_view(),
    name="my_activities",
),

    path(
    "joined-activities/",
    JoinedActivitiesView.as_view(),
    name="joined_activities",
),
    path("users/<int:pk>/", PublicProfileView.as_view(), name="public-profile"),

    path(
    "activities/<int:activity_id>/comments/",
    CommentListCreateView.as_view(),
    name="activity-comments",
),

    path(
    "comments/<int:pk>/",
    CommentDetailView.as_view(),
    name="comment-detail",
),

    path(
    "activities/<int:pk>/like/",
    ActivityLikeView.as_view(),
    name="activity-like",
),

    path(
    "notifications/",
    NotificationListView.as_view(),
    name="notifications",
),

    path(
    "notifications/<int:pk>/read/",
    NotificationDetailView.as_view(),
    name="notification-read",
),

    path(
    "notifications/read-all/",
    MarkAllNotificationsReadView.as_view(),
    name="notifications-read-all",
),

    path(
    "me/",
    CurrentUserView.as_view(),
    name="current-user",
),

    path(
    "change-password/",
    ChangePasswordView.as_view(),
    name="change-password",
),



    
]
