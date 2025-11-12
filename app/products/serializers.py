"""
Products API Serializers
Following Google/Fortune 500 best practices with drf-spectacular
"""

from rest_framework import serializers

from .models import MainCategory, Product, SubCategory


class MainCategorySerializer(serializers.ModelSerializer):
    """
    Main product categories (Insurance, Loans, etc.)
    Read-only for agents
    """

    sub_categories_count = serializers.SerializerMethodField()

    class Meta:
        model = MainCategory
        fields = [
            "id",
            "name",
            "slug",
            "icon",
            "description",
            "active",
            "display_order",
            "sub_categories_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_sub_categories_count(self, obj):
        """Count of active sub-categories"""
        return obj.sub_categories.filter(active=True).count()


class SubCategorySerializer(serializers.ModelSerializer):
    """
    Sub-categories (Health Insurance, Life Insurance, etc.)
    Used for insurance type selection
    """

    main_category_name = serializers.CharField(source="main_category.name", read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = [
            "id",
            "main_category",
            "main_category_name",
            "name",
            "slug",
            "icon",
            "description",
            "active",
            "display_order",
            "form_template",
            "products_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_products_count(self, obj):
        """Count of active products in this sub-category"""
        return obj.products.filter(active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight product serializer for list views
    """

    sub_category_name = serializers.CharField(source="sub_category.name", read_only=True)
    main_category_name = serializers.CharField(
        source="sub_category.main_category.name", read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "sub_category",
            "sub_category_name",
            "main_category_name",
            "active",
            "created_at",
        ]
        read_only_fields = fields


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full product details including custom fields and form template
    """

    sub_category = SubCategorySerializer(read_only=True)
    main_category_name = serializers.CharField(
        source="sub_category.main_category.name", read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "sub_category",
            "main_category_name",
            "key_features",
            "commission_rate",
            "commission_type",
            "custom_fields",
            "custom_form_fields",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
