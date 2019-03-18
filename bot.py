import telebot
import sqlite3
import datetime
from telebot.types import Message, ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery

TOKEN = '843095561:AAGHQNHS4aN0Pvs76DeGZ8Es8yfKL9113bE'

bot = telebot.TeleBot(TOKEN)

weekDays = [[0, 'Понедельник'],
            [1, 'Вторник'],
            [2, 'Среда'],
            [3, 'Четверг'],
            [4, 'Пятница'],
            [5, 'Суббота'],
            [6, 'Воскресенье']]


@bot.message_handler(commands=['start'])
@bot.edited_message_handler(commands=['start'])
def command_start(message: Message):
    webinars_sum = 1
    # webinars_sum = []
    i = 0

    conn = sqlite3.connect('webinars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM webinars')

    row = cursor.fetchall()
    # webinars_sum.append(row[0][0])

    while i < len(row) - 1:
        if row[i][0] == row[i + 1][0]:
            i += 1
        else:
            i += 1
            webinars_sum = webinars_sum + 1
            # webinars_sum.append(row[i][0])

    button1 = KeyboardButton(weekDays[0][1])
    button2 = KeyboardButton(weekDays[1][1])
    button3 = KeyboardButton(weekDays[2][1])
    button4 = KeyboardButton(weekDays[3][1])
    button5 = KeyboardButton(weekDays[4][1])
    button6 = KeyboardButton(weekDays[5][1])
    button7 = KeyboardButton(weekDays[6][1])

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    if webinars_sum == 1:
        keyboard.add(button1)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    elif webinars_sum == 2:
        keyboard.row(button1, button2)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    elif webinars_sum == 3:
        keyboard.row(button1, button2)
        keyboard.add(button3)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    elif webinars_sum == 4:
        keyboard.row(button1, button2)
        keyboard.row(button3, button4)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    elif webinars_sum == 5:
        keyboard.row(button1, button2)
        keyboard.row(button3, button4)
        keyboard.add(button5)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    elif webinars_sum == 6:
        keyboard.row(button1, button2)
        keyboard.row(button3, button4)
        keyboard.row(button5, button6)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    elif webinars_sum == 7:
        keyboard.row(button1, button2)
        keyboard.row(button3, button4)
        keyboard.row(button5, button6)
        keyboard.add(button7)
        bot.send_message(message.chat.id, 'Привет, давай согласуем дату и время первого демо-занятия.')
        bot.send_message(message.chat.id, 'На какой день недели вы хотели бы записаться?', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Нет доступных занятий.')

    conn.close()
    pass


@bot.message_handler(content_types=['text'])  # хэндлер всех сообщений
@bot.edited_message_handler(content_types=['text'])  # хэндлер изменнных сообщений
def send_reply(message: Message):  # функция принимает объект Message

    conn = sqlite3.connect('webinars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM webinars')

    row = cursor.fetchall()



    button_time_1 = KeyboardButton('12:00')

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(button_time_1)

    delete_keyboard = ReplyKeyboardRemove()

    for i in weekDays:
        if message.text == i[1]:
            bot.send_message(message.chat.id, 'Какое время вас устроит?', reply_markup=keyboard)
    if message.text == '12:00':
        bot.send_message(message.chat.id, 'Отлично, вот ваша ссылка на вебинар', reply_markup=delete_keyboard)
        bot.send_message(message.chat.id, 'http://webinar.com/1')
        bot.send_message(message.chat.id, 'Желаете оплатить следующие уроки?')

    conn.close()
    pass


bot.polling()