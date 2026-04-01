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
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    employee_id = serializers.CharField(write_only=True, required=True)
    contact_info = serializers.CharField(write_only=True, required=False, allow_blank=True)
    avatar = serializers.URLField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'employee_id', 'contact_info', 'avatar')

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")

        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")

        if not any(char.islower() for char in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number")

        return value

    def validate_employee_id(self, value):
        if UserInfo.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("This employee ID is already registered")
        return value

    def validate(self, data):
        employee_id = data.get('employee_id')
        email = data.get('email')

        if not Staff.objects.filter(employee_id=employee_id, email=email).exists():
            raise serializers.ValidationError({
                'employee_id': 'Employee ID and email combination not found in staff records. Please contact HR.'
            })

        return data

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        contact_info = validated_data.pop('contact_info', '')
        avatar = validated_data.pop('avatar', '')
        email = validated_data.get('email', '')

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=email,
                password=validated_data['password'],
                role='staff',
                is_staff_verified=True
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
