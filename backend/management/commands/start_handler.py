from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def start_command(message: types.Message, state: FSMContext):
    # приветствуем пользователя и показываем наш функционал
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    catalog_btn = KeyboardButton('/catalog')
    cart_btn = KeyboardButton('/shopping_cart')
    faq_btn = types.KeyboardButton('/faq')
    keyboard.add(catalog_btn, cart_btn, faq_btn)
    await message.reply("Приветствую в нашем магазине. Что вы хотите?",
                        reply_markup=keyboard)


def register_handlers_start(dp: Dispatcher):
    # при необходимости можно поменять начало так, чтобы вместо команд
    # были понятные для пользователя слова и смайлики: Каталог, Корзина и т.д
    dp.register_message_handler(start_command, commands='start', state='*')
