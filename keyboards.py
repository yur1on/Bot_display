from aiogram import types

async def create_help_submenu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    hello_button = types.KeyboardButton('🆘 Связь с поддержкой')
    goodbye_button = types.KeyboardButton('🆘 Помощь по навигации')
    markup.add(hello_button, goodbye_button)
    return markup

async def create_menu_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    start_button = types.KeyboardButton('🚀 start')
    registration_button = types.KeyboardButton('🗂registration')
    help_button = types.KeyboardButton('ℹ️ Info')
    size_search_button = types.KeyboardButton('🔎подбор стекла по размеру')
    markup.add(start_button, registration_button, help_button, size_search_button)
    return markup

async def create_back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    back_button = types.KeyboardButton('✏️ Исправить')
    markup.add(back_button)
    return markup



