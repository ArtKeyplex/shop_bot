from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from backend.models import (ProductCategory, ProductSubcategory,
                            Product, ShoppingCart, User)


# Поработать над созданием корзины и еды


class CatalogStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_confirmation = State()


async def cmd_catalog(message: types.Message, state: FSMContext):
    await CatalogStates.waiting_for_category.set()
    # узнаем категорию
    category_markup = InlineKeyboardMarkup()
    async for category in ProductCategory.objects.all():
        button = InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}")
        category_markup.add(button)
    await message.answer('Какая категория вам нужна?', reply_markup=category_markup)


async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split("_")[1])
    category = await ProductCategory.objects.aget(id=category_id)
    await state.update_data(category=category)

    # переходим к следующему состоянию
    await CatalogStates.waiting_for_subcategory.set()

    # Узнаем нужную категорию
    subcategory_markup = InlineKeyboardMarkup()
    async for subcategory in ProductSubcategory.objects.filter(category=category).all():
        button = InlineKeyboardButton(text=subcategory.name, callback_data=f"subcategory_{subcategory.id}")
        subcategory_markup.add(button)

    await callback_query.message.answer("Какая подкатегория вам нужна?", reply_markup=subcategory_markup)


async def process_subcategory(callback_query: types.CallbackQuery, state: FSMContext):
    # Сохраняем данные о подкатегории
    subcategory_id = int(callback_query.data.split("_")[1])
    subcategory = await ProductSubcategory.objects.aget(id=subcategory_id)
    await state.update_data(subcategory=subcategory)

    # переходим к следующему состоянию
    await CatalogStates.waiting_for_product.set()

    # показываем продукты
    products_markup = InlineKeyboardMarkup()
    async for product in Product.objects.filter(subcategory=subcategory):
        button = InlineKeyboardButton(text=product.name, callback_data=f"product_{product.id}")
        products_markup.add(button)
    await callback_query.message.answer('Товары:', reply_markup=products_markup)


async def process_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = int(callback_query.data.split("_")[1])
    product = await Product.objects.aget(id=product_id)
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
    data = await state.get_data()
    product = data.get('product')
    await state.update_data(quantity=quantity)
    # Add the product to the shopping cart
    cart, created = await ShoppingCart.objects.aget_or_create(user=user,
                                                      product=product,
                                                      amount=quantity)
    if created:
        await state.update_data(cart=cart)

        # Show the shopping cart

        # Set the state back to waiting_for_product
        await CatalogStates.waiting_for_confirmation.set()

        data = await state.get_data()
        product = data.get('product')
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
    else:
        await message.answer(f'Вы уже добавили {product}')
        await CatalogStates.waiting_for_product.set()
        return


async def process_confirm(message: types.Message, state: FSMContext):
    # Get the user and the shopping cart from the state
    if message.text.lower() == 'да':
        data = await state.get_data()
        subcategory = data.get('subcategory')
        await CatalogStates.waiting_for_product.set()
        products_markup = InlineKeyboardMarkup()
        async for product in Product.objects.filter(subcategory=subcategory):
            button = InlineKeyboardButton(text=product.name,
                                          callback_data=f"product_{product.id}")
            products_markup.add(button)
        await message.answer('Товары:', reply_markup=products_markup)
    else:
        print('хахаха')

# # Define the /shoppingcart command handler
# @dp.message_handler(commands=['shoppingcart'])
# async def cmd_shopping_cart(message: types.Message, state: FSMContext):
#     # Show the shopping cart
#     await message.reply("Here is your current shopping cart:")
#     await message.reply(get_shopping_cart_text(state))
#
# # Define the /faq command handler
# @dp.message_handler(commands=['faq'])
# async def cmd_faq(message: types.Message):
#     # Send the FAQ message
#     await message.reply("Here are some frequently asked questions:")


def register_handlers_catalog(dp: Dispatcher):
    dp.register_message_handler(cmd_catalog, commands="catalog", state="*")
    dp.register_callback_query_handler(process_category,
                                       lambda c: c.data.startswith('category_'),
                                       state=CatalogStates.waiting_for_category)
    dp.register_callback_query_handler(process_subcategory,
                                       lambda c: c.data.startswith('subcategory_'),
                                       state=CatalogStates.waiting_for_subcategory)
    dp.register_callback_query_handler(process_product_callback, lambda c: c.data.startswith('product_'), state=CatalogStates.waiting_for_product)
    dp.register_message_handler(process_quantity,
                                state=CatalogStates.waiting_for_quantity)
    dp.register_message_handler(process_confirm, state=CatalogStates.waiting_for_confirmation)