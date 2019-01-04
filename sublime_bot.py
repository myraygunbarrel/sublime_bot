import telebot
import os
from telebot import types
from storage import db

START, NAME, LOCATION, PHOTO, CONFIRMATION = range(5)


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


bot = telebot.TeleBot(os.environ.get('TOKEN', 0))


@bot.message_handler(commands=['add'])
def handle_message(message):
    bot.send_message(message.chat.id, text='Напиши название места')
    db.update_state(message, NAME)


@bot.message_handler(func=lambda message: db.get_state(message) == NAME)
def handle_message(message):
    db.add_item(message.chat.id, message.text)
    bot.send_message(message.chat.id, text='Пришли координаты места')
    db.update_state(message, LOCATION)


@bot.message_handler(content_types=['location'], func=lambda message: db.get_state(message) == LOCATION)
def handle_location(message):
    db.add_location(message.chat.id, message.location)
    bot.send_message(message.chat.id, text='Пришли фото (если не хочешь, так и скажи)')
    db.update_state(message, PHOTO)


@bot.message_handler(content_types=['photo', 'text'],
                     func=lambda message: db.get_state(message) == PHOTO)
def handle_message(message):
    if message.content_type == 'text':
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
def handle_message(message):
    places = db.get_recent_places(message.chat.id)

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
    places = db.get_nearest_places(message.chat.id, message.location)

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
    currency, value = currency_interpreter(text.lower())
    currency_answer(currency, value, message)


@bot.message_handler(commands=['rate'])
def handle_message(message):
    currency, value = currency_interpreter(message.text.lower())
    keyboard = create_keyboard()
    currency_answer(currency, value, message, keyboard)


def currency_answer(currency, value, message, keyboard=None):
    if currency:
        bot.send_message(message.chat.id, text='Курс {} равен {}₽'.format(currency, value),
                         reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Узнай курс валют', reply_markup=keyboard)


@bot.message_handler()
def handle_message(message):
    bot.send_message(chat_id=message.chat.id, text='здаров')


# import pdb; pdb.set_trace()
# telebot.apihelper.proxy = {'https': '185.115.42.27:3128'}
if __name__ == '__main__':
    bot.infinity_polling()
