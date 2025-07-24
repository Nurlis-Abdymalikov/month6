from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.cache import cache

class UserBaseSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=150)
    password = serializers.CharField()


class AuthValidateSerializer(UserBaseSerializer):
    pass


class RegisterValidateSerializer(UserBaseSerializer):
    first_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    username = serializers.CharField(max_length=50, required=False, allow_blank=True)
    def validate_email(self, email):
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Email уже существует!')
        return email


class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        if user.birthday:
            token['birthday'] = user.birthday.isoformat()
        return token

class GoogleLoginSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)


class ConfirmationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        code = attrs.get('code')

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise ValidationError('Пользователь не существует!')

        cache_key = f"confirmation_code_{user_id}"
        stored_code = cache.get(cache_key)

        if stored_code is None:
            raise ValidationError('Код подтверждения истёк или не существует!')

        if stored_code != code:
            raise ValidationError('Неверный код подтверждения!')

        return attrs
