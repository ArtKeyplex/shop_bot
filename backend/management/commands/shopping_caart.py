from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from backend.models import (ProductCategory, ProductSubcategory,
                            Product, ShoppingCart, User)


class ShoppingCartStates(StatesGroup):
    waiting_for_delete_confirmation = State()
    waiting_for_product_deletion = State()
    waiting_for_deletion = State()
    waiting_for_address = State()


async def start_cart(message: types.Message, state: FSMContext):
    user = await User.from_message(message)
    # показываем корзину
    cart_markup = InlineKeyboardMarkup()
    async for product in ShoppingCart.objects.filter(user=user).select_related('product'):
        button = InlineKeyboardButton(
            text=f'{product.product.name} {product.amount} шт.',
            callback_data=f'shopping_cart_{product.id}')
        cart_markup.add(button)
    await message.answer('Ваша корзина', reply_markup=cart_markup)
    yes_no_markup = InlineKeyboardMarkup(row_width=2)
    yes_button = InlineKeyboardButton(text='Да',
                                      callback_data='delete_cart_yes')
    no_button = InlineKeyboardButton(text='Нет, перейти к оформлению',
                                     callback_data='delete_cart_no')
    yes_no_markup.add(yes_button, no_button)
    await message.answer('Хотите ли вы что-то удалить?',
                         reply_markup=yes_no_markup)
    await ShoppingCartStates.waiting_for_delete_confirmation.set()


async def choose_product_to_delete(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user = await User.from_message(callback_query.message)
    # Check if user has confirmed they want to delete the product
    confirmed = callback_query.data.startswith('delete_cart_yes')
    if confirmed:
        try:
            cart_markup = InlineKeyboardMarkup()
            async for item in ShoppingCart.objects.filter(
                    user=user).select_related(
                    'product'):
                button = InlineKeyboardButton(
                    text=f'{item.product.name} {item.amount} шт.',
                    callback_data=f'delete_{item.product.id}')
                cart_markup.add(button)
            await callback_query.message.answer(
                'Выберите товар, который вы хотите удалить:',
                reply_markup=cart_markup)
            await ShoppingCartStates.waiting_for_product_deletion.set()

        except ShoppingCart.DoesNotExist:
            await callback_query.message.answer('Товар не найден в корзине')
    else:
        await callback_query.message.answer('Удаление отменено')


async def delete_product_from_cart(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(callback_query=callback_query)

    user = await User.from_message(callback_query.message)

    # Get the selected product ID from the callback data
    product_id = int(callback_query.data.split('_')[-1])

    try:
        # Get the ShoppingCart object for the selected product
        cart_item = await sync_to_async(ShoppingCart.objects.get)(
            user=user,
            product_id=product_id
        )

        # Delete the selected product from the shopping cart
        await sync_to_async(cart_item.delete)()
        await callback_query.message.answer('Товар удален из корзины')
        await start_cart(callback_query.message, state)

    except ShoppingCart.DoesNotExist:
        await callback_query.message.answer('Товар не найден в корзине')


def register_handlers_cart(dp: Dispatcher):
    dp.register_message_handler(start_cart, commands="shopping_cart", state="*")
    dp.register_callback_query_handler(choose_product_to_delete,
                                       lambda c: c.data.startswith(
                                           'delete_cart_'),
                                       state=ShoppingCartStates.waiting_for_delete_confirmation)
    dp.register_callback_query_handler(delete_product_from_cart,
                                       lambda c: c.data.startswith(
                                           'delete_'),
                                       state=ShoppingCartStates.waiting_for_product_deletion
                                       )

