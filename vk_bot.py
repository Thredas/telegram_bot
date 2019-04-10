import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

import mysql.connector

from flask import Flask, request, json


vk_session = vk_api.VkApi(
        token='c73b6c632962490a736292b8a5f28aac7de6d313308451b5867e3094e83a1d2d03699d0d30604d9840a0c')
longpoll = VkBotLongPoll(vk_session, '180703340')
vk = vk_session.get_api()

conn = mysql.connector.connect(
    host='db4free.net',
    database='test_bot_vk',
    user='mrtreyban',
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


def start_command(evento):
        cursor.execute('SELECT * FROM teachers')
        data_arr = cursor.fetchall()

        if len(data_arr) > 0:
            for data in data_arr:
                if data[0] == evento.obj.from_id:
                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message=f"Здравствуйте, {data[1]}.\n\nКакую операцию вы хотите выполнить?\n\n"
                                     '{Создать график занятий, \nпосмотреть записанных учеников}',
                                     random_id=get_random_id())

                    global callback, previous_message_id
                    previous_message_id = event.obj.conversation_message_id
                    print(previous_message_id)
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
                                             f"Вы остановились на {data[2]} занятии. \nЖелаете записаться на него?"
                                             '\n{да, нет}',
                                             random_id=get_random_id())

                            callback = 'continue'
                            previous_message_id = event.obj.conversation_message_id
                            print(previous_message_id)
                            break
                    else:
                        vk.messages.send(peer_id=evento.obj.from_id,
                                         message='В фигурных скобках пишутся варианты ответа на сообщения бота. \n'
                                                 'Например: {да, нет}.\n'
                                                 'Если вы введете, что-то кроме них, введите "Начать"\n'
                                                 'Если бот перестал отвечать на сообщения, введите "Начать"\n',
                                         random_id=get_random_id())
                        new_user(event)
                else:
                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message='В фигурных скобках пишутся варианты ответа на сообщения бота. \n'
                                     'Например: {да, нет}.\n'
                                     'Если вы введете, что-то кроме них, введите "Начать"\n'
                                     'Если бот перестал отвечать на сообщения, введите "Начать"\n',
                                     random_id=get_random_id())
                    new_user(event)


# Функции учителя


def timetable(evento):
    global days

    for weekDay2 in weekDays:
        if weekDay2[1] in evento.obj.text.lower():
            if ',' in evento.obj.text:
                days = evento.obj.text.lower().split(', ')
                break
            else:
                days.append(evento.obj.text.lower())
                break

    print(days)

    if z != len(days):
        vk.messages.send(peer_id=evento.obj.from_id,
                         message=f'Введите через запятую, в какое время в {days[z]} вы хотели бы работать.',
                         random_id=get_random_id())

        global callback, previous_message_id
        previous_message_id = event.obj.conversation_message_id
        callback = 'time_in_timetable'
    else:
        k = 0
        text = ''

        for day in days:
            time_text = ''
            for times in timez[k]:
                time_text += times + ', '

            text += f'В {day} в: {time_text}\n'
            k += 1

        vk.messages.send(peer_id=evento.obj.from_id,
                         message=f'Значит, вы хотите работать: \n{text}'
                                 '\n{да, нет}',
                         random_id=get_random_id())

        previous_message_id = event.obj.conversation_message_id
        callback = 'create_timetable'


def time_in_timetable(evento):
    global z
    z += 1
    timez.append(evento.obj.text.split(', '))
    print(timez)

    timetable(evento)


def create_timetable(evento):
    global days, timez, z
    k = 0
    for day in days:
        for weekDay in weekDays:
            if day == weekDay[1]:
                day = weekDay[0]

        for time in timez[k]:
            cursor.execute('SELECT * FROM teachers')
            data_arr = cursor.fetchall()

            for data in data_arr:
                if data[0] == evento.obj.from_id:
                    cursor.execute(f"insert into paid_webinars values ({day}, "
                                   f"'{time}', '{data[2]}', {data[0]},"
                                   f" '{data[1]}', '0')")
                    conn.commit()
        k += 1

    cursor.execute(f"update teachers set is_created_timetable = '1' "
                   f"where teacher_id = {evento.obj.from_id}")

    vk.messages.send(peer_id=evento.obj.from_id,
                     message="График занятий создан",
                     random_id=get_random_id())

    days = []
    timez = []
    z = 0


