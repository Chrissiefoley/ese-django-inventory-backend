from rest_framework import serializers
from .models import User, UserInfo, Staff
from django.db import transaction
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ('employee_id', 'contact_info', 'avatar')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    employee_id = serializers.CharField(write_only=True, required=True)
    contact_info = serializers.CharField(write_only=True, required=True)
    avatar = serializers.URLField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'employee_id', 'contact_info', 'avatar')

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        contact_info = validated_data.pop('contact_info')
        avatar = validated_data.pop('avatar', '')
        email = validated_data.get('email', '')

        is_verified = Staff.objects.filter(
            employee_id=employee_id,
            email=email
        ).exists()

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=email,
                password=validated_data['password'],
                role='viewer',  
                is_staff_verified=is_verified  
            )
            UserInfo.objects.create(
                user=user,
                employee_id=employee_id,
                contact_info=contact_info,
                avatar=avatar
            )
        return user

class UserSerializer(serializers.ModelSerializer):
    user_info = UserInfoSerializer()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'is_staff_verified', 'user_info')

class UserProfileUpdateSerializer(serializers.Serializer):
    avatar = serializers.URLField(required=False, allow_blank=True)
    contact_info = serializers.CharField(required=False, max_length=100, allow_blank=True)
    email = serializers.EmailField(required=False)

    def validate_avatar(self, value):
        if value:
            validator = URLValidator()
            try:
                validator(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Invalid URL format")

            if 'cloudinary.com' not in value and value != '':
                raise serializers.ValidationError("Avatar must be hosted on Cloudinary")
        return value

    def update(self, instance, validated_data):
        if 'email' in validated_data:
            instance.email = validated_data['email']
            instance.save()

        user_info = instance.user_info
        if 'avatar' in validated_data:
            user_info.avatar = validated_data['avatar']
        if 'contact_info' in validated_data:
            user_info.contact_info = validated_data['contact_info']
        user_info.save()

        return instance