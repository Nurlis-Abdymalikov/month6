from collections import OrderedDict
from django.db import transaction
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.core. cache import cache

from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ReviewSerializer,
    ProductWithReviewsSerializer,
    CategoryValidateSerializer,
    ProductValidateSerializer,
    ReviewValidateSerializer
)
from common.permissions import IsOwner, IsAnonymous, IsModeratorPermission

PAGE_SIZE = 5


class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('total', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

    def get_page_size(self, request):
        return PAGE_SIZE


class CategoryListCreateAPIView(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = CategoryValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = Category.objects.create(**serializer.validated_data)
        return Response(data=CategorySerializer(category).data,
                        status=status.HTTP_201_CREATED)


class CategoryDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CategoryValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance.name = serializer.validated_data.get('name')
        instance.save()

        return Response(data=CategorySerializer(instance).data)


from datetime import datetime, timedelta

class ProductListCreateAPIView(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        cached_data = cache.get('product_list')
        if cached_data:
            print("работает redis")
            return Response(data=cached_data, status=status.HTTP_200_OK)
        response = super().get(request, *args, **kwargs)
        print("обычный response")
        if response.data and len(response.data) > 0:
            cache.set("product_list", response.data, timeout=120)
        return response

    def post(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        birthday_str = None
        if request.auth:
            birthday_str = request.auth.get('birthday')

        if not birthday_str:
            return Response({'detail': 'Дата рождения не указана.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            birthday = datetime.fromisoformat(birthday_str).date()
        except ValueError:
            return Response({'detail': 'Неверный формат даты рождения в токене.'},
                            status=status.HTTP_400_BAD_REQUEST)

        today = datetime.today().date()
        age = (today - birthday).days // 365

        if age < 18:
            return Response({'detail': 'Вам должно быть 18 лет, чтобы создать продукт.'},
                            status=status.HTTP_403_FORBIDDEN)

        if request.user.is_staff:
            return Response({'detail': 'Модераторам запрещено создавать продукты.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = ProductValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data.get('title')
        description = serializer.validated_data.get('description')
        price = serializer.validated_data.get('price')
        category = serializer.validated_data.get('category')

        product = Product.objects.create(
            title=title,
            description=description,
            price=price,
            category=category,
            owner=request.user,
        )

        return Response(data=ProductSerializer(product).data,
                        status=status.HTTP_201_CREATED)




class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    lookup_field = 'id'
    permission_classes = [IsOwner | IsModeratorPermission | IsAnonymous]

    def put(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = ProductValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product.title = serializer.validated_data.get('title')
        product.description = serializer.validated_data.get('description')
        product.price = serializer.validated_data.get('price')
        product.category = serializer.validated_data.get('category')
        product.save()

        return Response(data=ProductSerializer(product).data)

class OwnerProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user).select_related('category')

class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    pagination_class = CustomPagination
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        serializer = ReviewValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get validated data
        text = serializer.validated_data.get('text')
        stars = serializer.validated_data.get('stars')
        product = serializer.validated_data.get('product')

        # Create review
        review = Review.objects.create(
            text=text,
            stars=stars,
            product=product
        )

        return Response(data=ReviewSerializer(review).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        serializer = ReviewValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review.text = serializer.validated_data.get('text')
        review.stars = serializer.validated_data.get('stars')
        review.product = serializer.validated_data.get('product')
        review.save()

        return Response(data=ReviewSerializer(review).data)


class ProductWithReviewsAPIView(APIView):
    def get(self, request):
        paginator = CustomPagination()
        products = Product.objects.select_related('category').prefetch_related('reviews').all()
        result_page = paginator.paginate_queryset(products, request)

        serializer = ProductWithReviewsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)