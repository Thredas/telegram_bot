import os
import mysql.connector
import telebot
from flask import Flask, request
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

weekDays = [[0, 'понедельник'],
            [1, 'вторник'],
            [2, 'среда'],
            [3, 'четверг'],
            [4, 'пятница'],
            [5, 'суббота'],
            [6, 'воскресенье']]

days = []
timez = []
z = 0

pupil_id = 0
chat_counter = 0
chat_isOver = 1

server = Flask(__name__)


# Общие функции


@bot.message_handler(commands=['start'])
@bot.edited_message_handler(commands=['start'])
def start_command(message: Message):

    cursor.execute('SELECT * FROM teachers')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == message.chat.id:
                keyboard = InlineKeyboardMarkup()
                keyboard.row(InlineKeyboardButton('Создать график занятий', callback_data='timetable'))
                keyboard.add(InlineKeyboardButton('Посмотреть записанных учеников', callback_data='pupils'))
                bot.send_message(message.chat.id, f"Здравствуйте, {data[1]}.\n\nКакую операцию вы хотите выполнить?",
                                 reply_markup=keyboard)

                break
        else:
            cursor.execute('SELECT * FROM Users')
            data_arr = cursor.fetchall()

            if len(data_arr) > 0:
                for data in data_arr:
                    if data[0] == message.chat.id:

                        day = 0

                        for weekDay in weekDays:
                            if data[3] == weekDay[1]:
                                day = weekDay[0]

                        cursor.execute(
                            f"update paid_webinars set isTaken = 0 "
                            f"where teacher_id = {data[5]} and time = '{data[4]}' and weekDay = {day}")
                        conn.commit()

                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton('Да', callback_data='continue_study'))
                        bot.send_message(message.chat.id,
                                         f"Снова здравствуйте, {message.from_user.first_name}.\n\n"
                                         f"Вы остановились на {data[2]} занятии. \nЖелаете записаться на него?",
                                         reply_markup=keyboard)
                        break
                else:
                    new_user(message)
            else:
                new_user(message)


@bot.callback_query_handler(func=lambda c: c.data)
def callback_handler(callback_query: CallbackQuery):
    bot.answer_callback_query(callback_query.id)

    for weekDay in weekDays:
        if weekDay[1] in callback_query.data:
            weekday_pick(callback_query, weekDay)
            break

    if ':' in callback_query.data:
        time_pick(callback_query)

    if callback_query.data == 'timetable':
        bot.send_message(callback_query.message.chat.id,
                         'Введите через запятую, в какие дни вы хотели бы работать.'
                         '\n\n'
                         'Например: Понедельник, вторник, пятница')
        bot.register_next_step_handler(callback_query.message, timetable)

    if callback_query.data == 'pupils':
        pupils(callback_query)

    if 'chat' in callback_query.data:
        teacher_chat(callback_query)

    if callback_query.data == 'buy':
        buy(callback_query)

    if callback_query.data == 'test_keyboard':
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('Да', callback_data='1'))
        bot.edit_message_text("Уверен?", callback_query.message.chat.id,
                              callback_query.message.message_id, reply_markup=keyboard)
    if callback_query.data == '1':
        os.remove('bot.py')

    if callback_query.data == 'create_timetable':
        create_timetable(callback_query)

    if callback_query.data == 'continue_study':
        continue_study(callback_query)

    if callback_query.data == 'teacher_pick_new' or callback_query.data == 'teacher_pick_old':
        teacher_pick(callback_query)

    cursor.execute('SELECT * FROM teachers')
    row = cursor.fetchall()
    for teacher in row:
        if callback_query.data == str(teacher[0]):
            teacher_pick2(callback_query)
            break


