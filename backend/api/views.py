from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics,status
from django.contrib.auth.models import User

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import RegisterSerializer, ActivitySerializer,ProfileSerializer,CommentSerializer,NotificationSerializer

from .models import Activity,Comment, ActivityLike,Notification

from .permissions import IsActivityCreator

from rest_framework.exceptions import NotFound

from django.contrib.auth import authenticate


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile

        return Response({
            "username": request.user.username,
            "email": request.user.email,
            "full_name": profile.full_name,
            "date_of_birth": profile.date_of_birth,
            "city": profile.city,
            "bio": profile.bio,
            "profile_picture": profile.profile_picture.url
            if profile.profile_picture
            else None,
        })

    def patch(self, request):
        profile = request.user.profile

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=400
        )

class ActivityListCreateView(generics.ListCreateAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = Activity.objects.all()

        city = self.request.query_params.get("city")
        search = self.request.query_params.get("search")
        date = self.request.query_params.get("date")
        category = self.request.query_params.get("category")
        ordering = self.request.query_params.get("ordering")

    


        if city:
            queryset = queryset.filter(location__iexact=city)

        if search:
            queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

        if date:
            queryset = queryset.filter(date_time__date=date)

        if category:
            queryset = queryset.filter(category__iexact=category)    

        

        if ordering in ["date_time", "-date_time"]:
            queryset = queryset.order_by(ordering)    

        return queryset

class ActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated,IsActivityCreator]

class JoinActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            activity = Activity.objects.get(pk=pk)
        except Activity.DoesNotExist:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if activity.created_by == request.user:
            return Response(
                {"error": "You created this activity"},
                status=status.HTTP_400_BAD_REQUEST
    )

        if activity.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You have already joined this activity"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if activity.participants.count() >= activity.max_participants:
            return Response(
                {"error": "Activity is full"},
                status=status.HTTP_400_BAD_REQUEST
            )

        activity.participants.add(request.user)

        if activity.created_by != request.user:
            Notification.objects.create(
             recipient=activity.created_by,
                sender=request.user,
                activity=activity,
                notification_type="join",
                message=f"{request.user.username} joined your activity"
    )

        return Response(
            {"message": "Successfully joined the activity"},
            status=status.HTTP_200_OK
        )

class LeaveActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            activity = Activity.objects.get(pk=pk)
        except Activity.DoesNotExist:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not activity.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You have not joined this activity"},
                status=status.HTTP_400_BAD_REQUEST
            )

        activity.participants.remove(request.user)

        return Response(
            {"message": "Successfully left the activity"},
            status=status.HTTP_200_OK
        )

class MyActivitiesView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(created_by=self.request.user)   


class JoinedActivitiesView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(
            participants=self.request.user
        )


class PublicProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        profile = user.profile

        created_activities = Activity.objects.filter(
            created_by=user
        )

        joined_activities = Activity.objects.filter(
            participants=user
        )

        return Response({
            "username": user.username,
            "full_name": profile.full_name,
            "date_of_birth": profile.date_of_birth,
            "city": profile.city,
            "bio": profile.bio,
            "profile_picture": (
                profile.profile_picture.url
                if profile.profile_picture
                else None
            ),
            "created_activities": ActivitySerializer(
                created_activities,
                many=True,
                context={"request": request}
            ).data,

            "joined_activities": ActivitySerializer(
                joined_activities,
                many=True,
                context={"request": request}
            ).data,
        })

class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        activity_id = self.kwargs["activity_id"]

        return Comment.objects.filter(
            activity_id=activity_id
        ).order_by("created_at")

    def get_serializer_class(self):
        return CommentSerializer

    def perform_create(self, serializer):
        activity_id = self.kwargs["activity_id"]

        try:
            activity = Activity.objects.get(pk=activity_id)
        except Activity.DoesNotExist:
            raise NotFound("Activity not found")

        comment = serializer.save(
        user=self.request.user,
        activity=activity
    )

        if activity.created_by != self.request.user:
            Notification.objects.create(
                recipient=activity.created_by,
                sender=self.request.user,
                activity=activity,
                notification_type="comment",
                message=f"{self.request.user.username} commented on your activity"
        )

class CommentDetailView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.user != request.user:
            return Response(
                {"error": "You can only delete your own comments"},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()

        return Response(
            {"message": "Comment deleted successfully"},
            status=status.HTTP_200_OK
        )

class ActivityLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            activity = Activity.objects.get(pk=pk)
        except Activity.DoesNotExist:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        like, created = ActivityLike.objects.get_or_create(
            activity=activity,
            user=request.user
        )

        if not created:
            return Response(
                {"message": "You already liked this activity"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if activity.created_by != request.user:
            Notification.objects.create(
                recipient=activity.created_by,
                sender=request.user,
                activity=activity,
                notification_type="like",
                message=f"{request.user.username} liked your activity"
            )

        return Response(
            {"message": "Activity liked successfully"},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        try:
            like = ActivityLike.objects.get(
                activity_id=pk,
                user=request.user
            )
        except ActivityLike.DoesNotExist:
            return Response(
                {"error": "You have not liked this activity"},
                status=status.HTTP_400_BAD_REQUEST
            )

        like.delete()

        return Response(
            {"message": "Activity unliked successfully"},
            status=status.HTTP_200_OK
        )

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def update(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.user != request.user:
            return Response(
                {"error": "You can only edit your own comments"},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.user != request.user:
            return Response(
                {"error": "You can only delete your own comments"},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()

        return Response(
            {"message": "Comment deleted successfully"},
            status=status.HTTP_200_OK
        )

class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = self.get_serializer(
        queryset,
        many=True
        )

        unread_count = queryset.filter(
            is_read=False
        ).count()

        return Response({
            "unread_count": unread_count,
            "notifications": serializer.data
        })

class NotificationDetailView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        )

    def update(self, request, *args, **kwargs):
        notification = self.get_object()

        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response({
            "message": "Notification marked as read"
        })


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            "message": "All notifications marked as read"
        })    

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        })


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Old password and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {"error": "New password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(new_password)
        request.user.save()

        return Response({
            "message": "Password changed successfully"
        })