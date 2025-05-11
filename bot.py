
# -*- coding: utf-8 -*-
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
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
    choosing_condition = State()
    entering_quantity = State()
    uploading_photos = State()
    entering_price = State()
    confirming = State()

@dp.message_handler(commands="start", state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    user_data[message.from_user.id] = {"items": [], "current_item": {}}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📍 Вибрати місто")
    await message.answer("Привіт! Оберіть місто для заявки:", reply_markup=markup)

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
        await message.answer("Оберіть, будь ласка, з кнопок.")
        return
    user_data[message.from_user.id]["city"] = city
    markup = InlineKeyboardMarkup(row_width=2)
    categories = ["Стіл Лофт", "Стіл ДСП", "Офісне крісло", "Стільці", "Шафи", "Тумби", "Стелажі", "Сейфи", "Інше"]
    for cat in categories:
        markup.insert(InlineKeyboardButton(f"⬜ {cat}", callback_data=f"cat_{cat}"))
    markup.add(InlineKeyboardButton("✅ Завершити вибір", callback_data="cat_done"))
    await message.answer("Що хочете продати? Оберіть категорії:", reply_markup=markup)
    user_data[message.from_user.id]["selected_categories"] = []
    await SellForm.choosing_category.set()

# Друга частина з описом, кольором, станом, кількістю, фото, ціною, редагуванням...

# Після всіх даних — підтвердження заявки
@dp.message_handler(commands="done", state="*")
async def confirm_final(message: types.Message, state: FSMContext):
    data = user_data.get(message.from_user.id)
    if not data or not data.get("items"):
        await message.answer("Немає даних для заявки.")
        return

    caption = "<b>Заявка на викуп меблів</b>\n\n"
    for i, item in enumerate(data["items"], 1):
        caption += f"<b>{i}. {item['category']}</b>\n"
        caption += f"Опис: {item['description']}\n"
        caption += f"Колір: {item['color']}\n"
        caption += f"Стан: {item['condition']}\n"
        caption += f"Кількість: {item['quantity']} шт.\n"
        if item.get("price"):
            caption += f"Ціна: {item['price']}\n"
        caption += "\n"

    caption += f"Місто: {data['city']}"

    media_group = []
    for item in data["items"]:
        for p in item.get("photos", []):
            media_group.append(InputMediaPhoto(media=p))

    # Надсилання в групу
    if media_group:
        await bot.send_media_group(chat_id=GROUP_ID, media=media_group)

    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🛒 Купити", url=f"https://t.me/{(await bot.get_me()).username}"))
    await bot.send_message(chat_id=GROUP_ID, text=caption, reply_markup=keyboard)

    # Надсилання адміну
    await bot.send_message(chat_id=ADMIN_ID, text="Заявка на викуп отримана:")
    await bot.send_message(chat_id=ADMIN_ID, text=caption)

    await message.answer("✅ Заявку надіслано!")
    await state.finish()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