def teacher_chat(information):
    cursor.execute('SELECT * FROM teachers')
    teachers = cursor.fetchall()

    global pupil_id
    pupil_id = information.data.split('/')[1]

    for teacher in teachers:
        if teacher[0] == information.from_user.id:

            global chat_isOver
            chat_isOver = 0

            bot.edit_message_reply_markup(information.message.chat.id, information.message.message_id, reply_markup=None)
            bot.send_message(teacher[0], 'Вы начали чат с ученикои. '
                                         'Все ваши следующие сообщения боту будут адресованы ученику.'
                                         ' Чат не прекратится, '
                                         'пока вы не напишите слово "Конец" (без кавычек).')
            bot.register_next_step_handler(information.message, teacher_chat2)
            break


def teacher_chat2(message):
    cursor.execute('SELECT * FROM teachers')
    teachers = cursor.fetchall()

    global chat_isOver

    for teacher in teachers:
        if teacher[0] == message.from_user.id:
            if chat_isOver == 0:
                if message.text.lower() == 'конец':
                    chat_isOver = 1
                    bot.send_message(message.from_user.id, 'Чат окончен')

                elif '/' in message.text.lower():
                    bot.send_message(message.from_user.id, 'Запрещенный в чате знак "/"')
                    bot.register_next_step_handler(message, chat2)

                else:
                    bot.send_message(pupil_id, message.text)
                    bot.register_next_step_handler(message, teacher_chat2)
                break

            else:
                bot.send_message(message.from_user.id, 'Чат окончен')


@bot.message_handler(commands=['chat'])
@bot.edited_message_handler(commands=['chat'])
def chat(message: Message):
    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == message.from_user.id:
                global chat_isOver
                chat_isOver = 0

                bot.send_message(message.from_user.id, 'Вы начали чат с учителем. '
                                                       'Все ваши следующие сообщения боту будут адресованы учителю.'
                                                       ' Чат не прекратится, '
                                                       'пока вы не напишите слово "Конец" (без кавычек).')
                bot.register_next_step_handler(message, chat2)
                break
        else:
            bot.send_message(message.from_user.id, 'Сначала запишитесь на занятия')
    else:
        bot.send_message(message.from_user.id, 'Сначала запишитесь на занятия')


def chat2(message: Message):
    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    global chat_isOver

    for data in data_arr:
        if data[0] == message.from_user.id:
            if chat_isOver == 0:
                if message.text.lower() == 'конец':
                    global chat_counter
                    chat_counter = 0

                    chat_isOver = 1
                    bot.send_message(message.from_user.id, 'Чат окончен')

                elif '/' in message.text.lower():
                    bot.send_message(message.from_user.id, 'Запрещенный в чате знак "/"')
                    bot.register_next_step_handler(message, chat2)
                else:
                    if chat_counter == 0:

                        chat_counter += 1

                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton('Начать', callback_data='chat/' + str(data[0])))

                        bot.send_message(data[5],
                                         f'Сообщение от ученика по имени {data[1]}:\n\n"{message.text}"\n\nНачать чат?',
                                         reply_markup=keyboard)
                    else:
                        bot.send_message(data[5], message.text)

                    bot.register_next_step_handler(message, chat2)
                break
            else:
                bot.send_message(message.from_user.id, 'Чат окончен')


# Функции ученика


