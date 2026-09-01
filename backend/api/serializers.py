from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Activity,Comment, ActivityLike,Notification
from users.models import Profile



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user

class ActivitySerializer(serializers.ModelSerializer):
    participant_count = serializers.SerializerMethodField()

    def get_participant_count(self, obj):
        return obj.participants.count()

    creator_username = serializers.CharField(
    source="created_by.username",
    read_only=True
    )

    creator_name = serializers.CharField(
    source="created_by.profile.full_name",
    read_only=True
    )

    likes_count = serializers.SerializerMethodField()
    
    def get_likes_count(self, obj):
            return obj.likes.count()

    is_liked = serializers.SerializerMethodField()

    def get_is_liked(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return obj.likes.filter(
             user=request.user
        ).exists()

    class Meta:
        model = Activity
        fields = [
            "id",
            "title",
            "description",
            "location",
            "date_time",
            "max_participants",
            "created_by",
            "creator_username",
            "creator_name",
            "participants",
            "participant_count",
            "created_at",
            "category",
            "likes_count",
            "is_liked",
        ]
        read_only_fields = ["id", "created_by", "created_at","participants"]       

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "date_of_birth",
            "city",
            "bio",
            "profile_picture",
        ]

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "activity",
            "user",
            "username",
            "text",
            "created_at",
        ]
        read_only_fields = [
            "activity",
            "user",
            "created_at",
        ]

class ActivityLikeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ActivityLike
        fields = [
            "id",
            "activity",
            "user",
            "created_at",
            
        ]
        read_only_fields = [
            "user",
            "created_at",
        ]

class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "sender_username",
            "activity",
            "notification_type",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "sender",
            "activity",
            "notification_type",
            "message",
            "created_at",
        ]