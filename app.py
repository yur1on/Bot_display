# app.py
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import json
import os
import sys
from pathlib import Path
import sqlite3

import config
from config import DB_PATH, ADMIN_ID, WEBAPP_URL  # DB_PATH должен быть Path или строкой
# если в config.py токен хранится в переменной tok, используем config.tok
TOK = getattr(config, "tok", None)
if not TOK:
    print("❌ BOT token not found in config.tok or BOT_TOKEN env. Set it.")
    # не завершаем, но бот не заработает без токена

# подключаем словари/данные
from baza import glass_data, glass_data2, glass_data3, glass_data4, glass_data5, glass_data6, glass_data7
from baza2 import glass_data9

# --- Проверка и открытие sqlite соединения (глобально) ---
# DB_PATH может быть Path или строка
DB_PATH = Path(DB_PATH)
print("🗄 DB_PATH:", DB_PATH)

if not DB_PATH.parent.exists():
    print("❌ Data directory does not exist:", DB_PATH.parent)
    sys.exit(1)

if not DB_PATH.exists():
    print("❌ Database file not found:", DB_PATH)
    print("   (Place your user_database.db into the data folder and restart.)")
    sys.exit(1)

try:
    # mode=rw — не создаст новую базу если её нет, и позволяет чтение-запись
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True, check_same_thread=False)
    cursor = conn.cursor()
    print("✅ Connected to SQLite DB (rw).")
except Exception as e:
    print("❌ Failed to open DB:", e)
    sys.exit(1)

# --- Инициализация бота и диспетчера ---
bot = Bot(TOK)
dp = Dispatcher(bot, storage=MemoryStorage())

# Если нужно — создаём таблицы только если их нет (на случай частичного дампа)
# Эти запросы безопасно выполнятся если таблицы уже существуют.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        name TEXT,
        city TEXT,
        phone_number TEXT
    )
