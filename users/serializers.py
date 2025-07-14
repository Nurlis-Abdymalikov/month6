from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ConfirmationCode, CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


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

class ConfirmationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        code = attrs.get('code')

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise ValidationError('User не существует!')

        try:
            confirmation_code = ConfirmationCode.objects.get(user=user)
        except ConfirmationCode.DoesNotExist:
            raise ValidationError('Код подтверждения не найден!')

        if confirmation_code.code != code:
            raise ValidationError('Неверный код подтверждения!')

        return attrs

class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        if user.birthday:
            token['birthday'] = user.birthday.isoformat()
        return token