def new_user(message):
    webinars_sum = []
    k = 0

    cursor.execute('SELECT * FROM paid_webinars')

    row = cursor.fetchall()

    for i in row:
        if len(webinars_sum) != 0:
            if i[0] == webinars_sum[k]:
                continue
            if i[5] == 1:
                continue
            webinars_sum.append(i[0])
            k += 1
        else:
            webinars_sum.append(i[0])

    keyboard = InlineKeyboardMarkup()

    for i in webinars_sum:
        keyboard.add(InlineKeyboardButton(weekDays[i][1].capitalize(), callback_data=f'{weekDays[i][1]}/{row[i][3]}'))

    if str(message.chat.id) == '523756571':
        keyboard_button = InlineKeyboardButton('test', callback_data='test_keyboard')
        keyboard.add(keyboard_button)
    bot.send_message(message.chat.id, 'Зравствуйте, давайте согласуем дату и время первого демо-занятия.\n\n'
                                      'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    pass


def weekday_pick(information, weekdayfromarr):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    callback = information.data.split('/')

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == information.from_user.id:
                if data[2] == 0:
                    print(weekdayfromarr[1])
                    print(callback)
                    cursor.execute(
                        f"update Users set lesson_weekday = '{weekdayfromarr[1]}', "
                        f"teacher_id = {callback[1]} "
                        f"where user_id = {information.from_user.id}")
                else:
                    cursor.execute(
                        f"update Users set lesson_weekday = '{weekdayfromarr[1]}' "
                        f"where user_id = {information.from_user.id}")
                conn.commit()
                break
        else:
            cursor.execute(f"insert into Users values ({int(information.from_user.id)}, "
                           f"'{str(information.from_user.first_name)}', 0, '{callback[0]}',"
                           f" '0:00', '{callback[1]}')")
            conn.commit()
    else:
        cursor.execute(f"insert into Users values ({int(information.from_user.id)}, "
                       f"'{str(information.from_user.first_name)}', 0, '{callback[0]}',"
                       f" '0:00', '{callback[1]}')")
        conn.commit()

    cursor.execute('SELECT * FROM paid_webinars')
    row = cursor.fetchall()

    keyboard = InlineKeyboardMarkup()

    for data in row:
        if data[0] == weekdayfromarr[0]:
            if data[5] == 0:
                keyboard.add(InlineKeyboardButton(data[1], callback_data=str(data[0]) + '/' + data[1]))

    conn.commit()

    bot.edit_message_text("На какое время вы хотели бы записаться?", information.message.chat.id,
                          information.message.message_id, reply_markup=keyboard)


def time_pick(information):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    cursor.execute('SELECT * FROM paid_webinars')
    row = cursor.fetchall()

    information.data = information.data.split('/')
    print(information.data)

    for i in row:
        for data in data_arr:
            if data[2] == 0:
                if information.data[0] == str(i[0]) and information.data[1] == i[1]:
                    cursor.execute(
                        f"update Users set lesson_time = '{information.data[1]}' "
                        f"where user_id = {information.from_user.id}")

                    cursor.execute(
                        f"update paid_webinars set isTaken = 1 "
                        f"where teacher_id = {i[3]} and time = '{information.data[1]}' "
                        f"and weekDay = {information.data[0]}")
                    conn.commit()

                    bot.edit_message_text(f"Отлично, ваш урок будет проводить {i[4]}.\n"
                                          f"Вот контакт вашего учителя: {i[2]}\n"
                                          f"Cвяжитесь с ним в Skype в выбранное время.",
                                          information.message.chat.id,
                                          information.message.message_id)
                    print('message modified')

                    for weekDay in weekDays:
                        if information.data[0] == str(weekDay[0]):
                            information.data[0] = weekDay[1]

                    bot.send_message(i[3], f'На занятия записался {information.from_user.first_name}\n'
                                           f'День недели: {information.data[0]}, время: {information.data[1]}')

                    cursor.execute('SELECT * FROM Users')
                    data_arr = cursor.fetchall()

                    if len(data_arr) > 0:
                        for data in data_arr:
                            if data[0] == information.from_user.id:
                                if data[2] == 0:
                                    keyboard = InlineKeyboardMarkup()
                                    keyboard.add(InlineKeyboardButton("Да", callback_data='buy'))
                                    bot.send_message(information.message.chat.id,
                                                     "Желаете оплатить следующие уроки?",
                                                     reply_markup=keyboard)
                                    break
                        else:
                            for data in data_arr:
                                if data[0] == information.from_user.id:
                                    cursor.execute('SELECT * FROM home_work')
                                    data_arr2 = cursor.fetchall()

                                    for data2 in data_arr2:
                                        if data2[0] == information.from_user.id:
                                            cursor.execute(
                                                f"update home_work set lesson = '{data[2]}' "
                                                f"where user_id = {information.from_user.id}")
                                            break
                                    else:
                                        cursor.execute(
                                            f"insert into home_work values ({int(information.from_user.id)}, "
                                            f"'{str(information.from_user.first_name)}',"
                                            f" {data[2]}, "
                                            f"'Ожидается ссылка',"
                                            f" 'Ожидается оценка')")
                                    break

                            bot.send_message(information.message.chat.id,
                                             "Чтобы получить домашнее задание, введите /home_work", )
                            conn.commit()
                            break
            else:
                if i[3] == data[5]:
                    if information.data[0] == str(i[0]) and information.data[1] == i[1]:
                        cursor.execute(
                            f"update Users set lesson_time = '{information.data[1]}' "
                            f"where user_id = {information.from_user.id}")

                        cursor.execute(
                            f"update paid_webinars set isTaken = 1 "
                            f"where teacher_id = {i[3]} and time = '{information.data[1]}' "
                            f"and weekDay = {information.data[0]}")
                        conn.commit()

                        bot.edit_message_text(f"Отлично, ваш урок будет проводить {i[4]}.\n"
                                              f"Вот контакт вашего учителя: {i[2]}\n"
                                              f"Cвяжитесь с ним в Skype в выбранное время.",
                                              information.message.chat.id,
                                              information.message.message_id)
                        print('message modified')

                        for weekDay in weekDays:
                            if information.data[0] == str(weekDay[0]):
                                information.data[0] = weekDay[1]

                        bot.send_message(i[3], f'На занятия записался {information.from_user.first_name}\n'
                        f'День недели: {information.data[0]}, время: {information.data[1]}')

                        cursor.execute('SELECT * FROM Users')
                        data_arr = cursor.fetchall()

                        if len(data_arr) > 0:
                            for data in data_arr:
                                if data[0] == information.from_user.id:
                                    if data[2] == 0:
                                        keyboard = InlineKeyboardMarkup()
                                        keyboard.add(InlineKeyboardButton("Да", callback_data='buy'))
                                        bot.send_message(information.message.chat.id,
                                                         "Желаете оплатить следующие уроки?",
                                                         reply_markup=keyboard)
                                        break
                            else:
                                for data in data_arr:
                                    if data[0] == information.from_user.id:
                                        cursor.execute('SELECT * FROM home_work')
                                        data_arr2 = cursor.fetchall()

                                        for data2 in data_arr2:
                                            if data2[0] == information.from_user.id:
                                                cursor.execute(
                                                    f"update home_work set lesson = '{data[2]}' "
                                                    f"where user_id = {information.from_user.id}")
                                                break
                                        else:
                                            cursor.execute(
                                                f"insert into home_work values ({int(information.from_user.id)}, "
                                                f"'{str(information.from_user.first_name)}',"
                                                f" {data[2]}, "
                                                f"'Ожидается ссылка',"
                                                f" 'Ожидается оценка')")
                                        break

                                bot.send_message(information.message.chat.id,
                                                 "Чтобы получить домашнее задание, введите /home_work", )
                                conn.commit()
                                break


def buy(information):
    cursor.execute('SELECT * FROM Users')

    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == information.from_user.id:

                if data[2] >= 13 or data[2] == 0:
                    bot.delete_message(information.message.chat.id, information.message.message_id)
                    bot.send_invoice(
                        information.message.chat.id,
                        title='Продолжение курса',
                        description='Чтобы продолжить обучение, заплатите за следующие 12 вебинаров.',
                        provider_token=PAYMENTS_PROVIDER_TOKEN,
                        currency='RUB',
                        photo_url='https://www.instituteiba.by/upload/medialibrary/5f5/'
                                  '5f5aa75c5497429160440528683d411c.jpg',
                        photo_height=560,
                        photo_width=1024,
                        photo_size=512,
                        is_flexible=False,  # True, если конечная цена зависит от способа доставки
                        prices=[PRICE],
                        start_parameter='paying_webinars',
                        invoice_payload='webinars_payed'
                    )
                    break

                else:
                    bot.send_message(information.message.chat.id,
                                     'Вы уже оплатили занятия, и сможете снова за них заплатить, '
                                     'когда пройдёте их все до конца.')
                    break


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

        conn.commit()

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('Выбрать нового', callback_data='teacher_pick_new'))
        keyboard.add(InlineKeyboardButton('Оставить текущего', callback_data='teacher_pick_old'))

        bot.send_message(message.chat.id, f'Спасибо за покупку, {message.from_user.first_name}!')
        bot.send_message(message.chat.id, "Вы оплатили 12 следующих уроков. "
                                          'После каждого занятия учитель будет отправлять вам домашнее задание. '
                                          'Когда вы его выполните, учитель поставит вам оценку, '
                                          'и обучение продолжиться до '
                                          'тех пор, пока вы не побываете на 12 занятиях.')
        bot.send_message(message.chat.id, "Вы хотите продолжить обучение с текущим учителем или выбрать нового?",
                         reply_markup=keyboard)


