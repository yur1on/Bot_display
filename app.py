# app.py
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, RetryAfter, UserDeactivated

import asyncio
import re
import json
import os
import sys
from pathlib import Path
import sqlite3
import traceback

import config
from config import DB_PATH, ADMIN_ID, WEBAPP_URL

# токен в config.tok (или config.BOT_TOKEN)
TOK = getattr(config, "tok", None)
if not TOK:
    print("❌ BOT token not found in config.tok. Set it and restart.")
    sys.exit(1)

# импорт данных
from baza import (
    glass_data, glass_data2, glass_data3, glass_data4,
    glass_data5, glass_data6, glass_data7
)
from baza2 import glass_data9

# --- Проверка и открытие sqlite соединения (глобально) ---
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
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True, check_same_thread=False)
    cursor = conn.cursor()
    print("✅ Connected to SQLite DB (rw).")
except Exception as e:
    print("❌ Failed to open DB:", e)
    traceback.print_exc()
    sys.exit(1)

# --- Инициализация бота и диспетчера ---
bot = Bot(TOK)
dp = Dispatcher(bot, storage=MemoryStorage())

# создаём таблицы при отсутствии
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER UNIQUE,
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

# ✅ Аналитика по поиску размеров
cursor.execute('''
    CREATE TABLE IF NOT EXISTS size_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        height REAL,
        width REAL,
        found_count INTEGER,
        source TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    # старая функция: отправляет только пользователям из РБ (по списку городов)
    chat_ids = get_belarusian_chat_ids()
    for chat_id in chat_ids:
        try:
            await bot_instance.send_message(chat_id, message_text)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")


# ✅ НОВОЕ: все зарегистрированные пользователи
def get_all_chat_ids():
    cursor.execute("SELECT chat_id FROM users")
    rows = cursor.fetchall()
    return [r[0] for r in rows if r and r[0]]


# ✅ НОВОЕ: рассылка всем с антифлудом и обработкой ошибок
async def send_to_all_users(bot_instance, message_text: str):
    chat_ids = get_all_chat_ids()
    ok = 0
    fail = 0

    for chat_id in chat_ids:
        try:
            await bot_instance.send_message(chat_id, message_text)
            ok += 1
            await asyncio.sleep(0.05)  # антифлуд
        except RetryAfter as e:
            await asyncio.sleep(e.timeout)
            try:
                await bot_instance.send_message(chat_id, message_text)
                ok += 1
            except Exception as e2:
                print(f"❌ send fail after RetryAfter to {chat_id}: {e2}")
                fail += 1
        except (BotBlocked, ChatNotFound, UserDeactivated) as e:
            print(f"⚠️ unreachable {chat_id}: {e}")
            fail += 1
        except Exception as e:
            print(f"❌ send error to {chat_id}: {e}")
            fail += 1

    return ok, fail


def save_message_to_db(chat_id, text):
    try:
        cursor.execute("INSERT INTO messages (chat_id, message_text) VALUES (?, ?)", (chat_id, text))
        conn.commit()
    except Exception as e:
        print("Ошибка записи сообщения в БД:", e)


# ✅ Запись аналитики по поиску размеров
def save_size_search_to_db(chat_id, height, width, found_count, source="unknown"):
    try:
        cursor.execute(
            "INSERT INTO size_searches (chat_id, height, width, found_count, source) VALUES (?, ?, ?, ?, ?)",
            (int(chat_id), float(height), float(width), int(found_count), str(source))
        )
        conn.commit()
    except Exception as e:
        print("Ошибка записи size_searches в БД:", e)


def add_src(url: str, src: str) -> str:
    # необязательно, но полезно для аналитики (menu/cmd)
    return f"{url}&src={src}" if "?" in url else f"{url}?src={src}"

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
]

# Реклама (будем отправлять ОДИН раз после всех блоков результатов)
# AD_TEXT = (
#     '<b>Для жителей РБ 🇧🇾</b>\n'
#     'Сервис для разборщиков мобильной техники.\n'
#     'Канал: <a href="https://t.me/MobiraRazbor">@MobiraRazbor</a>\n'
#     'Чат: <a href="https://t.me/mobirazbor_chat">@mobirazbor_chat</a>\n'
#     'Сайт: <a href="https://mobirazbor.by">mobirazbor.by</a>'
# )
AD_TEXT = (
    '<b>Для поиска взаимозаменяемых защитных стёкол:</b>\n'
    'Бот: <a href="https://t.me/safety_display_bot">@safety_display_bot</a>\n\n'
    'Чат: <a href="https://t.me/+yJDx_G2b0hNjNTBi">@tehnosfera_chat</a>\n'
    'Канал: <a href="https://t.me/+ze8-aO_YZ-Q0ZGEy">@tehnosfera_info</a>'
)

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
    # старая команда (по РБ)
    if message.from_user.id == ADMIN_ID:
        message_text = ("Друзья! Представляем новый проект — mobirazbor.by :\n"
                        "платформа для разборщиков мобильной техники,\n"
                        "удобный сервис для учёта и поиска запчастей мобильной техники.\n"
                        "🔹Личный склад\n🔹Умный поиск по всей базе\n🔹Поддержка фото, описаний, отзывов и связи между пользователями\n")
        await send_updates_to_all_users(bot, message_text)
        await message.answer("Сообщение отправлено пользователям из РБ (по городам).")
    else:
        await message.answer("У вас нет прав для отправки сообщений.")


# ✅ НОВОЕ: /send1 всем зарегистрированным
@dp.message_handler(commands=['send1'])
async def send1_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("У вас нет прав для отправки сообщений.")

    text = (
        "Автоматический поиск нужных сообщений в Telegram\n\n"
        "Больше не нужно вручную читать чаты.\n\n"
        "1️⃣ Добавляешь ключевые слова\n"
        "2️⃣ Подключаешь чаты\n"
        "3️⃣ Бот сам находит сообщения и отправляет тебе\n\n"
        "Без спама. Без лишнего.\n\n"
        "Подходит для:\n"
        "— продавцов запчастей\n"
        "— перекупов техники\n"
        "— мастеров по ремонту\n\n"
        "👉 @PhraseAlert24Bot"
    )

    ok, fail = await send_to_all_users(bot, text)

    await message.answer(
        f"✅ Рассылка завершена.\n"
        f"Отправлено: {ok}\n"
        f"Ошибок: {fail}"
    )

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


# ----------------- Меню -----------------
async def create_menu_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    start_button = types.KeyboardButton('🚀 start')
    registration_button = types.KeyboardButton('🗂registration')
    help_button = types.KeyboardButton('ℹ️ Info')

    # ✅ src=menu (если ваш index.html отправляет src обратно в sendData)
    size_button = types.KeyboardButton(
        '🔎подбор стекла по размеру',
        web_app=types.WebAppInfo(url=add_src(WEBAPP_URL, "menu"))
    )

    markup.add(start_button, registration_button, help_button)
    markup.add(size_button)
    return markup


# ----------------- /size: открыть форму и НЕ потерять меню -----------------
@dp.message_handler(commands=['size'])
async def size_cmd(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(
        types.KeyboardButton(
            "🔎подбор стекла по размеру",
            web_app=types.WebAppInfo(url=add_src(WEBAPP_URL, "cmd"))  # ✅ src=cmd
        )
    )
    kb.add(types.KeyboardButton("↩️ В меню"))

    await message.answer(
        "🔎 <b>Подбор стекла по размерам</b>\n\n"
        "Нажмите кнопку 👇 «🔎подбор стекла по размеру».\n\n"
        "Если передумали — нажмите «↩️ В меню».",
        parse_mode="html",
        reply_markup=kb
    )


@dp.message_handler(lambda m: m.text == "↩️ В меню")
async def back_to_menu(message: types.Message):
    await message.answer("Меню:", reply_markup=await create_menu_button())


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
        cursor.execute(
            "INSERT OR REPLACE INTO users (chat_id, name, city, phone_number) VALUES (?, ?, ?, ?)",
            (chat_id, name, city, phone_number)
        )
        conn.commit()
    except Exception as e:
        print("Ошибка при вставке пользователя в БД:", e)
        await bot.send_message(chat_id, "Ошибка сохранения регистрационных данных. Попробуйте позже.")
        await state.finish()
        return

    await state.finish()
    await bot.send_message(
        chat_id,
        "Регистрация успешно завершена!\n\nВведите модель стекла телефона или планшета, которое вы ищите.\n\n Изучите информацию и откройте доп. кнопки 👉 /info"
    )


@dp.message_handler(commands=['registration'])
async def start_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_info = get_user_info(chat_id)
    if user_info:
        user_name, user_city, user_phone = user_info
        await bot.send_message(
            chat_id,
            f"Вы зарегистрированы! \nВаше имя: {user_name}\nВаш город: {user_city}\nВаш № тел.: {user_phone}\n\nДля удаления регистрационных данных введите команду /delete_registration"
        )
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
        await bot.send_message(
            chat_id,
            f"Вы зарегистрированы! \nВаше имя: {user_name}\nВаш город: {user_city}\nВаш № тел.: {user_phone}\n\nДля удаления регистрационных данных введите команду /delete_registration"
        )
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
async def start_button_handler(message: types.Message):
    chat_id = message.chat.id
    save_message_to_db(chat_id, message.text)
    user_info = get_user_info(chat_id)
    if user_info:
        await bot.send_message(
            chat_id,
            f"Привет👋, @{message.from_user.username}\n Введите модель стекла телефона или планшета, которое вы ищете.\n Изучите информацию и откройте доп. кнопки 👉 /info"
        )
    else:
        await bot.send_message(
            chat_id,
            "Это бот для поиска взаимозаменяемых стекол для переклейки.\nДля пользования ботом, пожалуйста, зарегистрируйтесь! Используйте команду /registration"
        )


@dp.message_handler(commands=['info'])
async def handle_info(message: types.Message):
    chat_id = message.chat.id
    await bot.send_message(
        chat_id,
        "🤖 Я бот для поиска взаимозаменяемых моделей стекол телефонов и планшетов.\n\n"
        "✔️Для поиска взаимозаменяемых стекол отправьте сообщение нужной модели\n\n"
        "✔️Для подбора стекла по размерам: кнопка «🔎подбор стекла по размеру» или команда /size\n\n"
        "✔️/registration - команда для регистрации\n\n"
        "✔️/delete_registration - команда для удаления своих регистрационных данных из базы\n\n"
        "✔️Если нашли ошибку или знаете взаимозаменяемую модель стекла, напишите пожалуйста @expert_glass_lcd \n",
        reply_markup=await create_menu_button()
    )


@dp.message_handler(lambda message: message.text == 'ℹ️ Info')
async def info_button_handler(message: types.Message):
    chat_id = message.chat.id
    save_message_to_db(chat_id, message.text)
    await handle_info(message)

# ----------------- Поиск по размерам (WebApp) -----------------

@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def handle_size_webapp(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(
            chat_id,
            "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration",
            reply_markup=await create_menu_button()
        )
        return

    try:
        data = json.loads(message.web_app_data.data)
        height = float(str(data.get("height", "")).replace(",", "."))
        width = float(str(data.get("width", "")).replace(",", "."))
        source = str(data.get("src", "unknown"))
    except Exception:
        await bot.send_message(
            chat_id,
            "Некорректный формат. Введите длину и ширину числами (можно с запятой).",
            reply_markup=await create_menu_button()
        )
        return

    found_glasses9 = perform_size_search(height, width)

    # ✅ Аналитика: пишем каждый поиск по размерам
    save_size_search_to_db(chat_id, height, width, len(found_glasses9), source)

    if found_glasses9:
        await bot.send_message(
            chat_id,
            f"<em><u>Стекла по размерам {height}x{width} найдено:</u></em>",
            parse_mode="HTML"
        )
        for glass9 in found_glasses9:
            model = glass9.get("model")
            photo_path = glass9.get("photo_path")
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id,
                        photo,
                        caption=f"<b>Модель:</b> {model}",
                        parse_mode="HTML"
                    )
            else:
                await bot.send_message(chat_id, f"<b>Модель:</b> {model}", parse_mode="HTML")
    else:
        await bot.send_message(
            chat_id,
            "🔘По указанным размерам ничего не найдено!\n"
            "🔘Попробуйте увеличить или уменьшить размер в запросе на 0,5мм"
        )

    # ✅ ВОЗВРАЩАЕМ ОСНОВНОЕ МЕНЮ
    await bot.send_message(chat_id, "Меню:", reply_markup=await create_menu_button())


def perform_size_search(height, width):
    found_glasses9 = []
    for glass9 in glass_data9:
        try:
            if float(glass9.get("height")) == float(height) and float(glass9.get("width")) == float(width):
                found_glasses9.append({
                    "model": glass9.get('model'),
                    "photo_path": glass9.get('photo_path', None)
                })
        except Exception:
            continue
    return found_glasses9

# ----------------- Основной текстовый обработчик -----------------

@dp.message_handler()
async def handle_text(message: types.Message, state: FSMContext):
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
    if 'realmi' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>realmi</u> на правильное написание <b>realme</b>.", parse_mode='html')
        return
    if 'techno' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>techno</u> на правильное написание <b>tecno</b>.", parse_mode='html')
        return
    if 'tehno' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе слово <u>tehno</u> на правильное написание <b>tecno</b>.", parse_mode='html')
        return
    if '+' in user_message_lower:
        await bot.send_message(chat_id, "❗️Исправте в запросе знак <u>+</u> на слово <b>plus</b>.", parse_mode='html')
        return

    # ✅ если написали на русском — просим на английском
    if re.search(r"[а-яё]", user_message_lower):
        await bot.send_message(chat_id, "Пожалуйста, пишите модель на <b>английском</b> языке.", parse_mode="html")
        return

    # проверяем регистрацию
    user_info = get_user_info(chat_id)
    if not user_info:
        await bot.send_message(chat_id, "Для пользования ботом пожалуйста зарегистрируйтесь! \nИспользуйте команду 👉  /registration ")
        return

    # поиск по словарям
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

    # ✅ тут больше НЕ добавляем рекламу в каждый блок
    def build_found_block(found_list):
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
        return response, keyboard

    sent_any_results = False

    if found_glasses:
        resp, kb = build_found_block(found_glasses)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        sent_any_results = True

    if found_glasses2:
        resp, kb = build_found_block(found_glasses2)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        sent_any_results = True

    if found_glasses3:
        resp, kb = build_found_block(found_glasses3)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        sent_any_results = True

    if found_glasses4:
        resp, kb = build_found_block(found_glasses4)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        sent_any_results = True

    if found_glasses6:
        resp, kb = build_found_block(found_glasses6)
        await bot.send_message(chat_id, resp, reply_markup=kb, parse_mode='html')
        sent_any_results = True

    # ✅ реклама ОДИН раз — только если были результаты
    if sent_any_results:
        await bot.send_message(chat_id, "\n" + AD_TEXT, parse_mode="html", disable_web_page_preview=True)
        return

    # если вообще ничего не найдено
    await bot.send_message(
        chat_id,
        "<em><b>По Вашему запросу ничего не найдено!</b>\n\n"
        "1️⃣ Проверьте ошибки при написании модели.\n"
        "2️⃣ Попробуйте ввести полное название модели.\n\n"
        "🔎 <b>Вы можете подобрать стекло по размерам</b>\n"
        "👇 <b>нажмите кнопку внизу меню</b>\n"
        "«🔎подбор стекла по размеру»\n"
        "или команда /size</em>",
        parse_mode="html",
        reply_markup=await create_menu_button()
    )


@dp.callback_query_handler(lambda query: query.data and query.data.startswith('photo:'))
async def process_photo_callback(callback_query: types.CallbackQuery):
    photo_name = callback_query.data.split(':', 1)[1]
    possible_paths = [f"photos1/{photo_name}", f"photos/{photo_name}", photo_name]
    photo_path = None
    for p in possible_paths:
        if os.path.exists(p):
            photo_path = p
            break

    query_text = callback_query.message.text or ""

    if photo_path:
        lines = [ln.strip() for ln in query_text.splitlines()]
        found_lines = [ln for ln in lines[1:] if ln]  # всё после заголовка, без пустых
        photo_caption = "<b>Фото стекла:</b>\n" + "\n".join(found_lines) if found_lines else "<b>Фото стекла</b>"

        await bot.send_photo(
            callback_query.from_user.id,
            open(photo_path, 'rb'),
            caption=photo_caption,
            parse_mode='html'
        )
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
