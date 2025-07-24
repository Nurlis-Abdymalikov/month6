import os
import requests
from rest_framework.generics import CreateAPIView
from django.contrib.auth import get_user_model
from users.serializers import GoogleLoginSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class GoogleLoginAPIView(CreateAPIView):
    serializer_class = GoogleLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']


        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
                "redirect_uri": os.environ.get('GOOGLE_REDIRECT_URI'),
                "grant_type": "authorization_code"
            }
        )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return Response({"error": "Invalid access token"}, status=400)


        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        print(f"user_data {user_info}")

        email = user_info.get("email")
        first_name = user_info.get("given_name")
        last_name = user_info.get("family_name")
        picture = user_info.get("picture")


        user, created = User.objects.get_or_create(email=email)

        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.avatar = picture or user.avatar
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar": user.avatar
            }
        })
