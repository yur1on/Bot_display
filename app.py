
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


import config
from config import ADMIN_ID

from baza import glass_data, glass_data2, glass_data3, glass_data4, glass_data5, glass_data6, glass_data7
from baza2 import glass_data9
import sqlite3
import os






# Инициализация бота и диспетчера

bot = Bot(config.tok)
dp = Dispatcher(bot, storage=MemoryStorage())



conn = sqlite3.connect('user_database.db')
cursor = conn.cursor()


# Добавте столбец chat_id, если его нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,  -- Добавьте этот столбец
        name TEXT,
        city TEXT,
        phone_number TEXT
    )
''')

# Создаем таблицу для хранения сообщений
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        message_text TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS blocked_users (
    user_id INTEGER PRIMARY KEY
)
''')


conn.commit()


# Проверка, заблокирован ли пользователь
def is_user_blocked(user_id):
    cursor.execute('SELECT 1 FROM blocked_users WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None


# Блокировка пользователя
@dp.message_handler(commands=['block'], user_id=ADMIN_ID)
async def block_user(message: types.Message):
    try:
        user_id_to_block = int(message.text.split()[1])
        cursor.execute('INSERT INTO blocked_users (user_id) VALUES (?)', (user_id_to_block,))
        conn.commit()
        await message.reply(f"Пользователь с ID {user_id_to_block} заблокирован.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду в формате: /block <user_id>")


# Разблокировка пользователя
def unblock_user(user_id):
    cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id,))
    conn.commit()

# Обработчик команды /unblock
@dp.message_handler(commands=['unblock'], user_id=ADMIN_ID)
async def unblock_user_command(message: types.Message):
    try:
        user_id_to_unblock = int(message.text.split()[1])
        unblock_user(user_id_to_unblock)
        await message.reply(f"Пользователь с ID {user_id_to_unblock} разблокирован.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду в формате: /unblock <user_id>")


belarusian_cities = [
    "minsk", "минск",
    "grodno", "гродно",
    "brest", "брест",
    "vitebsk", "витебск",
    "mogilev", "могилев",
    "gomel", "гомель",
    "baranovichi", "барановичи",
    "bobruisk", "бобруйск",
    "borisov", "борисов",
    "pinsk", "пинск",
    "orsha", "орша",
    "mozyr", "мозырь",
    "soligorsk", "солигорск",
    "lida", "лида",
    "novopolotsk", "новополоцк",
    "polotsk", "полоцк",
    "Кобрин", "Инск",
    "Мин", "Ошмяны",
    "Слуцк", "Житковичи",
    "Rechitsa", "Речица",
    "Ошмяны", "Novokuznetsk",
    "Толочин", "микашевичи",
    "Пружаны"

]

# Функция для получения всех зарегистрированных пользователей
def get_belarusian_chat_ids():
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, city FROM users")
    users = cursor.fetchall()
    conn.close()

    # Фильтруем пользователей, чьи города есть в списке белорусских городов
    belarusian_chat_ids = [chat_id for chat_id, city in users if city and city.lower() in belarusian_cities]
    return belarusian_chat_ids



# Функция для отправки сообщения всем зарегистрированным пользователям
async def send_updates_to_all_users(bot, message_text):
    chat_ids = get_belarusian_chat_ids()
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, message_text)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")



# Обработчик команды /send
@dp.message_handler(commands=['send'])
async def send_updates_command(message: types.Message):
    # Проверяем, что пользователь, отправивший команду, является администратором
    if message.from_user.id == 486747175:  # Замените ADMIN_USER_ID на ваш ID
        message_text = "Друзья! Представляем новый проект — mobirazbor.by :\nплатформа для разборщиков мобильной техники,\nудобный сервис для учёта и поиска запчастей мобильной техники.\n🔹Личный склад\n🔹Умный поиск по всей базе\n🔹Поддержка фото, описаний, отзывов и связи между пользователями\n📢Присоединяйтесь к Telegram-каналу: t.me/MobiraRazbor\nСледите за развитием платформы и обновлениями."
        await send_updates_to_all_users(bot, message_text)
        await message.answer("Сообщение отправлено всем зарегистрированным пользователям.")
    else:
        await message.answer("У вас нет прав для отправки сообщений.")