def teacher_pick(information):

    cursor.execute('SELECT * FROM teachers')
    row = cursor.fetchall()

    if information.data == 'teacher_pick_new':
        keyboard = InlineKeyboardMarkup()

        for data in row:
            keyboard.add(InlineKeyboardButton(data[1], callback_data=data[0]))
        bot.edit_message_text('С каким учителем вы желаете продолжить обучение?', information.message.chat.id,
                              information.message.message_id, reply_markup=keyboard)
    else:
        bot.edit_message_text('Хорошо, за вами будет закреплен ваш текущий учитель.', information.message.chat.id,
                              information.message.message_id)
        keyboard2 = InlineKeyboardMarkup()
        keyboard2.add(InlineKeyboardButton('Да', callback_data='continue_study'))
        bot.send_message(information.message.chat.id, f"Желаете записаться на следующее занятие?",
                         reply_markup=keyboard2)


def teacher_pick2(information):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    for data in data_arr:
        if data[0] == information.from_user.id:
            cursor.execute(
                f"update Users set teacher_id = {information.data} "
                f"where user_id = {information.from_user.id}")

            day = 0

            for weekDay in weekDays:
                if data[3] == weekDay[1]:
                    day = weekDay[0]

            cursor.execute(
                f"update paid_webinars set isTaken = 0 "
                f"where teacher_id = {data[5]} and time = '{data[4]}' and weekDay = {day}")
            conn.commit()
            break
    conn.commit()

    name = ''
    cursor.execute('SELECT * FROM teachers')
    row = cursor.fetchall()
    for teacher in row:
        if information.data == str(teacher[0]):
            name = teacher[1]
            break

    bot.edit_message_text(f'Отлично, вы продолжите обучение с учителем по имени {name}.', information.message.chat.id,
                          information.message.message_id)

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Да', callback_data='continue_study'))
    bot.send_message(information.message.chat.id, f"Желаете записаться на следующее занятие?",
                     reply_markup=keyboard)


