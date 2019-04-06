import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

import mysql.connector

vk_session = vk_api.VkApi(token='c73b6c632962490a736292b8a5f28aac7de6d313308451b5867e3094e83a1d2d03699d0d30604d9840a0c')
longpoll = VkBotLongPoll(vk_session, '180703340')
vk = vk_session.get_api()

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

previous_message_id = 0
callback = ''


def start_command(evento):

    cursor.execute('SELECT * FROM teachers')
    data_arr = cursor.fetchall()

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == evento.obj.from_id:

                vk.messages.send(peer_id=evento.obj.from_id,
                                 message=f"Здравствуйте, {data[1]}.\n\nКакую операцию вы хотите выполнить?",
                                 random_id=get_random_id())

                break
        else:
            cursor.execute('SELECT * FROM Users')
            data_arr = cursor.fetchall()

            if len(data_arr) > 0:
                for data in data_arr:
                    if data[0] == evento.obj.from_id:

                        day = 0

                        for weekDay in weekDays:
                            if data[3] == weekDay[1]:
                                day = weekDay[0]

                        cursor.execute(
                            f"update paid_webinars set isTaken = 0 "
                            f"where teacher_id = {data[5]} and time = '{data[4]}' and weekDay = {day}")
                        conn.commit()

                        vk.messages.send(peer_id=evento.obj.from_id,
                                         message=f"Снова здравствуйте, "
                                         f"{vk.users.get(user_ids=evento.obj.from_id)[0]['first_name']}.\n\n"
                                         f"Вы остановились на {data[2]} занятии. \nЖелаете записаться на него?",
                                         random_id=get_random_id())
                        break
                else:
                    new_user(event)
            else:
                new_user(event)


def new_user(evento):
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

    text = ''

    for data in webinars_sum:
        for weekDay in weekDays:
            if data == weekDay[0]:
                text += weekDay[1] + '\n'

    vk.messages.send(peer_id=evento.obj.from_id,
                     message='Зравствуйте, давайте согласуем дату и время первого демо-занятия.\n\n'
                             f'Занятия будут проводится в следующие дни недели:\n\n'
                             f'{text}'
                             '\n\nВведите на какой день недели вы хотели бы записаться.',
                     random_id=get_random_id())

    global previous_message_id, callback

    previous_message_id = event.obj.conversation_message_id


def weekday_pick(evento, weekdayfromarr):

    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    callback_data = callback.split('/')

    if len(data_arr) > 0:
        for data in data_arr:
            if data[0] == evento.obj.from_id:
                if data[2] == 0:
                    cursor.execute(
                        f"update Users set lesson_weekday = '{weekdayfromarr[1]}', "
                        f"teacher_id = {callback_data[1]} "
                        f"where user_id = {evento.from_user.id}")
                else:
                    cursor.execute(
                        f"update Users set lesson_weekday = '{weekdayfromarr[1]}' "
                        f"where user_id = {evento.obj.from_id}")
                conn.commit()
                break
        else:
            cursor.execute(f"insert into Users values ({int(evento.obj.from_id)}, "
                           f"'{str(vk.users.get(user_ids=evento.obj.from_id)[0]['first_name'])}', "
                           f"0, '{callback_data[0]}',"
                           f" '0:00', '{callback_data[1]}')")
            conn.commit()
    else:
        cursor.execute(f"insert into Users values ({int(evento.obj.from_id)}, "
                       f"'{str(vk.users.get(user_ids=evento.obj.from_id)[0]['first_name'])}', 0, '{callback_data[0]}',"
                       f" '0:00', '{callback_data[1]}')")
        conn.commit()

    cursor.execute('SELECT * FROM paid_webinars')
    row = cursor.fetchall()

    text = ''

    for data in row:
        if data[0] == weekdayfromarr[0]:
            if data[5] == 0:
                text += data[1] + '\n'

    conn.commit()

    vk.messages.send(peer_id=evento.obj.from_id,
                     message=f'Занятия будут проводится в следующее время:\n\n'
                             f'{text}'
                             '\n\nВведите на какое время вы хотели бы записаться.',
                     random_id=get_random_id())

    global previous_message_id

    previous_message_id = event.obj.conversation_message_id


