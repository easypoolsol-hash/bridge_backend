"""
Products API ViewSets
Following Google/Fortune 500 best practices
Read-only access for agents, full access for admins
"""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MainCategory, Product, SubCategory
from .serializers import (
    MainCategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    SubCategorySerializer,
)


class ProductFilter(filters.FilterSet):
    """Filtering for products"""

    sub_category = filters.NumberFilter(field_name="sub_category__id")
    main_category = filters.NumberFilter(field_name="sub_category__main_category__id")
    active = filters.BooleanFilter(field_name="active")

    class Meta:
        model = Product
        fields = ["sub_category", "main_category", "active"]


@extend_schema_view(
    list=extend_schema(
        summary="List all main categories",
        description="Returns active main categories (Insurance, Loans, etc.)",
        tags=["Products"],
    ),
    retrieve=extend_schema(
        summary="Get main category details",
        description="Get details of a specific main category",
        tags=["Products"],
    ),
)
class MainCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for main product categories
    Agents can only view, admins can manage via Django admin
    """

    queryset = MainCategory.objects.filter(active=True).order_by("display_order", "name")
    serializer_class = MainCategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"


@extend_schema_view(
    list=extend_schema(
        summary="List sub-categories",
        description="Returns insurance types (Health, Life, Car, etc.)",
        tags=["Products"],
    ),
    retrieve=extend_schema(
        summary="Get sub-category details",
        description="Get details of a specific insurance type",
        tags=["Products"],
    ),
)
class SubCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for sub-categories (Insurance types)
    """

    queryset = SubCategory.objects.filter(active=True).select_related("main_category").order_by(
        "main_category", "display_order", "name"
    )
    serializer_class = SubCategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"
    filterset_fields = ["main_category"]

    def get_queryset(self):
        """Filter by main_category if provided"""
        queryset = super().get_queryset()

        # Filter by main category slug
        main_category = self.request.query_params.get("main_category_slug")
        if main_category:
            queryset = queryset.filter(main_category__slug=main_category)

        return queryset


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Returns products filtered by category",
        tags=["Products"],
    ),
    retrieve=extend_schema(
        summary="Get product details",
        description="Get full details of a specific product",
        tags=["Products"],
    ),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for products
    Agents can browse and share products with customers
    """

    queryset = Product.objects.filter(active=True).select_related(
        "sub_category", "sub_category__main_category"
    ).order_by("sub_category", "name")
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"
    filterset_class = ProductFilter

    def get_serializer_class(self):
        """Use different serializers for list vs detail"""
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @extend_schema(
        summary="Get featured products",
        description="Returns top products for agents to promote",
        tags=["Products"],
    )
    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured/recommended products"""
        # For now, return first 10 active products
        # In future: add is_featured field or use AI recommendations
        products = self.get_queryset()[:10]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
