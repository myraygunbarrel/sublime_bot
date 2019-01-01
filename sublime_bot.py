import telebot
from telebot import types
from collections import defaultdict
from config import TOKEN
from storage import db

START, NAME, LOCATION, PHOTO, CONFIRMATION = range(5)
USER_STATE = defaultdict(lambda: START)


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state


def currency_interpreter(message):
    for key in db.cur_synonym:
        for syn in key:
            if syn in message:
                proper_key = db.cur_synonym[key]
                return proper_key, db.get_currency()[proper_key.encode()].decode()
    return None, None


def create_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=c, callback_data=c)
               for c in ['EUR', 'USD']]
    keyboard.add(*buttons)
    return keyboard


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['add'])
def handle_message(message):
    bot.send_message(message.chat.id, text='Напиши название места')
    update_state(message, NAME)


@bot.message_handler(func=lambda message: get_state(message) == NAME)
def handle_message(message):
    db.add_place(message.chat.id, message.text)
    bot.send_message(message.chat.id, text='Пришли координаты места')
    update_state(message, LOCATION)
    print(db.storage_tmp)


@bot.message_handler(content_types=['location'], func=lambda message: get_state(message) == LOCATION)
def handle_location(message):
    db.add_location(message.chat.id, message.location)
    bot.send_message(message.chat.id, text='Пришли фото (если не хочешь, так и скажи)')
    update_state(message, PHOTO)


@bot.message_handler(content_types=['photo', 'text'],
                     func=lambda message: get_state(message) == PHOTO)
def handle_message(message):
    if message.content_type == 'text':
        db.add_photo(message.chat.id, 'no photo')
    else:
        photo_id = message.json.get('photo')[2]['file_id']
        db.add_photo(message.chat.id, photo_id)
    bot.send_message(message.chat.id, text='Сохраняем? Да/Нет')
    update_state(message, CONFIRMATION)
    print(db.storage_tmp)


@bot.message_handler(func=lambda message: get_state(message) == CONFIRMATION)
def handle_message(message):
    if message.text.lower() == 'да':
        db.confirm_place(message.chat.id)
        bot.send_message(message.chat.id, text='Сохранено')
    else:
        db.cancel_place(message.chat.id)
        bot.send_message(message.chat.id, text='Отменено')
    update_state(message, START)


@bot.message_handler(commands=['list'])
def handle_message(message):
    places = db.get_recent_places(message.chat.id)
    for place in places:
        print(place)
        bot.send_message(message.chat.id, text=place.name)
        bot.send_location(message.chat.id, *place.location)
        if place.photo != 'no photo':
            bot.send_photo(message.chat.id, place.photo)


@bot.message_handler(content_types=['location'])
def nearest_places(message):
    places = db.get_nearest_places(message.chat.id, message.location)
    for place in places:
        print(place)
        bot.send_message(message.chat.id, text=place.name)
        bot.send_location(message.chat.id, *place.location)
        if place.photo != 'no photo':
            bot.send_photo(message.chat.id, place.photo)



@bot.callback_query_handler(func=lambda x: True)
def callback_handler(callback_query):
    message = callback_query.message
    text = callback_query.data
    currency, value = currency_interpreter(text.lower())
    currency_answer(currency, value, message)


@bot.message_handler(content_types=['location'], func=lambda message: get_state(message) == START)
def handle_location(message):
    im = open('image2.jpg', 'rb')
    bot.send_photo(message.chat.id, im, caption='Опора моста, возле ИКЕА-Химки')
    bot.send_location(message.chat.id, 55.920032, 37.392755)


@bot.message_handler(commands=['rate'])
def handle_message(message):
    print(message.text, message.chat.id)
    currency, value = currency_interpreter(message.text.lower())
    keyboard = create_keyboard()
    currency_answer(currency, value, message, keyboard)


def currency_answer(currency, value, message, keyboard=None):
    if currency:
        bot.send_message(chat_id=message.chat.id, text='ты спросил про валюту')
        bot.send_message(message.chat.id, text='Курс {} равен {}'.format(currency, value),
                         reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'узнай курс валют', reply_markup=keyboard)


@bot.message_handler()
def handle_message(message):
    print(message.text, message.chat.id)
    bot.send_message(chat_id=message.chat.id, text='здаров')


# telebot.apihelper.proxy = {'https': '185.115.42.27:3128'}
bot.polling()
