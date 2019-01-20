import telebot
import os
import time
from telebot import types
from storage import db
from currency_parser import CurrencyHandler
from location_analyzer import LocationAnalyzer

START, NAME, LOCATION, PHOTO, CONFIRMATION = range(5)


def create_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=c, callback_data=c)
               for c in ['EUR', 'USD']]
    keyboard.add(*buttons)
    return keyboard


currency_info = CurrencyHandler(db.conn)
location_info = LocationAnalyzer(db.conn)
bot = telebot.TeleBot(os.environ.get('TOKEN'))


@bot.message_handler(commands=['add'])
def handle_message(message):
    bot.send_message(message.chat.id, text='Напишите название места')
    db.update_state(message, NAME)


@bot.message_handler(func=lambda message: db.get_state(message) == NAME)
def handle_message(message):
    db.add_item(message.chat.id, message.text)
    bot.send_message(message.chat.id, text='Пришлите координаты места')
    db.update_state(message, LOCATION)


@bot.message_handler(content_types=['location', 'photo', 'text'],
                     func=lambda message: db.get_state(message) == LOCATION)
def handle_location(message):
    if message.content_type != 'location':
        bot.send_message(message.chat.id, text='Локация обязательна для нового места')
        return

    db.add_location(message.chat.id, message.location)
    bot.send_message(message.chat.id, text='Пришлите фото (можно отказаться)')
    db.update_state(message, PHOTO)


@bot.message_handler(content_types=['photo', 'text', 'location'],
                     func=lambda message: db.get_state(message) == PHOTO)
def handle_message(message):
    if message.content_type != 'photo':
        db.add_item(message.chat.id, 'no photo')
    else:
        photo_id = message.json.get('photo')[2]['file_id']
        db.add_item(message.chat.id, photo_id)
    bot.send_message(message.chat.id, text='Сохраняем? Да/Нет')
    db.update_state(message, CONFIRMATION)


@bot.message_handler(func=lambda message: db.get_state(message) == CONFIRMATION)
def handle_message(message):
    if message.text.lower() == 'да':
        db.confirm_place(message.chat.id)
        bot.send_message(message.chat.id, text='Сохранено')
    else:
        db.confirm_place(message.chat.id, cancel=True)
        bot.send_message(message.chat.id, text='Отменено')
    db.update_state(message, START)


@bot.message_handler(commands=['list'])
def recent_places(message):
    places = location_info.get_recent_places(message.chat.id)

    if isinstance(places, str):
        bot.send_message(message.chat.id, text=places)
        return

    for place in places:
        bot.send_message(message.chat.id, text=place.name)
        bot.send_location(message.chat.id, *place.location)
        if place.photo != 'no photo':
            bot.send_photo(message.chat.id, place.photo)


@bot.message_handler(commands=['reset'])
def handle_message(message):
    db.erase_places(message.chat.id)
    bot.send_message(message.chat.id, text='Места удалены')


@bot.message_handler(content_types=['location'])
def nearest_places(message):
    places = location_info.get_nearest_places(message.chat.id, message.location)

    if isinstance(places, str):
        bot.send_message(message.chat.id, text=places)
        return

    for place in places:
        bot.send_message(message.chat.id, text=place.name)
        bot.send_location(message.chat.id, *place.location)
        if place.photo != 'no photo':
            bot.send_photo(message.chat.id, place.photo)


@bot.callback_query_handler(func=lambda x: True)
def callback_handler(callback_query):
    message = callback_query.message
    text = callback_query.data
    currency, value = currency_info.currency_interpreter(text.lower())
    currency_answer(currency, value, message)


@bot.message_handler(commands=['rate'])
def handle_message(message):
    currency, value = currency_info.currency_interpreter(message.text.lower())
    keyboard = create_keyboard()
    currency_answer(currency, value, message, keyboard)


def currency_answer(currency, value, message, keyboard=None):
    if currency and value:
        bot.send_message(message.chat.id, text='Курс {} равен {}₽'.format(currency, value),
                         reply_markup=keyboard)
    elif not currency:
        bot.send_message(message.chat.id, 'Выберите валюту', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Сервер недоступен. Попробуйте позже', reply_markup=keyboard)


@bot.message_handler()
def handle_message(message):
    bot.send_message(chat_id=message.chat.id, text='Отправьте свою локацию, чтобы увидеть места поблизости. \n'
                                                   'Добавить новое место можно командой /add \n'
                                                   'Удалить все ранее добавленное – /reset \n'
                                                   'Чтобы увидеть список команд, введите /'
                     )


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            time.sleep(15)
