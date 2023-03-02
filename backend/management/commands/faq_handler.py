from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

questions_and_answers = {
    'вопрос 1': 'ответ 1',
    'вопрос 2': 'ответ 2',
    'вопрос 3': 'ответ 3'
}


async def faq_command(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    for question in questions_and_answers:
        button = InlineKeyboardButton(text=question,
                                      callback_data=f'{question}_data')
        keyboard.add(button)
    await message.answer('Самые популярные вопросы:', reply_markup=keyboard)


async def handle_question(callback_query: types.CallbackQuery, state: FSMContext):
    question = callback_query.data.split('_')[0]
    answer = questions_and_answers.get(question)
    await callback_query.message.answer(f'Вопрос: {question}\n'
                                        f'Ответ: {answer}')


def register_handlers_faq(dp: Dispatcher):
    dp.register_message_handler(faq_command, commands='faq', state='*')
    dp.register_callback_query_handler(handle_question,
                                       lambda c: c.data.endswith('_data'),
                                       state='*')
