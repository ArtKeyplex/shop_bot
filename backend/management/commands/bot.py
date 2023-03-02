from aiogram.utils import executor
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


from .catalog import register_handlers_catalog
from .shopping_caart import register_handlers_cart
from .start_handler import register_handlers_start
from .faq_handler import register_handlers_faq

bot = Bot(token='5430634553:AAGFfvQr_JnXfVHoBk8-qr0_OQR76xUNXr4')
dp = Dispatcher(bot=bot, storage=MemoryStorage())

register_handlers_start(dp)
register_handlers_catalog(dp)
register_handlers_cart(dp)
register_handlers_faq(dp)


class Command(BaseCommand):

    def handle(self, *args, **options):
        executor.start_polling(dp)