def pupils(evento):

    cursor.execute('SELECT * FROM Users ORDER BY lesson_weekday, lesson_time')
    data_arr = cursor.fetchall()

    text = 'К вам записаны: \n\n'

    for data in data_arr:
        if data[5] == evento.obj.from_id:
            text += f'{data[1]} в {data[3]} на {data[4]}\n'

    vk.messages.send(peer_id=evento.obj.from_id,
                     message=text,
                     random_id=get_random_id())


# Чат


# Функции ученика


def new_user(evento):
        webinars_sum = []
        k = 0

        cursor.execute('SELECT * FROM paid_webinars ORDER BY weekDay')
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
                if i[5] == 1:
                    continue
                webinars_sum.append(i[0])

        text = ''

        if len(webinars_sum) != 0:
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

            previous_message_id = event.obj.conversation_message_id + 1
            callback = 'weekday_pick'
            print(previous_message_id)

        else:
            vk.messages.send(peer_id=evento.obj.from_id,
                             message='Извините, но занятия на этой неделе либо все заняты, '
                                     'либо на этой неделе их не будет',
                             random_id=get_random_id())


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
                            f"where user_id = {evento.obj.from_id}")
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

        cursor.execute('SELECT * FROM paid_webinars ORDER BY weekDay, time')
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

        previous_message_id = evento.obj.conversation_message_id
        print(previous_message_id)


def time_pick(evento):
        global previous_message_id, callback

        cursor.execute('SELECT * FROM Users')
        data_arr = cursor.fetchall()

        cursor.execute('SELECT * FROM paid_webinars ORDER BY weekDay')
        row = cursor.fetchall()

        callback_data = callback.split('/')

        for weekDay in weekDays:
            if callback_data[0] == weekDay[1]:
                callback_data[0] = weekDay[0]
                break

        evento.obj.text = (str(callback_data[0]) + '/' + evento.obj.text).split('/')
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

                        vk.messages.send(peer_id=evento.obj.from_id,
                                         message=f"Отлично, ваш урок будет проводить {i[4]}.\n"
                                         f"Вот контакт вашего учителя: {i[2]}\n"
                                         f"Cвяжитесь с ним в Skype в выбранное время.",
                                         random_id=get_random_id())

                        print('message modified')

                        for weekDay in weekDays:
                            if evento.obj.text[0] == str(weekDay[0]):
                                evento.obj.text[0] = weekDay[1]

                        cursor.execute('SELECT * FROM Users')
                        data_arr = cursor.fetchall()

                        if len(data_arr) > 0:
                            for data in data_arr:
                                if data[0] == evento.obj.from_id:
                                    if data[2] == 0:
                                        vk.messages.send(peer_id=evento.obj.from_id,
                                                         message="Желаете оплатить следующие уроки?"
                                                                 '\n{да, нет}',
                                                         random_id=get_random_id())

                                        previous_message_id = evento.obj.conversation_message_id + 1
                                        print(previous_message_id)
                                        callback = 'buy'
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

                                vk.messages.send(peer_id=evento.obj.from_id,
                                                 message="Чтобы получить домашнее задание, введите /home_work",
                                                 random_id=get_random_id())

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

                            vk.messages.send(peer_id=evento.obj.from_id,
                                             message=f"Отлично, ваш урок будет проводить {i[4]}.\n"
                                             f"Вот контакт вашего учителя: {i[2]}\n"
                                             f"Cвяжитесь с ним в Skype в выбранное время.",
                                             random_id=get_random_id())
                            print('message modified')

                            for weekDay in weekDays:
                                if evento.obj.text[0] == str(weekDay[0]):
                                    evento.obj.text[0] = weekDay[1]

                            cursor.execute('SELECT * FROM Users')
                            data_arr = cursor.fetchall()

                            if len(data_arr) > 0:
                                for data in data_arr:
                                    if data[0] == evento.obj.from_id:
                                        if data[2] == 0:
                                            vk.messages.send(peer_id=evento.obj.from_id,
                                                             message="Желаете оплатить следующие уроки?"
                                                                     '\n{да, нет}',
                                                             random_id=get_random_id())

                                            previous_message_id = evento.obj.conversation_message_id + 1
                                            print(previous_message_id)
                                            callback = 'buy'
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

                                    vk.messages.send(peer_id=evento.obj.from_id,
                                                     message="Чтобы получить домашнее задание, введите 'домашняя работа'",
                                                     random_id=get_random_id())
                                    conn.commit()
                                    break


def continue_study(evento):

        cursor.execute('SELECT * FROM Users')
        data_arr = cursor.fetchall()

        if len(data_arr) > 0:
            for data in data_arr:
                if data[0] == evento.obj.from_id:
                    if data[2] == 0:
                        webinars_sum = []
                        k = 0

                        cursor.execute('SELECT * FROM paid_webinars ORDER BY weekDay')
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
                                if i[5] == 1:
                                    continue
                                webinars_sum.append(i[0])

                        print(webinars_sum)

                        text = ''

                        if len(webinars_sum) != 0:
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
                            callback = 'weekday_pick'
                            print(previous_message_id)
                            break

                        else:
                            vk.messages.send(peer_id=evento.obj.from_id,
                                             message='Извините, но занятия на этой неделе либо все заняты, '
                                                     'либо на этой неделе их не будет',
                                             random_id=get_random_id())
                            break

                    elif data[2] < 13:
                        webinars_sum = []
                        k = 0

                        cursor.execute('SELECT * FROM paid_webinars ORDER BY weekDay')
                        row = cursor.fetchall()

                        for i in row:
                            if len(webinars_sum) != 0:
                                if i[5] == 1:
                                    continue
                                if i[3] != data[5]:
                                    continue
                                if i[0] == webinars_sum[k]:
                                    continue
                                webinars_sum.append(i[0])
                                k += 1
                                print(k)
                            else:
                                if i[5] == 1:
                                    continue
                                webinars_sum.append(i[0])

                        print(webinars_sum)

                        text = ''

                        if len(webinars_sum) != 0:
                            for data in webinars_sum:
                                for weekDay in weekDays:
                                    if data == weekDay[0]:
                                        text += weekDay[1] + '\n'

                            vk.messages.send(peer_id=evento.obj.from_id,
                                             message=f'Занятия будут проводится в следующие дни недели:\n\n'
                                             f'{text}'
                                             '\n\nВведите на какой день недели вы хотели бы записаться.',
                                             random_id=get_random_id())

                            previous_message_id = event.obj.conversation_message_id
                            callback = 'weekday_pick'
                            print(previous_message_id)
                            break

                        else:
                            vk.messages.send(peer_id=evento.obj.from_id,
                                             message='Извините, но занятия на этой неделе либо все заняты, '
                                                     'либо на этой неделе их не будет',
                                             random_id=get_random_id())
                            break

            else:
                buy(event)


def buy(evento):
        process_successful_payment(evento)


def process_successful_payment(evento):

        cursor.execute('SELECT * FROM Users')

        data_arr = cursor.fetchall()

        day = 0

        if len(data_arr) > 0:
            for data in data_arr:
                if data[0] == evento.obj.from_id:
                    if data[2] >= 13:

                        for weekDay in weekDays:
                            if data[3] == weekDay[1]:
                                day = weekDay[0]

                        cursor.execute(
                            f"update paid_webinars set isTaken = 0 "
                            f"where teacher_id = {data[5]} and time = '{data[4]}' and weekDay = {day}")

                        cursor.execute(
                            f"update Users set lesson_Now = 1 where User_ID = {evento.obj.from_id}")
                        break
                    else:
                        cursor.execute(
                            f"update paid_webinars set isTaken = 0 "
                            f"where teacher_id = {data[5]} and time = '{data[4]}' and weekDay = {day}")

                        cursor.execute(
                            f"update Users set lesson_Now = {data[2] + 1} where User_ID = {evento.obj.from_id}")
                        break

        conn.commit()

        vk.messages.send(peer_id=evento.obj.from_id,
                         message=f"Спасибо за покупку, {vk.users.get(user_ids=evento.obj.from_id)[0]['first_name']}!",
                         random_id=get_random_id())
        vk.messages.send(peer_id=evento.obj.from_id,
                         message="Вы оплатили 12 следующих уроков. "
                                 'После каждого занятия учитель будет отправлять вам домашнее задание. '
                                 'Когда вы его выполните, учитель поставит вам оценку, '
                                 'и обучение продолжиться до '
                                 'тех пор, пока вы не побываете на 12 занятиях.',
                         random_id=get_random_id())
        vk.messages.send(peer_id=evento.obj.from_id,
                         message='Вы хотите продолжить обучение с текущим учителем или выбрать нового?'
                                 '\n{Выбрать нового, Оставить текущего}',
                         random_id=get_random_id())

        global previous_message_id

        previous_message_id = evento.obj.conversation_message_id + 2
        print(previous_message_id)