# Обработчик команды /send_to_user
@dp.message_handler(commands=['send_to_user'])
async def send_to_user_command(message: types.Message):
    # Проверяем, что пользователь, отправивший команду, является администратором
    if message.from_user.id == 486747175:  # Замените ADMIN_USER_ID на ваш ID
        try:
            # Получаем аргумент команды, который должен содержать ID пользователя
            user_id = int(message.text.split()[1])
            # Получаем текст сообщения
            message_text = ' '.join(message.text.split()[2:])

            # Отправляем сообщение пользователю с заданным ID
            await bot.send_message(user_id, message_text)
            await message.answer("Сообщение отправлено пользователю с ID: " + str(user_id))
        except (IndexError, ValueError):
            await message.answer("Неверный формат команды. Используйте /send_to_user <ID пользователя> <текст сообщения>")
    else:
        await message.answer("У вас нет прав для отправки сообщений.")



# Функция для получения информации о пользователе по chat_id
def get_user_info(chat_id):
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name, city, phone_number FROM users WHERE chat_id=?", (chat_id,))
    user_info = cursor.fetchone()

    conn.close()

    return user_info  # Возвращает кортеж (name, city, phone_number) или None, если пользователь не найден

# Добавляем новый класс для состояний поиска по размерам
class UserSizeSearch(StatesGroup):
    height = State()
    width = State()


# Добавляем новый обработчик команды/кнопки для инициирования поиска по размерам
@dp.message_handler(lambda message: message.text == '/size')
async def start_size_search(message: types.Message, state: FSMContext):

    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()
    # Проверяем, зарегистрирован ли пользователь
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(chat_id, "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration ")
        return
    await bot.send_message(chat_id, "🔘Эта функция по введенному Вами запросу (длина и ширина), покажет стекла с одинаковыми размерами. \n🔘Точность измерения проводилась с округлением до <b>0.5мм</b>.\nБаза каждый день наполняеться.  \n\n<b>Введите длину стекла 📱в мм:</b>\nПример ввода: 155 или 155,5", parse_mode='html')
    # Установка состояние для обработки введенных значений
    await UserSizeSearch.height.set()

