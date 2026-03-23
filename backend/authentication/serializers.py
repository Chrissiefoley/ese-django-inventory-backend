from rest_framework import serializers
from .models import User, UserInfo
from django.db import transaction

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ('employee_id', 'contact_info', 'avatar')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    employee_id = serializers.CharField(write_only=True, required=True)
    contact_info = serializers.CharField(write_only=True, required=True)
    avatar = serializers.URLField(write_only=True, required=False, allow_blank=True)
    role = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role', 'employee_id', 'contact_info', 'avatar')

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        contact_info = validated_data.pop('contact_info')
        avatar = validated_data.pop('avatar', '')
        role = validated_data.pop('role')

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                role=role
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
        fields = ('id', 'username', 'email', 'role', 'user_info')