def time_pick(evento):
    cursor.execute('SELECT * FROM Users')
    data_arr = cursor.fetchall()

    cursor.execute('SELECT * FROM paid_webinars')
    row = cursor.fetchall()

    evento.obj.text = evento.obj.text.split('/')
    print(evento.obj.text)

    for i in row:
        for data in data_arr:
            if data[2] == 0:
                if evento.obj.text[0] == str(i[0]) and evento.obj.text[1] == i[1]:
                    cursor.execute(
                        f"update Users set lesson_time = '{evento.obj.text[1]}' "
                        f"where user_id = {evento.obj.from_id}")

                    cursor.execute(
                        f"update paid_webinars set isTaken = 1 "
                        f"where teacher_id = {i[3]} and time = '{evento.obj.text[1]}' "
                        f"and weekDay = {evento.obj.text[0]}")
                    conn.commit()

                    bot.edit_message_text(f"Отлично, ваш урок будет проводить {i[4]}.\n"
                                          f"Вот контакт вашего учителя: {i[2]}\n"
                                          f"Cвяжитесь с ним в Skype в выбранное время.",
                                          information.message.chat.id,
                                          information.message.message_id)
                    print('message modified')

                    for weekDay in weekDays:
                        if evento.obj.text[0] == str(weekDay[0]):
                            evento.obj.text[0] = weekDay[1]

                    bot.send_message(i[3], f'На занятия записался {information.from_user.first_name}\n'
                                           f'День недели: {information.data[0]}, время: {information.data[1]}')

                    cursor.execute('SELECT * FROM Users')
                    data_arr = cursor.fetchall()

                    if len(data_arr) > 0:
                        for data in data_arr:
                            if data[0] == evento.obj.from_id:
                                if data[2] == 0:

                                    bot.send_message(information.message.chat.id,
                                                     "Желаете оплатить следующие уроки?",
                                                     reply_markup=keyboard)
                                    break
                        else:
                            for data in data_arr:
                                if data[0] == evento.obj.from_id:
                                    cursor.execute('SELECT * FROM home_work')
                                    data_arr2 = cursor.fetchall()

                                    for data2 in data_arr2:
                                        if data2[0] == evento.obj.from_id:
                                            cursor.execute(
                                                f"update home_work set lesson = '{data[2]}' "
                                                f"where user_id = {evento.obj.from_id}")
                                            break
                                    else:
                                        cursor.execute(
                                            f"insert into home_work values ({int(evento.obj.from_id)}, "
                                            f"'{str(vk.users.get(user_ids=evento.obj.from_id)[0]['first_name'])}',"
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
                    if evento.obj.text[0] == str(i[0]) and evento.obj.text[1] == i[1]:
                        cursor.execute(
                            f"update Users set lesson_time = '{evento.obj.text[1]}' "
                            f"where user_id = {evento.obj.from_id}")

                        cursor.execute(
                            f"update paid_webinars set isTaken = 1 "
                            f"where teacher_id = {i[3]} and time = '{evento.obj.text[1]}' "
                            f"and weekDay = {evento.obj.text[0]}")
                        conn.commit()

                        bot.edit_message_text(f"Отлично, ваш урок будет проводить {i[4]}.\n"
                                              f"Вот контакт вашего учителя: {i[2]}\n"
                                              f"Cвяжитесь с ним в Skype в выбранное время.",
                                              information.message.chat.id,
                                              information.message.message_id)
                        print('message modified')

                        for weekDay in weekDays:
                            if evento.obj.text[0] == str(weekDay[0]):
                                evento.obj.text[0] = weekDay[1]

                        bot.send_message(i[3], f'На занятия записался {information.from_user.first_name}\n'
                        f'День недели: {evento.obj.text[0]}, время: {evento.obj.text[1]}')

                        cursor.execute('SELECT * FROM Users')
                        data_arr = cursor.fetchall()

                        if len(data_arr) > 0:
                            for data in data_arr:
                                if data[0] == evento.obj.from_id:
                                    if data[2] == 0:

                                        bot.send_message(information.message.chat.id,
                                                         "Желаете оплатить следующие уроки?",
                                                         reply_markup=keyboard)
                                        break
                            else:
                                for data in data_arr:
                                    if data[0] == evento.obj.from_id:
                                        cursor.execute('SELECT * FROM home_work')
                                        data_arr2 = cursor.fetchall()

                                        for data2 in data_arr2:
                                            if data2[0] == evento.obj.from_id:
                                                cursor.execute(
                                                    f"update home_work set lesson = '{data[2]}' "
                                                    f"where user_id = {evento.obj.from_id}")
                                                break
                                        else:
                                            cursor.execute(
                                                f"insert into home_work values ({int(evento.obj.from_id)}, "
                                                f"'{str(information.from_user.first_name)}',"
                                                f" {data[2]}, "
                                                f"'Ожидается ссылка',"
                                                f" 'Ожидается оценка')")
                                        break

                                bot.send_message(information.message.chat.id,
                                                 "Чтобы получить домашнее задание, введите /home_work", )
                                conn.commit()
                                break


for event in longpoll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:

            if event.obj.conversation_message_id == previous_message_id + 2:

                cursor.execute('SELECT * FROM paid_webinars')
                row = cursor.fetchall()

                for weekDay in weekDays:
                    if weekDay[1] in event.obj.text.lower():
                        for data in row:
                            if weekDay[0] == data[0]:
                                callback = f'{weekDay[1]}/{data[3]}'
                                weekday_pick(event, weekDay)
                                break

                if ':' in event.obj.text.lower():
                    time_pick(event)

                previous_message_id = 0

            if event.obj.text.lower() == 'начать':
                start_command(event)
