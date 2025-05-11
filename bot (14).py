
# -*- coding: utf-8 -*-
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
    "Харківська область 🌳": "Харківська область 🌳"
}

class SellForm(StatesGroup):
    choosing_city = State()
    choosing_category = State()
    choosing_condition = State()

@dp.message_handler(commands="start", state="*")
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
    categories = ["Стіл Лофт", "Стіл ДСП", "Офісне крісло", "Стільці", "Шафи", "Тумби", "Стелажі", "Сейфи", "Інше"]
    for cat in categories:
        markup.insert(InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    markup.add(InlineKeyboardButton("✅ Завершити вибір", callback_data="cat_done"))

    await message.answer("Що хочете продати? Оберіть категорії:", reply_markup=markup)
    await SellForm.choosing_category.set()

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"), state=SellForm.choosing_category)
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "cat_done":
        await callback.message.edit_text("Оберіть стан меблів:")
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Гарний", "⚠️ Середній", "❌ Потребує ремонту")
        await callback.message.answer("Будь ласка, оберіть стан:", reply_markup=markup)
        await SellForm.choosing_condition.set()
    else:
        category = callback.data[4:]
        user_data[callback.from_user.id]["items"].append({"category": category})
        await callback.answer(f"Додано: {category}")

@dp.message_handler(state=SellForm.choosing_condition)
async def select_condition(message: types.Message, state: FSMContext):
    condition = message.text
    if condition not in ["✅ Гарний", "⚠️ Середній", "❌ Потребує ремонту"]:
        await message.answer("Будь ласка, оберіть варіант з кнопок.")
        return
    if user_data[message.from_user.id]["items"]:
        user_data[message.from_user.id]["items"][-1]["condition"] = condition
    await message.answer(f"Стан збережено: {condition}")
    await state.finish()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
