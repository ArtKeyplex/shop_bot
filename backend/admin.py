from django.contrib import admin
from backend.models import Product, ProductCategory, ProductSubcategory, ShoppingCart


# Register your models here.


@admin.register(ProductCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProductSubcategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')


@admin.register(Product)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'image', 'subcategory')


@admin.register(ShoppingCart)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'amount')
