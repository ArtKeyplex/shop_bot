from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from backend.management.commands.pagination import create_keyboard
from backend.models import (ProductCategory, ProductSubcategory,
                            Product, ShoppingCart, User)

CURRENT_PAGE = 1


class CatalogStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_confirmation = State()


async def cmd_catalog(message: types.Message):
    # Wait for user input
    await CatalogStates.waiting_for_category.set()

    # Create category keyboard markup
    category_markup = InlineKeyboardMarkup()

    async for category in ProductCategory.objects.all():
        button = InlineKeyboardButton(text=category.name, callback_data=f"category_{category.name}")
        category_markup.add(button)
    # Send message to user
    await message.answer('Какая категория вам нужна?', reply_markup=category_markup)


async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    get_cat = state_data.get('category')
    if get_cat and get_cat == callback_query.data.split("_")[1]:
        category = get_cat
    else:
        category_name = callback_query.data.split("_")[1]
        category = await ProductCategory.objects.aget(name=category_name)

    await state.update_data(category=category)

    # переходим к следующему состоянию
    await CatalogStates.waiting_for_subcategory.set()

    # Узнаем нужную категорию
    subcategory_markup = InlineKeyboardMarkup()
    async for subcategory in ProductSubcategory.objects.filter(category=category).all():
        button = InlineKeyboardButton(
            text=subcategory.name,
            callback_data=f"category_{category}_"
                          f"{subcategory.name}_subcategory")
        subcategory_markup.add(button)
    back_button = InlineKeyboardButton(text="Вернуться к категориям", callback_data="go_back")
    subcategory_markup.add(back_button)
    await callback_query.message.answer("Какая подкатегория вам нужна?", reply_markup=subcategory_markup)


async def process_subcategory(callback_query: types.CallbackQuery, state: FSMContext):
    # Сохраняем данные о подкатегории
    state_data = await state.get_data()
    get_sub = state_data.get('subcategory')
    category = state_data.get('category')
    if callback_query.data.startswith('go_back'):
        await cmd_catalog(callback_query.message)
    elif get_sub and get_sub.name == await ProductSubcategory.objects.aget(name=get_sub):
        subcategory = state_data.get('subcategory')
        await create_keyboard(callback_query.message, subcategory, category)
    else:
        subcategory_name = callback_query.data.split("_")[2]
        subcategory = await ProductSubcategory.objects.aget(name=subcategory_name)
        await state.update_data(subcategory=subcategory)

        # переходим к следующему состоянию
        await CatalogStates.waiting_for_product.set()
        await create_keyboard(callback_query.message, subcategory, category)


async def process_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data.endswith('go_sub'):
        await process_category(callback_query, state)
    else:
        product_name = callback_query.data.split("_")[1]
        product = await Product.objects.aget(name=product_name)
        await state.update_data(product=product)

        # Set the state to waiting_for_quantity
        await CatalogStates.waiting_for_quantity.set()

        # Ask for the quantity
        await callback_query.message.answer('Какое количество товара вы хотите?')


async def process_quantity(message: types.Message, state: FSMContext):
    # Save the quantity to the state
    user = await User.from_message(message)
    quantity = message.text
    if not quantity.isdigit():
        await message.answer('Введено неверное значение, введите цифру')
        return
    if int(quantity) <= 0:
        await message.answer('Введите число больше 0')
        return
    data = await state.get_data()
    product = data.get('product')
    await state.update_data(quantity=quantity)
    # Add the product to the shopping cart
    exist = await ShoppingCart.objects.filter(user=user, product=product).aexists()
    if exist:
        await message.answer(f'Вы уже добавили {product}')
        await CatalogStates.waiting_for_product.set()
        return
    else:
        # Set the state back to waiting_for_product
        await CatalogStates.waiting_for_confirmation.set()
        data = await state.get_data()
        smth = await Product.objects.aget(name=product)
        # Show the user the summary of their order
        quantity = int(data.get('quantity'))
        total_price = int(smth.price) * quantity
        summary = f"Товар: {product.name}\nКоличество: {quantity}\nСумма: {total_price} руб."
        await message.reply(f"Пожалуйста, подтвердите ваш заказ:\n\n{summary}",
                            reply_markup=ReplyKeyboardMarkup(
                                [[KeyboardButton('Да')],
                                 [KeyboardButton('Нет')]],
                                resize_keyboard=True))


async def process_confirm(message: types.Message, state: FSMContext):
    # Get the user and the shopping cart from the state
    if message.text.lower() == 'да':
        user = await User.from_message(message)
        data = await state.get_data()
        product = data.get('product')
        quantity = data.get('quantity')
        category = data.get('category')
        await ShoppingCart.objects.acreate(user=user,
                                           product=product, amount=quantity)
        data = await state.get_data()
        subcategory = data.get('subcategory')

        await CatalogStates.waiting_for_product.set()
        await message.answer('Товар успешно добавлен в корзину!')
        await create_keyboard(message, subcategory, category)
    else:
        await message.answer('Что-то пошло не так...')
        return


def register_handlers_catalog(dp: Dispatcher):
    dp.register_message_handler(cmd_catalog, commands="catalog", state="*")
    dp.register_callback_query_handler(
        process_category,
        lambda c: c.data.startswith('category_'),
        state=CatalogStates.waiting_for_category
    )
    dp.register_callback_query_handler(
        process_subcategory,
        lambda c: c.data.endswith('_subcategory')
        or c.data.startswith('go_back'),
        state=CatalogStates.waiting_for_subcategory
    )
    dp.register_callback_query_handler(
        process_product_callback,
        lambda c: c.data.startswith('product_')
        or c.data.endswith('go_sub'),
        state=CatalogStates.waiting_for_product
    )
    dp.register_message_handler(
        process_quantity,
        state=CatalogStates.waiting_for_quantity
    )
    dp.register_message_handler(
        process_confirm,
        state=CatalogStates.waiting_for_confirmation
    )
