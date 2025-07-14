from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import CustomUser
from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
from .models import ConfirmationCode
import random
import string
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.serializers import CustomTokenObtainSerializer


class AuthorizationAPIView(CreateAPIView):
    serializer_class = AuthValidateSerializer
    def post(self, request):
        serializer = AuthValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(**serializer.validated_data)

        if user:
            if not user.is_active:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={'error': 'User account is not activated yet!'}
                )

            token, _ = Token.objects.get_or_create(user=user)
            return Response(data={'key': token.key})

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={'error': 'User credentials are wrong!'}
        )


class RegistrationAPIView(CreateAPIView):
    serializer_class = RegisterValidateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        # Use transaction to ensure data consistency
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                username=validated_data.get('username', ''),
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                is_active=False
            )

            # Create a random 6-digit code
            code = ''.join(random.choices(string.digits, k=6))

            confirmation_code = ConfirmationCode.objects.create(
                user=user,
                code=code
            )

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_id': user.id,
                'confirmation_code': code
            }
        )


class ConfirmUserAPIView(CreateAPIView):
    serializer_class = ConfirmationSerializer
    def post(self, request):
        serializer = ConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']

        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

            ConfirmationCode.objects.filter(user=user).delete()

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'key': token.key
            }
        )
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer