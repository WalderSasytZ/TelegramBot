import telebot
import sqlite3
import datetime
import time
import threading

person_id = { "мак": 769231781, "?нина": 779020072, "папа": 1653991970, "егас": 632578036 , "герман": 1798118387, "я": 1082479755 }
id_person = {}
for name, _id in person_id.items():    id_person[_id] = name

bot = telebot.TeleBot('6213643172:AAEQRvpNShPsImla-2fSRCBkkMLzlh7Y80I')




# create a table in a datebase
conn = sqlite3.connect('reminders.db')
conn.execute('''CREATE TABLE IF NOT EXISTS reminders (
                    reminder_id INTEGER PRIMARY KEY NOT NULL,
                    chat_id INTEGER NOT NULL,
                    remind_date TEXT,
                    remind_text TEXT
                );''')
conn.close()

# print datebase info in console
@bot.message_handler(commands=['print_all'])
def print_datebase_admin(message):
    if message.chat.id != 1082479755: return
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute(''' SELECT * FROM reminders;''')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    print()
    bot.send_message(message.chat.id, 'all data is printed')
    conn.close()

#delete all data from table
@bot.message_handler(commands=['delete_all'])
def delete_datebase_admin(message):
    if message.chat.id != 1082479755: return
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM reminders;''')
    print('all data is deleted')
    bot.send_message(message.chat.id, 'all data is deleted')
    conn.commit()
    conn.close()

@bot.message_handler(commands=['create'])
def create_message_admin(message):
    if message.chat.id != 1082479755: return
    request = message.text.split()
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()

    # create a unique id
    cursor.execute(''' SELECT MAX(reminder_id)
                           FROM reminders;''')
    result = cursor.fetchone()
    if result[0] is None:
        reminder_id = 0
    else:
        reminder_id = result[0] + 1

    # transform name
    if request[1] in person_id:
        name = person_id[request[1]]
    else:
        name = request[1]

    # create date
    try:
        date = datetime.datetime.strptime(request[2], '%d.%m.%Y_%H:%M')
    except ValueError:
        bot.send_message(message.chat.id, 'date error')
        return

    # merge text
    text = ''
    for i in range(3, len(request)):
        text += request[i] + ' '

    # insert reminder into database
    cursor.execute(''' INSERT INTO reminders (reminder_id, chat_id, remind_date, remind_text)
                       VALUES (?, ?, ?, ?)
                   ''', (reminder_id, name, date, text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, 'succesfully')

# back to begin of dialogue
@bot.message_handler(commands=['home'])
def go_home(message):
    bot.send_message(message.chat.id, 'Вы уже в начале диалога.')

# create new reminder
@bot.message_handler(commands=['new'])
def new_reminder(message):
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()

    # find a number of undone cartages for this person
    cursor.execute(''' SELECT COUNT(*)
                       FROM reminders
                       WHERE chat_id = ? AND remind_text IS NULL;
                   ''', (message.chat.id,))
    undone_cartage_num = cursor.fetchone()[0]
    reminder_id = None

    # if person does not have an undone cartage
    if undone_cartage_num == 0:

        # find the biggest reminder_id
        cursor.execute(''' SELECT MAX(reminder_id)
                           FROM reminders;''')
        result = cursor.fetchone()

        # create a unique id for reminder
        if result[0] is None:
            reminder_id = 0
        else:
            reminder_id = result[0] + 1

        # create an empty cartage for reminder
        cursor.execute('''INSERT INTO reminders (reminder_id, chat_id, remind_date, remind_text)
                          VALUES (?, ?, NULL, NULL)
                       ''', (reminder_id, message.chat.id,))
    else:

        # find an undone cartage
        cursor.execute(''' SELECT reminder_id
                           FROM reminders
                           WHERE chat_id = ? AND remind_text IS NULL;
                       ''', (message.chat.id,))
        reminder_id = cursor.fetchone()[0]
    bot.send_message(message.chat.id, 'Введи дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ для нового напоминания.')
    conn.commit()
    conn.close()
    bot.register_next_step_handler(message, set_date, reminder_id)

def set_date(message, reminder_id):
    if message.text == '/home':
        bot.send_message(message.chat.id, 'Вы вернулись в начало диалога.')
        return
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    try:
        # set a date of reminder for current person
        date = datetime.datetime.strptime(message.text, '%d.%m.%Y %H:%M')
        cursor.execute('''UPDATE reminders           
                          SET remind_date = ?
                          WHERE reminder_id = ?
                       ''', (date, reminder_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, 'Теперь введи текст напоминания.')
        bot.register_next_step_handler(message, set_remind_text, reminder_id)
    except ValueError:
        bot.send_message(message.chat.id, 'Не удалось распознать дату и время.\n Попробуй еще раз.')
        bot.register_next_step_handler(message, set_date, reminder_id)

def set_remind_text(message, reminder_id):
    if message.text == '/home':
        bot.send_message(message.chat.id, 'Вы вернулись в начало диалога.')
        return
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()

    # set a text of reminder for current person
    cursor.execute('''UPDATE reminders           
                      SET remind_text = ?
                      WHERE reminder_id = ?
                   ''', (message.text, reminder_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, 'Напоминание успешно создано!')
    print(str(reminder_id) + ' was created by ' + id_person[message.chat.id] if message.chat.id in id_person else message.chat.id)

@bot.message_handler(commands=['print'])
def print_reminders(message):
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()

    # select all reminders for current person
    cursor.execute(''' SELECT reminder_id, remind_date, remind_text
                       FROM reminders
                       WHERE chat_id = ? AND remind_text IS NOT NULL;
                   ''', (message.chat.id,))
    results = cursor.fetchall()
    
    # print reminders
    bot.send_message(message.chat.id, 'Количество напоминаний: ' + str(len(results)))
    for result in results:
        _id = result[0]
        date = result[1]
        text = result[2]
        bot.send_message(message.chat.id, 'Номер: ' + str(_id) + '\n' +
                                          'Дата и время: ' + date + '\n' +
                                          'Текст: ' + text)
    conn.close()

# delete a reminder
@bot.message_handler(commands=['delete'])
def delete_reminder(message):
    print_reminders(message)

    # check a number of reminders for current person
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute(''' SELECT reminder_id, remind_date, remind_text
                       FROM reminders
                       WHERE chat_id = ? AND remind_text IS NOT NULL;
                   ''', (message.chat.id,))
    results = cursor.fetchall()

    # stop function if there are no reminders
    if len(results) == 0: return

    bot.send_message(message.chat.id, 'Укажите номер напоминания которое вы хотите удалить.')
    bot.register_next_step_handler(message, delete_id)

def delete_id(message):
    if message.text == '/home':
        bot.send_message(message.chat.id, 'Вы вернулись в начало диалога.')
        return
    try:
        remind_id = int(message.text)
    except:
        bot.send_message(message.chat.id, 'В качестве номера должно быть целое число. Попробуйте ещё раз, либо вернитесь в начало командой /home')
        bot.register_next_step_handler(message, delete_id)
        return
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()

    # find a number of reminders which person want to delete ( 0 or 1 )
    cursor.execute(''' SELECT COUNT(*)
                       FROM reminders
                       WHERE reminder_id = ? AND chat_id = ?;
                   ''', (remind_id, message.chat.id,))
    result = cursor.fetchall()[0]
    if result == 0:
        bot.send_message(message.chat.id, 'У вас нету напоминания с таким номером. Попробуйте ещё раз, либо вернитесь в начало командой /home')
        bot.register_next_step_handler(message, delete_id)
        return
    bot.send_message(message.chat.id, 'Вы уверены что хотите удалить это напоминание? Ответьте "да" если хотите.')
    bot.register_next_step_handler(message, confirm_delete, remind_id)

def confirm_delete(message, remind_id):
    if message.text == '/home':
        bot.send_message(message.chat.id, 'Вы вернулись в начало диалога.')
        return
    if message.text != 'да' and message.text != 'Да' and message.text != 'дA' and message.text != 'ДА':
        bot.send_message(message.chat.id, 'Напоминание не удалено.')
        return

    # deleting a reminder
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute(''' DELETE FROM reminders
                       WHERE reminder_id = ?;
                   ''', (remind_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, 'Напоминание успешно удалено!')
    print(str(remind_id) + ' was deleted by ' + id_person[message.chat.id] if message.chat.id in id_person else message.chat.id)

def remind_checker():
    while True:
        # find current time
        now = datetime.datetime.now()

        # find reminders to send
        conn = sqlite3.connect('reminders.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT chat_id, remind_text
                      FROM reminders
                      WHERE remind_text IS NOT NULL AND remind_date <= ?;
                   ''', (now,))
        results = cursor.fetchall()

        # sending reminders
        for result in results:
            chat_id = result[0]
            remind_text = result[1]
            bot.send_message(chat_id, 'На данный момент у вас запланировано напоминание:')
            bot.send_message(chat_id, remind_text)
    
        # deleting irrelevant reminders
        cursor.execute('''DELETE FROM reminders
                          WHERE remind_date <= ?;
                       ''', (now,))
    
        conn.commit()
        conn.close()
        time.sleep(1)

remind_checker_thread = threading.Thread(target=remind_checker)
remind_checker_thread.start()

bot.polling()