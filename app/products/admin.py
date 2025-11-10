from django.contrib import admin
from .models import MainCategory, SubCategory, Product


@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'active', 'display_order', 'created_at']
    list_filter = ['active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'main_category', 'slug', 'active', 'display_order', 'created_at']
    list_filter = ['main_category', 'active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sub_category', 'commission_rate', 'commission_type', 'active', 'created_at']
    list_filter = ['sub_category__main_category', 'sub_category', 'active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