def continue_study(information):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == information.message.chat.id:
                if data[2] == 0:
                    webinars_sum = []
                    k = 0

                    cursor.execute('SELECT * FROM paid_webinars')
                    row = cursor.fetchall()

                    for i in row:
                        if len(webinars_sum) != 0:
                            if i[0] == webinars_sum[k]:
                                continue
                            if i[5] == 1:
                                continue
                            webinars_sum.append(i[0])
                            k += 1
                        else:
                            webinars_sum.append(i[0])

                    keyboard = InlineKeyboardMarkup()

                    for i in webinars_sum:
                        keyboard.add(
                            InlineKeyboardButton(weekDays[i][1].capitalize(),
                                                 callback_data=f'{weekDays[i][1]}/{row[i][3]}'))

                    if str(information.message.chat.id) == '523756571':
                        keyboard_button = InlineKeyboardButton('test', callback_data='test_keyboard')
                        keyboard.add(keyboard_button)
                    bot.edit_message_text('На какой день недели вы хотели бы записаться?', information.message.chat.id,
                                          information.message.message_id, reply_markup=keyboard)
                    break

                elif data[2] < 13:
                    webinars_sum = []
                    k = 0

                    cursor.execute('SELECT * FROM paid_webinars')

                    row = cursor.fetchall()

                    for i in row:
                        if len(webinars_sum) != 0:
                            if i[0] == webinars_sum[k]:
                                continue
                            if i[5] == 1:
                                continue
                            if i[3] != data[5]:
                                continue
                            webinars_sum.append(i[0])
                            k += 1
                        else:
                            webinars_sum.append(i[0])

                    keyboard = InlineKeyboardMarkup()

                    for i in webinars_sum:
                        keyboard.add(InlineKeyboardButton(weekDays[i][1],
                                                          callback_data=f'{weekDays[i][1]}/{row[i][3]}'))

                    bot.edit_message_text("На какой день недели вы хотели бы записаться?", information.message.chat.id,
                                          information.message.message_id, reply_markup=keyboard)
                    break

        else:
            buy(information)


