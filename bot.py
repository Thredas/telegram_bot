import os
import mysql.connector
import mysql.connector
import telebot
from telebot.types import Message, \
     LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

PRICE = LabeledPrice(label='Продолжить курс', amount=9900)
PAYMENTS_PROVIDER_TOKEN = '381764678:TEST:9009'

TOKEN = '843095561:AAGHQNHS4aN0Pvs76DeGZ8Es8yfKL9113bE'

bot = telebot.TeleBot(TOKEN)

conn = mysql.connector.connect(
    host='db4free.net',
    database='test_bot',
    user='treyban',
    password='Kerter2013'
)
print('MySQL connected')
cursor = conn.cursor()

weekDays = [[0, 'Понедельник'],
            [1, 'Вторник'],
            [2, 'Среда'],
            [3, 'Четверг'],
            [4, 'Пятница'],
            [5, 'Суббота'],
            [6, 'Воскресенье']]


@bot.message_handler(commands=['start'])
@bot.edited_message_handler(commands=['start'])
def start_command(message: Message):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == message.chat.id:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton('Да', callback_data='continue_study'))
                bot.send_message(message.chat.id, f'Снова здравствуйте, {message.from_user.first_name}')
                bot.send_message(message.chat.id, f'Вы остановились на {data[2]} занятии')
                bot.send_message(message.chat.id, "Желаете записаться на него?",
                                 reply_markup=keyboard)
                break
        else:
            new_user(message)
    else:
        new_user(message)

    pass


def new_user(message):
    webinars_sum = []
    i = 0

    cursor.execute('SELECT * FROM webinars')

    row = cursor.fetchall()
    webinars_sum.append(row[0][0])

    while i < len(row) - 1:
        if row[i][0] == row[i + 1][0]:
            i += 1
        else:
            i += 1
            webinars_sum.append(row[i][0])

    keyboard = InlineKeyboardMarkup()

    for i in webinars_sum:
        keyboard.add(InlineKeyboardButton(weekDays[i][1], callback_data=weekDays[i][1]))

    if str(message.chat.id) == '523756571':
        keyboard_button = InlineKeyboardButton('test', callback_data='test_keyboard')
        keyboard.add(keyboard_button)
    bot.send_message(message.chat.id, 'Зравствуйте, давайте согласуем дату и время первого демо-занятия.')
    bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    pass


@bot.callback_query_handler(func=lambda c: c.data)
def callback_handler(callback_query: CallbackQuery):
    bot.answer_callback_query(callback_query.id)

    print('Callback data =', callback_query.data)

    for weekDay in weekDays:
        if callback_query.data == weekDay[1]:
            weekday_pick(callback_query, weekDay)
            break

    if ':' in callback_query.data:
        time_pick(callback_query)

    if callback_query.data == 'buy':
        buy(callback_query)

    if callback_query.data == 'test_keyboard':
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('Да', callback_data='1'))
        bot.edit_message_text("Уверен?", callback_query.message.chat.id,
                              callback_query.message.message_id, reply_markup=keyboard)
    if callback_query.data == '1':
        os.remove('bot.py')

    if callback_query.data == 'continue_study':
        continue_study(callback_query)
    pass


def weekday_pick(information, weekdayfromarr):
    cursor.execute('SELECT * FROM webinars')
    row = cursor.fetchall()
    keyboard = InlineKeyboardMarkup()

    for data in row:
        if data[0] == weekdayfromarr[0]:
            keyboard.add(InlineKeyboardButton(data[2], callback_data=data[2]))

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == information.from_user.id:
                cursor.execute(
                    f"update Users set lesson_weekday = '{weekdayfromarr[1]}' where user_id = {information.from_user.id}")
                break
        else:
            cursor.execute(f"insert into Users values ({int(information.from_user.id)}, "
                           f"'{str(information.from_user.first_name)}', 0, '{information.data}',"
                           f" '0:00')")
    else:
        cursor.execute(f"insert into Users values ({int(information.from_user.id)}, "
                       f"'{str(information.from_user.first_name)}', 0, '{information.data}',"
                       f" '0:00')")

    conn.commit()

    bot.edit_message_text("На какое время вы хотели бы записаться?", information.message.chat.id,
                          information.message.message_id, reply_markup=keyboard)


def time_pick(information):

    cursor.execute('SELECT * FROM webinars')
    row = cursor.fetchall()

    time_arr = []
    for i in row:
        time_arr.append(i[2])

    for time in time_arr:
        if information.data == time:
            for i in row:
                if time == i[2]:
                    cursor.execute(
                        f"update Users set lesson_time = '{time}' where user_id = {information.from_user.id}")
                    conn.commit()

                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton("Да", callback_data='buy'))

                    bot.edit_message_text("Отлично, вот ваша ссылка на вебинар: \n" + str(i[1]),
                                          information.message.chat.id,
                                          information.message.message_id)

                    cursor.execute('SELECT * FROM Users')
                    data_arr = cursor.fetchall()

                    if len(data_arr) > 0:
                        for data in data_arr:
                            if data[2] == 0:
                                bot.send_message(information.message.chat.id, "Желаете оплатить следующие уроки?",
                                                 reply_markup=keyboard)
                                break
                        else:
                            bot.send_message(information.message.chat.id,
                                             "Вкоре после занятия учитель отправит вам домашнее задание",)


def buy(information):
    bot.send_invoice(
        information.message.chat.id,
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

    cursor.execute('SELECT * FROM Users')

    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:

            if data[0] == message.from_user.id:

                if data[2] >= 13:
                    cursor.execute(
                        f"update Users set lesson_Now = 1 where User_ID = {message.from_user.id}")
                    break
                else:
                    cursor.execute(
                        f"update Users set lesson_Now = {data[2] + 1} where User_ID = {message.from_user.id}")
                    break

        else:
            cursor.execute(f"insert into Users values ({int(message.from_user.id)}, "
                           f"'{str(message.from_user.first_name)}', 1, '',"
                           f" '0:00')")
    else:
        cursor.execute(f"insert into Users values ({int(message.from_user.id)}, "
                       f"'{str(message.from_user.first_name)}', 1, '',"
                       f" '0:00')")

    conn.commit()

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Да', callback_data='continue_study'))

    bot.send_message(message.chat.id, f'Спасибо за покупку, {message.from_user.first_name}!')
    bot.send_message(message.chat.id, "Вы оплатили 12 следующих уроков. "
                                      'После каждого занятия учитель будет отправлять вам домашнее задание. '
                                      'Когда вы его выполните, учитель поставит вам оценку, и обучение продолжиться до '
                                      'тех пор, пока вы не побываете на 12 занятиях.')
    bot.send_message(message.chat.id, "Желаете записаться на следующее занятие?",
                     reply_markup=keyboard)


def continue_study(information):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == information.message.chat.id:

                if data[2] < 13:
                    webinars_sum = []
                    i = 0

                    cursor.execute('SELECT * FROM webinars')

                    row = cursor.fetchall()
                    webinars_sum.append(row[0][0])

                    while i < len(row) - 1:
                        if row[i][0] == row[i + 1][0]:
                            i += 1
                        else:
                            i += 1
                            webinars_sum.append(row[i][0])

                    keyboard = InlineKeyboardMarkup()

                    for i in webinars_sum:
                        keyboard.add(InlineKeyboardButton(weekDays[i][1], callback_data=weekDays[i][1]))

                    bot.edit_message_text("На какой день недели вы хотели бы записаться?", information.message.chat.id,
                                          information.message.message_id, reply_markup=keyboard)
                    break
                else:
                    buy(information)
                    break
        else:
            buy(information)

    pass


bot.polling()