# Добавляем новый обработчик команды/кнопки для инициирования поиска по размерам
@dp.message_handler(lambda message: message.text == '🔎подбор стекла по размеру')
async def start_size_search(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()
    # Проверяем, зарегистрирован ли пользователь
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(chat_id, "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration ")
        return
    await bot.send_message(chat_id, "🔘Эта функция по введенному Вами запросу (длина и ширина), покажет стекла с одинаковыми размерами. \n🔘Точность измерения проводилась с округлением до <b>0.5мм</b>.\nБаза каждый день наполняеться.  \n\n<b>Введите длину стекла 📱в мм:</b>\nПример ввода: 155 или 155,5", parse_mode='html')
    # Установка состояние для обработки введенных значений
    await UserSizeSearch.height.set()


# Обработчик ввода высоты
@dp.message_handler(state=UserSizeSearch.height)
async def process_height(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    try:
        # Замена запятой на точку и преобразование в число
        height = float(message.text.replace(',', '.'))

        # Сохранения значения высоты в контексте состояния
        await state.update_data(height=height)

        # Запрос у пользователя значение ширины
        await bot.send_message(chat_id, "<b>Теперь введите ширину ↔📱 в мм:</b>", parse_mode='html')
        await UserSizeSearch.width.set()
    except ValueError:
        await bot.send_message(chat_id, "Некорректный формат ввода размера стекла! Пожалуйста, введите число.\n\n<b>Введите длину стекла 📱в мм:</b>\nПример ввода: 155 или 155,5", parse_mode='html')


# Обработчик ввода ширины
@dp.message_handler(state=UserSizeSearch.width)
async def process_width(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    try:
        # Замените запятую на точку и преобразуйте в число
        width = float(message.text.replace(',', '.'))

        # Получите значение высоты из контекста состояния
        user_data = await state.get_data()
        height = user_data.get('height')

        # Выполните поиск по размерам
        found_glasses9 = perform_size_search(height, width)

        if found_glasses9:
            response_header = f"<em><u>Стекла по размерам {height}x{width} найдено:</u></em>\n"

            # Отправляем текст только один раз перед циклом
            await bot.send_message(chat_id, response_header, parse_mode='HTML')

            for glass9 in found_glasses9:
                model = glass9['model']
                photo_path = glass9['photo_path']

                if photo_path:
                    # Загружаем фотографию в виде обычного вложения
                    with open(photo_path, 'rb') as photo:
                        # Создаем сообщение с текстом и фото
                        await bot.send_photo(chat_id, photo, caption=f"<b>Модель:</b> {model}", parse_mode='HTML')
                else:
                    # Если фото нет, просто отправляем текстовое сообщение
                    await bot.send_message(chat_id, f"<b>Модель:</b> {model}", parse_mode='HTML')

            user_info = get_user_info(chat_id)
            if user_info:
                await UserSizeSearch.height.set()
            else:
                await bot.send_message(chat_id, "Для использования поиска по размерам, сначала зарегистрируйтесь! Используйте команду /registration")
        else:
            await bot.send_message(chat_id, "🔘По указанным размерам ничего не найдено!\n 🔘Побрубуйте увеличить или уменьшить размер в запросе на 0,5мм")

        # Завершите состояние
        await state.finish()
    except ValueError:
        await bot.send_message(chat_id, "Некорректный формат ввода!\nПожалуйста, введите число.")



# class UserRegistration(StatesGroup):
#     name = State()
#     city = State()
#     phone_number = State()
#     is_registered = State()


# Обработчик команды /delete_registration
@dp.message_handler(commands=['delete_registration'])
async def delete_registration(message: types.Message):
    chat_id = message.chat.id


    # Удалить пользователя из базы данных
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

    await bot.send_message(chat_id, "Ваши регистрационные данные успешно удалены. Для повторной регистрации используйте команду /registration")




async def create_menu_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    start_button = types.KeyboardButton('🚀 start')
    registration_button = types.KeyboardButton('🗂registration')
    help_button = types.KeyboardButton('ℹ️ Info')
   #size_search_button = types.KeyboardButton('🔎подбор стекла по размеру')
    markup.add(start_button, registration_button, help_button,) #size_search_button)
    return markup




# Определения состояния регистрации пользователя
class UserRegistration(StatesGroup):
    name = State()
    city = State()
    phone_number = State()
    is_registered = False  # По умолчанию пользователь не зарегистрирован

@dp.message_handler(state=UserRegistration.name)
async def register_name(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    name = message.text
    await state.update_data(name=name)
    await UserRegistration.city.set()
    await bot.send_message(chat_id, "Введите Ваш город:", reply_markup=await create_menu_button())
    UserRegistration.is_registered = True

@dp.message_handler(lambda message: message.text.isdigit(), state=UserRegistration.city)
async def register_invalid_phone(message: types.Message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Некорректно введен город!")

@dp.message_handler(state=UserRegistration.city)
async def register_city(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    city = message.text
    await state.update_data(city=city)
    await UserRegistration.phone_number.set()
    await bot.send_message(chat_id, "Введите Ваш номер телефона:")

@dp.message_handler(lambda message: not message.text.isdigit(), state=UserRegistration.phone_number)
async def register_invalid_phone(message: types.Message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Номер телефона должен содержать только цифры. Пожалуйста, введите корректный номер телефона.")

@dp.message_handler(lambda message: message.text.isdigit(), state=UserRegistration.phone_number)
async def register_phone_number(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    phone_number = message.text
    user_data = await state.get_data()
    name = user_data.get('name')
    city = user_data.get('city')

    # Сохраняем данные пользователя в базу данных
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (chat_id, name, city, phone_number) VALUES (?, ?, ?, ?)", (chat_id, name, city, phone_number))
    conn.commit()
    conn.close()

    await state.finish()
    await bot.send_message(chat_id, "Регистрация успешно завершена!\n\nВведите модель стекла телефона или планшета, которое вы ищите.\n\n Изучите информацию и откройте доп. кнопки 👉 /info")

@dp.message_handler(commands=['registration'])
async def start_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_info = get_user_info(chat_id)

    if user_info:
        user_name, user_city, user_phone = user_info
        await bot.send_message(chat_id, f"Вы зарегистрированы! \n"
                                       f"Ваше имя: {user_name}\n"
                                       f"Ваш город: {user_city}\n"
                                       f"Ваш № тел.: {user_phone}\n\n"
                                       f"Для удаления регистрационных данных введите команду /delete_registration")
    else:
        await bot.send_message(chat_id, f"Здравствуйте!\n"
                                       f"Введите свое имя для регистрации:")
        await UserRegistration.name.set()

@dp.message_handler(lambda message: message.text == '🗂registration')
async def start_message(message: types.Message, state: FSMContext):
    user = message.from_user
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    chat_id = message.chat.id
    user_info = get_user_info(chat_id)

    if user_info:
        user_name, user_city, user_phone = user_info
        await bot.send_message(chat_id, f"Вы зарегистрированы! \n"
                                       f"Ваше имя: {user_name}\n"
                                       f"Ваш город: {user_city}\n"
                                       f"Ваш № тел.: {user_phone}\n\n"
                                        f"Для удаления регистрационных данных введите команду /delete_registration")
    else:
        await bot.send_message(chat_id, f"Здравствуйте!\n"
                                       f"Введите свое имя для регистрации:")
        await UserRegistration.name.set()



async def send_message_with_ad(chat_id, text, reply_markup=None, parse_mode='html'):
    ad_text = "\n\nmobirazbor.by"
    await bot.send_message(chat_id, text + ad_text, reply_markup=reply_markup, parse_mode=parse_mode)



@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = message.from_user
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    user_info = get_user_info(chat_id)
    if user_info:
        await send_message_with_ad(
            chat_id,
            f"Привет👋, @{message.from_user.username}!\n Введите модель стекла телефона или планшета, которое вы ищете.\n Изучите информацию и откройте доп. кнопки 👉 /info"
        )
    else:
        await send_message_with_ad(
            chat_id,
            "Это бот для поиска взаимозаменяемых стекол для переклейки.\nДля пользования ботом, пожалуйста, зарегистрируйтесь! Используйте команду /registration"
        )

@dp.message_handler(lambda message: message.text == '🚀 start')
async def start(message: types.Message):
    user = message.from_user
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    chat_id = message.chat.id
    user_info = get_user_info(chat_id)

    if user_info:
        await bot.send_message(chat_id, f"Привет👋, @{message.from_user.username}\n Введите модель стекла телефона или планшета, которое вы ищете.\n Изучите информацию и откройте доп. кнопки 👉 /info")
    else:
        await bot.send_message(chat_id, "Это бот для поиска взаимозаменяемых стекол для переклейки.\nДля пользования ботом, пожалуйста, зарегистрируйтесь! Используйте команду /registration")





# Обработчик команды /info
@dp.message_handler(commands=['info'])
async def handle_help(message):
    user = message.from_user
    chat_id = message.chat.id
    if user.username:
        await bot.send_message(chat_id, "🤖 Я бот для поиска взаимозаменяемых моделей стекол телефонов и планшетов.\n\n"
                              "✔️Для поиска взаимозаменяемых стекол отправьте сообщения нужной модели\n\n"
                              "✔️Для подбора стекла по размерам используте команду /size\n\n"
                              "✔️/registration - команда для регистрации\n\n"
                              "✔️/delete_registration - команда для удаления своих регистрационных данных из базы\n\n"
                              "✔️Если нашли ошибку или знаете взаимозаменяемую модель стекла, напишите пожалуйста @expert_glass_lcd \n", reply_markup=await create_menu_button())





# Обработчик команды /info
@dp.message_handler(lambda message: message.text == 'ℹ️ Info')
async def handle_help(message):
    user = message.from_user
    chat_id = message.chat.id
    user_message = message.text

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    user = message.from_user
    chat_id = message.chat.id
    if user.username:
        await bot.send_message(chat_id, "🤖 Я бот для поиска взаимозаменяемых моделей стекол телефонов и планшетов.\n\n"
                              "✔️Для поиска взаимозаменяемых стекол отправте сообщения нужной модели\n\n"
                              "✔️Для подбора стекла по размерам используте команду /size\n\n"
                              "✔️/registration - команда для регистрации\n\n"
                              "✔️/delete_registration - команда для удаления своих регистрационных данных из базы\n\n"
                              "✔️Если нашли ошибку или знаете взаимозаменяемую модель стекла, напишите пожалуйста @expert_glass_lcd \n", reply_markup=await create_menu_button())




def perform_size_search(height, width):

    found_glasses9 = []

    for glass9 in glass_data9:
        if glass9["height"] == height and glass9["width"] == width:
            found_glasses9.append({
                "model": glass9['model'],
                "photo_path": glass9.get('photo_path', None)  # Если нет фото, будет None
            })

    return found_glasses9





@dp.message_handler()
async def handle_text(message, state: FSMContext):
    user_message = message.text.lower() # Приводим текст к нижнему регистру для удобства сравнения
    chat_id = message.chat.id

    # Сохранение сообщения в базу данных
    cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, user_message))
    conn.commit()

    # проверяем заблокирован ли пользователь
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        await message.reply("Вы заблокированы и не можете использовать этого бота.")
        return

    # Проверяем, содержит ли запрос слово "galaxy"
    if 'galaxy' in user_message:
        await bot.send_message(chat_id, "Повторите пожалуйста запрос не используя слово <b>galaxy</b>.", parse_mode='html')
        return
    # Проверяем, содержит ли запрос слово "realmi"
    if 'realmi' in user_message:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>realmi</u> на правильное написание <b>realme</b>.", parse_mode='html')
        return
    # Проверяем, содержит ли запрос слово "techno"
    if 'techno' in user_message:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>techno</u> на правильное написание <b>tecno</b>.", parse_mode='html')
        return
    # Проверяем, содержит ли запрос слово "comon"
    if 'comon' in user_message:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>comon</u> на правильное написание <b>camon</b>.", parse_mode='html')
        return
    # Проверяем, содержит ли запрос слово "tekno"
    if 'tekno' in user_message:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>tekno</u> на правильное написание <b>tecno</b>.", parse_mode='html')
        return
    # Проверяем, содержит ли запрос знак "+"
    if '+' in user_message:
        await bot.send_message(chat_id, "❗️Исправте в запросе знак <u>+</u> на слово <b>plus</b>.", parse_mode='html')
        return

    # Проверяем, содержит ли запрос запрещенные слова
    forbidden_words = ['хонор', 'самсунг', 'редми', 'реалми', 'хуавей', 'техно', 'виво', 'ксиаоми', 'инфиникс', 'айфон', 'асус', 'сони', 'а', 'б', 'с', 'в', 'г', 'и', 'л', 'к', 'е', 'у', 'э', 'з']
    if any(word in user_message for word in forbidden_words):
        forbidden_words_str = ', '.join(forbidden_words)
        await bot.send_message(chat_id, f"Пожалуйста пишите модель на английском языке")
        return

    # Создаем клавиатуру с кнопкой "Посмотреть фото"
    keyboard = types.InlineKeyboardMarkup()
    keyboard1 = types.InlineKeyboardMarkup()
    keyboard2 = types.InlineKeyboardMarkup()
    keyboard3 = types.InlineKeyboardMarkup()
    keyboard4 = types.InlineKeyboardMarkup()

    # Проверяем, зарегистрирован ли пользователь
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(chat_id, "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration ")
        return




    found_glasses = []
    found_glasses2 = []
    found_glasses3 = []
    found_glasses4 = []
    found_glasses5 = []
    found_glasses6 = []
    found_glasses7 = []



    for model, glasses in glass_data:
        if user_message.lower() == model.lower():
            found_glasses = glasses
            photo_name = glasses[-1]  # Имя файла фото
            break


    for model, glasses in glass_data2:
        if user_message.lower() == model.lower():
            found_glasses2 = glasses
            photo_name1 = glasses[-1]  # Имя файла фото
            break


    for model, glasses in glass_data3:
        if user_message.lower() == model.lower():
            found_glasses3 = glasses
            photo_name2 = glasses[-1]  # Имя файла фото
            break



    for model, glasses in glass_data4:
        if user_message.lower() == model.lower():
            found_glasses4 = glasses
            photo_name3 = glasses[-1]  # Имя файла фото
            break

    for model, glasses in glass_data5:
        if user_message.lower() == model.lower():
            found_glasses5 = glasses
            break

    for model, glasses in glass_data6:
        if user_message.lower() == model.lower():
            found_glasses6 = glasses
            photo_name4 = glasses[-1]  # Имя файла фото
            break

    for model, glasses in glass_data7:
        if user_message.lower() == model.lower():
            found_glasses7 = glasses
            break

    AD_TEXT = (
        '\n\n<b>Для жителей РБ 🇧🇾</b>\n'
        'Сервис для разборщиков мобильной техники.\n'
        'Канал: <a href="https://t.me/MobiraRazbor">@MobiraRazbor</a>\n'
        'Чат: <a href="https://t.me/mobirazbor_chat">@mobirazbor_chat</a>\n'
        'Сайт: <a href="https://mobirazbor.by">mobirazbor.by</a>'
    )

    if found_glasses5:
        response = f"<em>Я знаю многое о продукции<b> {user_message}</b>. Укажите конкретную модель!</em>\n"
        response += "\n".join(found_glasses5)
        await bot.send_message(chat_id, response, parse_mode='html')
     #Проверяем, если сообщение содержит ключевые слова
    elif found_glasses7:
        response = f"<em>Уточните, какая именно модель<b> {user_message}</b> Вас интересует?</em>\n"
        response += "\n".join(found_glasses5)
        await bot.send_message(chat_id, response, parse_mode='html')


    else:

        # ПЕРВЫЙ блок: сюда добавляем рекламу AD_TEXT

        if found_glasses:

            response = (

                f"<em><u>Взаимозаменяемые стекла по поиску "

                f"🔍<b>'{user_message}'</b> найдено:</u></em>\n"

            )

            for index, glass in enumerate(found_glasses):

                # Если последний элемент — имя файла .png, добавляем кнопку вместо текста

                if glass.lower().endswith(".png") and index == len(found_glasses) - 1:

                    photo_name = glass  # Получаем имя фото

                    photo_callback_data = f"photo:{photo_name}"

                    photo_button = types.InlineKeyboardButton(

                        "Посмотреть фото стекла",

                        callback_data=photo_callback_data

                    )

                    keyboard.add(photo_button)

                else:

                    response += f"{glass}\n"

            # 👉 РЕКЛАМА ТОЛЬКО ТУТ
            response += AD_TEXT
            await bot.send_message(
                chat_id,
                response,
                reply_markup=keyboard,
                parse_mode='html'
            )

        else:
            await bot.send_message(
                chat_id,

                "<em><b>По Вашему запросу ничего не найдено!</b>\n"

                "1️⃣ Проверте ошибки при написании модели.\n"

                "2️⃣ Попробуйте ввести полное название модели. Пример: Realme Narzo 50i</em>\n\n",

                parse_mode='html'

            )

        @dp.callback_query_handler(lambda query: query.data.startswith('photo:'))
        async def process_photo_callback(callback_query: types.CallbackQuery):
            photo_name = callback_query.data.split(':')[-1]
            photo_path = f"photos1/{photo_name}"

            # Получаем текст запроса
            query_text = callback_query.message.text

            # Создаем сообщение с фото и результатами поиска
            if os.path.exists(photo_path):
                found_glasses = query_text.split('\n')[1:-1]  # Результаты поиска без первой и последней строки
                photo_caption = f"<b>Фото стекла:</b>\n"
                photo_caption += '\n'.join(found_glasses)

                await bot.send_photo(callback_query.from_user.id, open(photo_path, 'rb'), caption=photo_caption, parse_mode='html')



        if found_glasses2:
            response = f"<em><u>Взаимозаменяемые стекла по поиску 🔍<b>'{user_message}'</b> найдено:</u></em>\n"
            for index, glass in enumerate(found_glasses2):
                if glass.lower().endswith(".png") and index == len(found_glasses2) - 1:  # Если это фото и последний элемент
                    photo_name1 = glass  # Получаем имя фото
                    photo_callback_data = f"photo:{photo_name1}"
                    photo_button1 = types.InlineKeyboardButton("Посмотреть фото стекла", callback_data=photo_callback_data)
                    keyboard1.add(photo_button1)  # Добавляем кнопку в клавиатуру
                else:
                    response += f"{glass}\n"

            await bot.send_message(chat_id, response, reply_markup=keyboard1, parse_mode='html')


        @dp.callback_query_handler(lambda query: query.data.startswith('photo:'))
        async def process_photo_callback(callback_query: types.CallbackQuery):
            photo_name1 = callback_query.data.split(':')[-1]
            photo_path = f"photos1/{photo_name1}"

            # Получаем текст запроса
            query_text = callback_query.message.text

            # Создаем сообщение с фото и результатами поиска
            if os.path.exists(photo_path):
                found_glasses2 = query_text.split('\n')[1:-1]  # Результаты поиска без первой и последней строки
                photo_caption = f"<b>Фото стекла:</b>\n"
                photo_caption += '\n'.join(found_glasses2)

                await bot.send_photo(callback_query.from_user.id, open(photo_path, 'rb'), caption=photo_caption, parse_mode='html')



        if found_glasses3:
            response = f"<em><u>Взаимозаменяемые стекла по поиску 🔍<b>'{user_message}'</b> найдено:</u></em>\n"
            for index, glass in enumerate(found_glasses3):
                if glass.lower().endswith(".png") and index == len(found_glasses3) - 1:  # Если это фото и последний элемент
                    photo_name2 = glass  # Получаем имя фото
                    photo_callback_data = f"photo:{photo_name2}"
                    photo_button2 = types.InlineKeyboardButton("Посмотреть фото стекла", callback_data=photo_callback_data)
                    keyboard2.add(photo_button2)  # Добавляем кнопку в клавиатуру
                else:
                    response += f"{glass}\n"

            await bot.send_message(chat_id, response, reply_markup=keyboard2, parse_mode='html')

        @dp.callback_query_handler(lambda query: query.data.startswith('photo:'))
        async def process_photo_callback(callback_query: types.CallbackQuery):
            photo_name2 = callback_query.data.split(':')[-1]
            photo_path = f"photos1/{photo_name2}"

            # Получаем текст запроса
            query_text = callback_query.message.text

            # Создаем сообщение с фото и результатами поиска
            if os.path.exists(photo_path):
                found_glasses3 = query_text.split('\n')[1:-1]  # Результаты поиска без первой и последней строки
                photo_caption = f"<b>Фото стекла:</b>\n"
                photo_caption += '\n'.join(found_glasses3)

                await bot.send_photo(callback_query.from_user.id, open(photo_path, 'rb'), caption=photo_caption, parse_mode='html')


        if found_glasses4:
            response = f"<em><u>Взаимозаменяемые стекла по поиску 🔍<b>'{user_message}'</b> найдено:</u></em>\n"
            for index, glass in enumerate(found_glasses4):
                if glass.lower().endswith(".png") and index == len(found_glasses4) - 1:  # Если это фото и последний элемент
                    photo_name3 = glass  # Получаем имя фото
                    photo_callback_data = f"photo:{photo_name3}"
                    photo_button3 = types.InlineKeyboardButton("Посмотреть фото стекла", callback_data=photo_callback_data)
                    keyboard3.add(photo_button3)  # Добавляем кнопку в клавиатуру
                else:
                    response += f"{glass}\n"

            await bot.send_message(chat_id, response, reply_markup=keyboard3, parse_mode='html')

        @dp.callback_query_handler(lambda query: query.data.startswith('photo:'))
        async def process_photo_callback(callback_query: types.CallbackQuery):
            photo_name3 = callback_query.data.split(':')[-1]
            photo_path = f"photos/{photo_name3}"

            # Получаем текст запроса
            query_text = callback_query.message.text

            # Создаем сообщение с фото и результатами поиска
            if os.path.exists(photo_path):
                found_glasses4 = query_text.split('\n')[1:-1]  # Результаты поиска без первой и последней строки
                photo_caption = f"<b>Фото стекла:</b>\n"
                photo_caption += '\n'.join(found_glasses4)

                await bot.send_photo(callback_query.from_user.id, open(photo_path, 'rb'), caption=photo_caption, parse_mode='html')


        if found_glasses6:
            response = f"<em><u>Взаимозаменяемые стекла по поиску 🔍<b>'{user_message}'</b> найдено:</u></em>\n"
            for index, glass in enumerate(found_glasses6):
                if glass.lower().endswith(".png") and index == len(found_glasses6) - 1:  # Если это фото и последний элемент
                    photo_name4 = glass  # Получаем имя фото
                    photo_callback_data = f"photo:{photo_name4}"
                    photo_button4 = types.InlineKeyboardButton("Посмотреть фото стекла", callback_data=photo_callback_data)
                    keyboard4.add(photo_button4)  # Добавляем кнопку в клавиатуру
                else:
                    response += f"{glass}\n"

            await bot.send_message(chat_id, response, reply_markup=keyboard4, parse_mode='html')

        @dp.callback_query_handler(lambda query: query.data.startswith('photo:'))
        async def process_photo_callback(callback_query: types.CallbackQuery):
            photo_name4 = callback_query.data.split(':')[-1]
            photo_path = f"photos/{photo_name4}"

            # Получаем текст запроса
            query_text = callback_query.message.text

            # Создаем сообщение с фото и результатами поиска
            if os.path.exists(photo_path):
                found_glasses6 = query_text.split('\n')[1:-1]  # Результаты поиска без первой и последней строки
                photo_caption = f"<b>Фото стекла:</b>\n"
                photo_caption += '\n'.join(found_glasses6)

                await bot.send_photo(callback_query.from_user.id, open(photo_path, 'rb'), caption=photo_caption, parse_mode='html')







# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)