def teacher_pick(evento):
        global previous_message_id, callback

        cursor.execute('SELECT * FROM teachers')
        row = cursor.fetchall()

        if callback == 'teacher_pick_new':
            text = ''

            for data in row:
                text += data[1] + '\n'

            vk.messages.send(peer_id=evento.obj.from_id,
                             message='С каким учителем вы желаете продолжить обучение?\n\n'
                             f'{text}'
                                     '\n\nВведите имя выбранного учителя',
                             random_id=get_random_id())

            previous_message_id = event.obj.conversation_message_id
            print(previous_message_id)

        else:
            vk.messages.send(peer_id=evento.obj.from_id,
                             message='Хорошо, за вами будет закреплен ваш текущий учитель.',
                             random_id=get_random_id())
            vk.messages.send(peer_id=evento.obj.from_id,
                             message=f"Желаете записаться на следующее занятие?"
                             '\n{да, нет}',
                             random_id=get_random_id())
            callback = 'continue'
            previous_message_id = event.obj.conversation_message_id + 1
            print(previous_message_id)


def teacher_pick2(evento):

        cursor.execute('SELECT * FROM Users')
        data_arr = cursor.fetchall()

        cursor.execute('SELECT * FROM teachers')
        row = cursor.fetchall()

        teacher_id = 0

        for teacher in row:
            if evento.obj.text == str(teacher[1]):
                teacher_id = teacher[0]
                break

        for data in data_arr:
            if data[0] == evento.obj.from_id:
                cursor.execute(
                    f"update Users set teacher_id = {teacher_id} "
                    f"where user_id = {evento.obj.from_id}")

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

        vk.messages.send(peer_id=evento.obj.from_id,
                         message=f'Отлично, вы продолжите обучение с учителем по имени {evento.obj.text}.',
                         random_id=get_random_id())

        vk.messages.send(peer_id=evento.obj.from_id,
                         message=f"Желаете записаться на следующее занятие?"
                         '\n{да, нет}',
                         random_id=get_random_id())

        global previous_message_id, callback
        callback = 'continue'
        previous_message_id = event.obj.conversation_message_id + 1
        print(previous_message_id)


def home_work(evento):
        cursor.execute('SELECT * FROM home_work')
        row = cursor.fetchall()

        for data in row:

            if data[0] == evento.obj.from_id:
                if data[3] == "Ожидается ссылка":
                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message=f'Учитель еще не отправил вам домашнее задание',
                                     random_id=get_random_id())
                    break
                else:
                    cursor.execute(
                        f"update Users set lesson_Now = {data[2] + 1} where User_ID = {evento.obj.from_id}")
                    cursor.execute(
                        f"update home_work set hw_link = 'Ожидается ссылка' where user_id = {evento.obj.from_id}")

                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message=f"Вот ваше д/з: \n{data[3]} \n\nЧтобы узнать оценку введите /grade",
                                     random_id=get_random_id())

                    conn.commit()
                    break


