from typing import Tuple

from aiogram import types
from django.core.validators import MinValueValidator
from django.db import models
from . import utils


class User(models.Model):
    user_id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=32, null=True, blank=True)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    language_code = models.CharField(max_length=8, null=True, blank=True,
                                     help_text="Telegram client's lang")
    deep_link = models.CharField(max_length=64, null=True, blank=True)

    is_blocked_bot = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    async def from_message(cls, message: types.Message) -> Tuple['User', bool]:
        if message.from_user.is_bot:
            data = {
                'user_id': message.chat.id,
                'username': message.chat.username,
                'first_name': message.chat.first_name,
                'last_name': message.chat.last_name,
            }
        else:
            data = {
                'user_id': message.from_user.id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'language_code': message.from_user.language_code,
        }

        user, _ = await cls.objects.aget_or_create(user_id=data['user_id'],
                                                   defaults=data)
        return user

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class ProductSubcategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(ProductCategory, to_field='name', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='product_photos/', blank=True, null=True)
    subcategory = models.ForeignKey(ProductSubcategory, to_field='name', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Пользователь'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Товар'
    )

    amount = models.SmallIntegerField(
        'Количество товара',
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'],
                                    name='unique cart')
        ]