''')

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

# ----------------- Вспомогательные функции -----------------

def is_user_blocked(user_id):
    cursor.execute('SELECT 1 FROM blocked_users WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None

def get_user_info(chat_id):
    cursor.execute("SELECT name, city, phone_number FROM users WHERE chat_id=?", (chat_id,))
    return cursor.fetchone()

def get_belarusian_chat_ids():
    cursor.execute("SELECT chat_id, city FROM users")
    users = cursor.fetchall()
    belarusian_chat_ids = [chat_id for chat_id, city in users if city and city.lower() in belarusian_cities]
    return belarusian_chat_ids

async def send_updates_to_all_users(bot_instance, message_text):
    chat_ids = get_belarusian_chat_ids()
    for chat_id in chat_ids:
        try:
            await bot_instance.send_message(chat_id, message_text)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")

def save_message_to_db(chat_id, text):
    try:
        cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, text))
        conn.commit()
    except Exception as e:
        print("Ошибка записи сообщения в БД:", e)

# ----------------- Данные -----------------
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
    "кобрин", "инск",
    "мин", "ошмяны",
    "слуцк", "житковичи",
    "rechitsa", "речица",
    "ошмяны", "novokuznetsk",
    "толочин", "микашевичи",
    "пружаны"
]

# ----------------- Хэндлеры / команды -----------------

@dp.message_handler(commands=['block'], user_id=ADMIN_ID)
async def block_user(message: types.Message):
    try:
        user_id_to_block = int(message.text.split()[1])
        cursor.execute('INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)', (user_id_to_block,))
        conn.commit()
        await message.reply(f"Пользователь с ID {user_id_to_block} заблокирован.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду в формате: /block <user_id>")

@dp.message_handler(commands=['unblock'], user_id=ADMIN_ID)
async def unblock_user_command(message: types.Message):
    try:
        user_id_to_unblock = int(message.text.split()[1])
        cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id_to_unblock,))
        conn.commit()
        await message.reply(f"Пользователь с ID {user_id_to_unblock} разблокирован.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду в формате: /unblock <user_id>")

@dp.message_handler(commands=['send'])
async def send_updates_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        message_text = ("Друзья! Представляем новый проект — mobirazbor.by :\n"
                        "платформа для разборщиков мобильной техники,\n"
                        "удобный сервис для учёта и поиска запчастей мобильной техники.\n"
                        "🔹Личный склад\n🔹Умный поиск по всей базе\n🔹Поддержка фото, описаний, отзывов и связи между пользователями\n"
                        "📢Присоединяйтесь к Telegram-каналу: t.me/MobiraRazbor\nСледите за развитием платформы и обновлениями.")
        await send_updates_to_all_users(bot, message_text)
        await message.answer("Сообщение отправлено всем зарегистрированным пользователям.")
    else:
        await message.answer("У вас нет прав для отправки сообщений.")

@dp.message_handler(commands=['send_to_user'])
async def send_to_user_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            message_text = ' '.join(message.text.split()[2:])
            await bot.send_message(user_id, message_text)
            await message.answer("Сообщение отправлено пользователю с ID: " + str(user_id))
        except (IndexError, ValueError):
            await message.answer("Неверный формат команды. Используйте /send_to_user <ID пользователя> <текст сообщения>")
    else:
        await message.answer("У вас нет прав для отправки сообщений.")

@dp.message_handler(commands=['delete_registration'])
async def delete_registration(message: types.Message):
    chat_id = message.chat.id
    cursor.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
    conn.commit()
    await bot.send_message(chat_id, "Ваши регистрационные данные успешно удалены. Для повторной регистрации используйте команду /registration")

async def create_menu_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    start_button = types.KeyboardButton('🚀 start')
    registration_button = types.KeyboardButton('🗂registration')
    help_button = types.KeyboardButton('ℹ️ Info')

    size_button = types.KeyboardButton(
        '🔎подбор стекла по размеру',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    )

    markup.add(start_button, registration_button, help_button)
    markup.add(size_button)
    return markup

@dp.message_handler(commands=['size'])
async def size_cmd(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔎 Открыть поиск по размерам", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    await message.answer("Нажмите кнопку, чтобы открыть форму:", reply_markup=kb)

# ----------------- Регистрация -----------------
class UserRegistration(StatesGroup):
    name = State()
    city = State()
    phone_number = State()

@dp.message_handler(state=UserRegistration.name)
async def register_name(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    name = message.text
    await state.update_data(name=name)
    await UserRegistration.city.set()
    await bot.send_message(chat_id, "Введите Ваш город:", reply_markup=await create_menu_button())

@dp.message_handler(lambda message: message.text.isdigit(), state=UserRegistration.city)
async def register_invalid_city(message: types.Message):
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

    try:
        cursor.execute("INSERT INTO users (chat_id, name, city, phone_number) VALUES (?, ?, ?, ?)",
                       (chat_id, name, city, phone_number))
        conn.commit()
    except Exception as e:
        print("Ошибка при вставке пользователя в БД:", e)
        await bot.send_message(chat_id, "Ошибка сохранения регистрационных данных. Попробуйте позже.")
        await state.finish()
        return

    await state.finish()
    await bot.send_message(chat_id, "Регистрация успешно завершена!\n\nВведите модель стекла телефона или планшета, которое вы ищите.\n\n Изучите информацию и откройте доп. кнопки 👉 /info")

@dp.message_handler(commands=['registration'])
async def start_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_info = get_user_info(chat_id)
    if user_info:
        user_name, user_city, user_phone = user_info
        await bot.send_message(chat_id, f"Вы зарегистрированы! \nВаше имя: {user_name}\nВаш город: {user_city}\nВаш № тел.: {user_phone}\n\nДля удаления регистрационных данных введите команду /delete_registration")
    else:
        await bot.send_message(chat_id, "Здравствуйте!\nВведите свое имя для регистрации:")
        await UserRegistration.name.set()

@dp.message_handler(lambda message: message.text == '🗂registration')
async def registration_button_handler(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    save_message_to_db(chat_id, message.text)
    user_info = get_user_info(chat_id)
    if user_info:
        user_name, user_city, user_phone = user_info
        await bot.send_message(chat_id, f"Вы зарегистрированы! \nВаше имя: {user_name}\nВаш город: {user_city}\nВаш № тел.: {user_phone}\n\nДля удаления регистрационных данных введите команду /delete_registration")
    else:
        await bot.send_message(chat_id, "Здравствуйте!\nВведите свое имя для регистрации:")
        await UserRegistration.name.set()

async def send_message_with_ad(chat_id, text, reply_markup=None, parse_mode='html'):
    ad_text = "\n\nmobirazbor.by"
    await bot.send_message(chat_id, text + ad_text, reply_markup=reply_markup, parse_mode=parse_mode)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    chat_id = message.chat.id
    save_message_to_db(chat_id, message.text)
    user_info = get_user_info(chat_id)
    if user_info:
        await send_message_with_ad(chat_id, f"Привет👋, @{message.from_user.username}!\n Введите модель стекла телефона или планшета, которое вы ищете.\n Изучите информацию и откройте доп. кнопки 👉 /info")
    else:
        await send_message_with_ad(chat_id, "Это бот для поиска взаимозаменяемых стекол для переклейки.\nДля пользования ботом, пожалуйста, зарегистрируйтесь! Используйте команду /registration")

@dp.message_handler(lambda message: message.text == '🚀 start')
async def start_button_handler(message: types.Message):
    chat_id = message.chat.id
    save_message_to_db(chat_id, message.text)
    user_info = get_user_info(chat_id)
    if user_info:
        await bot.send_message(chat_id, f"Привет👋, @{message.from_user.username}\n Введите модель стекла телефона или планшета, которое вы ищете.\n Изучите информацию и откройте доп. кнопки 👉 /info")
    else:
        await bot.send_message(chat_id, "Это бот для поиска взаимозаменяемых стекол для переклейки.\nДля пользования ботом, пожалуйста, зарегистрируйтесь! Используйте команду /registration")

@dp.message_handler(commands=['info'])
async def handle_info(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id,
                           "🤖 Я бот для поиска взаимозаменяемых моделей стекол телефонов и планшетов.\n\n"
                           "✔️Для поиска взаимозаменяемых стекол отправьте сообщения нужной модели\n\n"
                           "✔️Для подбора стекла по размерам используте команду /size\n\n"
                           "✔️/registration - команда для регистрации\n\n"
                           "✔️/delete_registration - команда для удаления своих регистрационных данных из базы\n\n"
                           "✔️Если нашли ошибку или знаете взаимозаменяемую модель стекла, напишите пожалуйста @expert_glass_lcd \n",
                           reply_markup=await create_menu_button())

@dp.message_handler(lambda message: message.text == 'ℹ️ Info')
async def info_button_handler(message: types.Message):
    chat_id = message.chat.id
    save_message_to_db(chat_id, message.text)
    await handle_info(message)

# ----------------- Поиск по размерам -----------------
class UserSizeSearch(StatesGroup):
    height = State()
    width = State()

@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def handle_size_webapp(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(chat_id, "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration")
        return

    try:
        data = json.loads(message.web_app_data.data)
        height = float(str(data.get("height", "")).replace(",", "."))
        width  = float(str(data.get("width", "")).replace(",", "."))
    except Exception:
        await bot.send_message(chat_id, "Некорректный формат. Введите длину и ширину числами (можно с запятой).")
        return

    found_glasses9 = perform_size_search(height, width)
    if found_glasses9:
        await bot.send_message(chat_id, f"<em><u>Стекла по размерам {height}x{width} найдено:</u></em>", parse_mode="HTML")
        for glass9 in found_glasses9:
            model = glass9["model"]
            photo_path = glass9.get("photo_path")
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, "rb") as photo:
                    await bot.send_photo(chat_id, photo, caption=f"<b>Модель:</b> {model}", parse_mode="HTML")
            else:
                await bot.send_message(chat_id, f"<b>Модель:</b> {model}", parse_mode="HTML")
    else:
        await bot.send_message(chat_id, "🔘По указанным размерам ничего не найдено!\n 🔘Побрубуйте увеличить или уменьшить размер в запросе на 0,5мм")

def perform_size_search(height, width):
    found_glasses9 = []
    for glass9 in glass_data9:
        if glass9.get("height") == height and glass9.get("width") == width:
            found_glasses9.append({
                "model": glass9.get('model'),
                "photo_path": glass9.get('photo_path', None)
            })
    return found_glasses9

# ----------------- Основной текстовый обработчик -----------------

@dp.message_handler()
async def handle_text(message, state: FSMContext):
    user_message = message.text
    if not user_message:
        return

    user_message_lower = user_message.lower()
    chat_id = message.chat.id

    save_message_to_db(chat_id, user_message_lower)

    user_id = message.from_user.id
    if is_user_blocked(user_id):
        await message.reply("Вы заблокированы и не можете использовать этого бота.")
        return

    # простая валидация/подсказки
    if 'galaxy' in user_message_lower:
        await bot.send_message(chat_id, "Повторите пожалуйста запрос не используя слово <b>galaxy</b>.", parse_mode='html')
        return
    # исправления опечаток
    if 'realmi' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>realmi</u> на правильное написание <b>realme</b>.", parse_mode='html')
        return
    if 'techno' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>techno</u> на правильное написание <b>tecno</b>.", parse_mode='html')
        return
    if '+' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе знак <u>+</u> на слово <b>plus</b>.", parse_mode='html')
        return

    forbidden_words = ['хонор', 'самсунг', 'редми', 'реалми', 'хуавей', 'техно', 'виво', 'ксиаоми', 'инфиникс', 'айфон', 'асус', 'сони']
    if any(word in user_message_lower for word in forbidden_words):
        await bot.send_message(chat_id, "Пожалуйста пишите модель на английском языке")
        return

    # проверяем регистрацию
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(chat_id, "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration ")
        return

    # поиск по словарям (как было)
    found_glasses = []
    found_glasses2 = []
    found_glasses3 = []
    found_glasses4 = []
    found_glasses5 = []
    found_glasses6 = []
    found_glasses7 = []

    for model, glasses in glass_data:
        if user_message_lower == model.lower():
            found_glasses = glasses
            break

    for model, glasses in glass_data2:
        if user_message_lower == model.lower():
            found_glasses2 = glasses
            break

    for model, glasses in glass_data3:
        if user_message_lower == model.lower():
            found_glasses3 = glasses
            break

    for model, glasses in glass_data4:
        if user_message_lower == model.lower():
            found_glasses4 = glasses
            break

    for model, glasses in glass_data5:
        if user_message_lower == model.lower():
            found_glasses5 = glasses
            break

    for model, glasses in glass_data6:
        if user_message_lower == model.lower():
            found_glasses6 = glasses
            break

    for model, glasses in glass_data7:
        if user_message_lower == model.lower():
            found_glasses7 = glasses
            break

    AD_TEXT = (
        '\n\n<b>Для жителей РБ 🇧🇾</b>\n'
        'Сервис для разборщиков мобильной техники.\n'
        'Канал: <a href="https://t.me/MobiraRazbor">@MobiraRazbor</a>\n'
        'Чат: <a href="https://t.me/mobirazbor_chat">@mobirazbor_chat</a>\n'
        'Сайт: <a href="https://mobirazbor.by">mobirazbor.by</a>'
    )

    # ответы
    if found_glasses5:
        response = f"<em>Я знаю многое о продукции<b> {user_message}</b>. Укажите конкретную модель!</em>\n"
        response += "\n".join(found_glasses5)
        await bot.send_message(chat_id, response, parse_mode='html')
        return
    if found_glasses7:
        response = f"<em>Уточните, какая именно модель<b> {user_message}</b> Вас интересует?</em>\n"
        response += "\n".join(found_glasses7)
        await bot.send_message(chat_id, response, parse_mode='html')
        return

    # Формируем клавиатуры и сообщения для найденных списков
    def send_found_list(chat, found_list):
        keyboard = types.InlineKeyboardMarkup()
        response = f"<em><u>Взаимозаменяемые стекла по поиску 🔍<b>'{user_message}'</b> найдено:</u></em>\n"
        for index, glass in enumerate(found_list):
            if isinstance(glass, str) and glass.lower().endswith(".png") and index == len(found_list) - 1:
                photo_name = glass
                photo_callback_data = f"photo:{photo_name}"
                photo_button = types.InlineKeyboardButton("Посмотреть фото стекла", callback_data=photo_callback_data)
                keyboard.add(photo_button)
            else:
                response += f"{glass}\n"
        response += AD_TEXT
        return response, keyboard

    handled = False
    if found_glasses:
        resp, kb = send_found_list(chat_id, found_glasses)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        handled = True
    if found_glasses2:
        resp, kb = send_found_list(chat_id, found_glasses2)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        handled = True
    if found_glasses3:
        resp, kb = send_found_list(chat_id, found_glasses3)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        handled = True
    if found_glasses4:
        resp, kb = send_found_list(chat_id, found_glasses4)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        handled = True
    if found_glasses6:
        resp, kb = send_found_list(chat_id, found_glasses6)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        handled = True

    if not handled:
        kb_size = types.InlineKeyboardMarkup()
        kb_size.add(types.InlineKeyboardButton("🔎 Подобрать стекло по размерам", web_app=types.WebAppInfo(url=WEBAPP_URL)))
        await bot.send_message(chat_id,
                               "<em><b>По Вашему запросу ничего не найдено!</b>\n"
                               "1️⃣ Проверьте ошибки при написании модели.\n"
                               "2️⃣ Попробуйте ввести полное название модели. Пример: Realme Narzo 50i\n"
                               "3️⃣ Или подберите стекло по размерам (длина × ширина) — нажмите кнопку ниже.</em>\n",
                               parse_mode='html',
                               reply_markup=kb_size)

# единый callback handler для фото (обрабатывает все photo:... callback_data)
@dp.callback_query_handler(lambda query: query.data and query.data.startswith('photo:'))
async def process_photo_callback(callback_query: types.CallbackQuery):
    photo_name = callback_query.data.split(':', 1)[1]
    # разные папки в проекте — пробуем несколько вариантов
    possible_paths = [f"photos1/{photo_name}", f"photos/{photo_name}", photo_name]
    photo_path = None
    for p in possible_paths:
        if os.path.exists(p):
            photo_path = p
            break
    query_text = callback_query.message.text or ""
    if photo_path:
        found_lines = query_text.split('\n')[1:-1] if '\n' in query_text else []
        photo_caption = "<b>Фото стекла:</b>\n" + "\n".join(found_lines)
        await bot.send_photo(callback_query.from_user.id, open(photo_path, 'rb'), caption=photo_caption, parse_mode='html')
    else:
        await bot.send_message(callback_query.from_user.id, "Фото не найдено.")

# ----------------- Запуск -----------------
if __name__ == '__main__':
    print("🚀 Bot starting...")
    try:
        executor.start_polling(dp, skip_updates=False)
    finally:
        try:
            conn.close()
            print("🗄 DB connection closed.")
        except:
            pass