@bot.message_handler(commands=['home_work'])
@bot.edited_message_handler(commands=['home_work'])
def home_work(message: Message):
    cursor.execute('SELECT * FROM home_work')
    row = cursor.fetchall()

    for data in row:

        if data[0] == message.chat.id:
            if data[3] == "Ожидается ссылка":
                bot.send_message(message.chat.id,
                                 "Учитель еще не отправил вам домашнее задание, повторите команду позднее")
                break
            else:
                cursor.execute(
                    f"update Users set lesson_Now = {data[2] + 1} where User_ID = {message.chat.id}")
                cursor.execute(
                    f"update home_work set hw_link = 'Ожидается ссылка' where user_id = {message.chat.id}")
                bot.send_message(message.chat.id, f"Вот ваше д/з: \n{data[3]} \n\nЧтобы узнать оценку введите /grade")
                conn.commit()
                break


@bot.message_handler(commands=['grade'])
@bot.edited_message_handler(commands=['grade'])
def grade(message: Message):
    cursor.execute('SELECT * FROM home_work')
    row = cursor.fetchall()

    for data in row:

        if data[0] == message.chat.id:
            if data[4] == "Ожидается оценка":
                bot.send_message(message.chat.id,
                                 "Учитель еще не поставил вам оценку за домашнее задание, повторите команду позднее")
                break
            else:
                bot.send_message(message.chat.id, f"Ваша оценка за последнее выполненное д/з: {data[4]}")

                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton('Да', callback_data='continue_study'))
                bot.send_message(message.chat.id, f"Желаете записаться на следующее занятие?", reply_markup=keyboard)
                break


# Функции учителя


def timetable(message: Message):

    for weekDay in weekDays:
        if weekDay[1] in message.text:
            days.append(message.text.lower().split(', '))

    if z != len(days[0]):
        bot.send_message(message.chat.id,
                         f'Введите через запятую, в какое время в {days[0][z]} вы хотели бы работать.')
        bot.register_next_step_handler(message, time_in_timetable)
    else:
        k = 0
        text = ''

        for day in days[0]:
            time_text = ''
            for times in timez[k]:
                time_text += times + ', '

            text += f'В {day} в: {time_text}\n'
            k += 1

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('Да', callback_data='create_timetable'))

        bot.send_message(message.chat.id,
                         f'Значит, вы хотите работать: \n{text}', reply_markup=keyboard)


def time_in_timetable(message: Message):
    global z
    z += 1
    timez.append(message.text.split(', '))

    timetable(message)


def create_timetable(information):
    k = 0
    for day in days[0]:
        for weekDay in weekDays:
            if day == weekDay[1]:
                day = weekDay[0]

        for time in timez[k]:
            cursor.execute('SELECT * FROM teachers')
            data_arr = cursor.fetchall()

            for data in data_arr:
                if data[0] == information.from_user.id:
                    cursor.execute(f"insert into paid_webinars values ({day}, "
                                   f"'{time}', '{data[2]}', {data[0]},"
                                   f" '{data[1]}', '0')")
                    conn.commit()
        k += 1
    bot.edit_message_text("График занятий создан", information.message.chat.id,
                          information.message.message_id)


def pupils(information):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    text = 'К вам записаны: \n\n'

    for data in data_arr:
        if data[5] == information.from_user.id:
            text += f'{data[1]} в {data[3]} на {data[4]}'

    bot.send_message(information.message.chat.id, text)
    pass


bot.polling()