def grade(evento):
        cursor.execute('SELECT * FROM home_work')
        row = cursor.fetchall()

        for data in row:

            if data[0] == evento.obj.from_id:
                if data[4] == "Ожидается оценка":
                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message="Учитель еще не поставил вам оценку за домашнее задание,"
                                             " повторите команду позднее",
                                     random_id=get_random_id())
                    break

                else:
                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message=f"Ваша оценка за последнее выполненное д/з: {data[4]}",
                                     random_id=get_random_id())
                    vk.messages.send(peer_id=evento.obj.from_id,
                                     message=f"Желаете записаться на следующее занятие?"
                                     '\n{да, нет}',
                                     random_id=get_random_id())

                    global previous_message_id, callback
                    callback = 'continue'
                    previous_message_id = event.obj.conversation_message_id + 1
                    print(previous_message_id)
                    break


for event in longpoll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:

            if event.obj.text.lower() == 'начать':
                start_command(event)
            elif event.obj.text.lower() == 'домашняя работа':
                home_work(event)
            elif event.obj.text.lower() == 'оценка':
                grade(event)

            if event.obj.conversation_message_id == previous_message_id + 2:
                print('pr + 2')

                if event.obj.text.lower() == 'создать график занятий':
                    cursor.execute('SELECT * FROM teachers')
                    row2 = cursor.fetchall()
                    for teacher in row2:
                        if event.obj.from_id == teacher[0]:
                            if teacher[3] == 1:
                                print('teacher 1')
                                cursor.execute(f"DELETE FROM `paid_webinars` WHERE `teacher_id`={event.obj.from_id}")
                                cursor.execute(f"update teachers set is_created_timetable = '0' "
                                               f"where teacher_id = {event.obj.from_id}")
                                conn.commit()

                            vk.messages.send(peer_id=event.obj.from_id,
                                             message='При повторном вводе этой команды все предыдущие записи '
                                                     'о занятиях будут стерты.\n'
                                                     'Введите через запятую, в какие дни вы хотели бы работать.'
                                                     '\n\n'
                                                     'Например: Понедельник, вторник, пятница',
                                             random_id=get_random_id())
                            callback = 'timetable'
                            previous_message_id = event.obj.conversation_message_id
                            break

                elif event.obj.text.lower() == 'посмотреть записанных учеников':
                    pupils(event)

                elif ':' in event.obj.text.lower():
                    if callback == 'time_in_timetable':
                        time_in_timetable(event)
                    else:
                        time_pick(event)

                elif event.obj.text.lower() == 'да':
                    if callback == 'continue':
                        continue_study(event)
                    elif callback == 'buy':
                        buy(event)
                    elif callback == 'create_timetable':
                        create_timetable(event)

                elif event.obj.text.lower() == 'выбрать нового' or event.obj.text.lower() == 'оставить текущего':
                    if event.obj.text.lower() == 'выбрать нового':
                        callback = 'teacher_pick_new'
                    else:
                        callback = 'teacher_pick_old'
                    teacher_pick(event)

                elif event.obj.text.lower() == 'нет':
                    previous_message_id = 0
                    callback = ''
                    days = []
                    timez = []
                    z = 0
                    pupil_id = 0
                    chat_counter = 0
                    chat_isOver = 1
                    start_command(event)

                elif callback == 'weekday_pick':
                    cursor.execute('SELECT * FROM paid_webinars ORDER BY weekDay')
                    row2 = cursor.fetchall()
                    for weekDay in weekDays:
                        if weekDay[1] in event.obj.text.lower():
                            for data2 in row2:
                                if weekDay[0] == data2[0]:
                                    callback = f'{weekDay[1]}/{data2[3]}'
                                    weekday_pick(event, weekDay)
                                    break

                elif callback == 'timetable':
                    for weekDay in weekDays:
                        if weekDay[1] in event.obj.text.lower():
                            timetable(event)
                            break

                elif callback == 'teacher_pick_new':
                    cursor.execute('SELECT * FROM teachers')
                    row2 = cursor.fetchall()
                    for teacher in row2:
                        if event.obj.text == str(teacher[1]):
                            teacher_pick2(event)
                            break

                else:
                    vk.messages.send(peer_id=event.obj.from_id,
                                     message='Введите сообщение правильно',
                                     random_id=get_random_id())
                    previous_message_id += 2
