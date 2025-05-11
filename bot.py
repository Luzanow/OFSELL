
# -*- coding: utf-8 -*-
import logging
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

GROUP_ID = -1001234567890
ADMIN_ID = 123456789

dp = Dispatcher(bot, storage=MemoryStorage())

user_data = {}

city_options = {
    "Київ 🏙️": "Київ 🏙️",
    "Київська область 🌳": "Київська область 🌳",
    "Харків 🏙️": "Харків 🏙️",
    "Харківська область 🌳": "Харківська область 🌳",
    "Одеса 🌊": "Одеса 🌊",
    "Одеська область 🌳": "Одеська область 🌳",
    "Львів 🏞️": "Львів 🏞️",
    "Львівська область 🌳": "Львівська область 🌳",
    "Дніпро 🌆": "Дніпро 🌆",
    "Дніпропетровська область 🌳": "Дніпропетровська область 🌳"
}

class SellForm(StatesGroup):
    choosing_city = State()
    choosing_category = State()
    entering_description = State()
    entering_color = State()
    entering_quantity = State()
    uploading_photos = State()
    entering_price = State()
    entering_name = State()
    entering_phone = State()

# ... (додамо решту функцій далі)

@dp.message_handler(commands='start', state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    user_data[message.from_user.id] = {"items": []}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📍 Вибрати місто")
    await message.answer("Вітаю! Спершу оберіть місто:", reply_markup=markup)

@dp.message_handler(Text(equals="📍 Вибрати місто"))
async def choose_city(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city in city_options:
        markup.add(city)
    await message.answer("Оберіть місто або область:", reply_markup=markup)
    await SellForm.choosing_city.set()

@dp.message_handler(state=SellForm.choosing_city)
async def save_city(message: types.Message, state: FSMContext):
    city = message.text
    if city not in city_options:
        await message.answer("Будь ласка, оберіть місто з кнопок.")
        return
    user_data[message.from_user.id]["city"] = city
    markup = InlineKeyboardMarkup(row_width=2)
    for cat in ["Стіл", "Стілець", "Шафа", "Тумба", "Інше"]:
        markup.insert(InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    markup.add(InlineKeyboardButton("✅ Завершити вибір", callback_data="cat_done"))
    await message.answer("Що хочете продати? Оберіть категорії:", reply_markup=markup)
    await SellForm.choosing_category.set()

# (Далі буде продовження: опис, фото, кількість, ціна, підтвердження, надсилання заявки...)

