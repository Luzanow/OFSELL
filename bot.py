import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

class Form(StatesGroup):
    city = State()
    category = State()
    photo = State()
    description = State()
    condition = State()
    phone = State()

city_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🏙️ Київ"), KeyboardButton("🌳 Київська область"),
    KeyboardButton("🏢 Харків"), KeyboardButton("🌾 Харківська область"),
    KeyboardButton("🏗️ Дніпро"), KeyboardButton("🏞️ Дніпропетровська область"),
    KeyboardButton("🏰 Львів"), KeyboardButton("⛰️ Львівська область"),
    KeyboardButton("🌊 Одеса"), KeyboardButton("🌅 Одеська область"),
    KeyboardButton("🏭 Запоріжжя"), KeyboardButton("🌋 Запорізька область"),
    KeyboardButton("🏞️ Івано-Франківськ"), KeyboardButton("🌄 Івано-Франківська область"),
    KeyboardButton("🏡 Вінниця"), KeyboardButton("🌻 Вінницька область"),
    KeyboardButton("📍 Інше")
)

category_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🏢 Столи"),
    KeyboardButton("🪑 Стільці"),
    KeyboardButton("💺 Крісла"),
    KeyboardButton("🗄️ Шафи / Тумби / Комоди"),
    KeyboardButton("🛋️ Дивани / М’які меблі"),
    KeyboardButton("📦 Стелажі"),
    KeyboardButton("🔐 Сейфи"),
    KeyboardButton("🖥️ Офісна техніка"),
    KeyboardButton("🛒 Кухонна техніка"),
    KeyboardButton("🧾 Інше")
)

condition_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("✅ Ідеальний"),
    KeyboardButton("👍 Гарний"),
    KeyboardButton("⚠️ Задовільний"),
    KeyboardButton("❌ Потребує ремонту")
)

phone_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("📱 Поділитися номером", request_contact=True)
)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Обери місто або область:", reply_markup=city_keyboard)
    await Form.city.set()

@dp.message_handler(state=Form.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Що саме продаєш?", reply_markup=category_keyboard)
    await Form.category.set()

@dp.message_handler(state=Form.category)
async def get_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Надішли фото меблів:")
    await Form.photo.set()

@dp.message_handler(content_types=['photo'], state=Form.photo)
async def get_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer("Введи короткий опис (наприклад: стан, кількість):")
    await Form.description.set()

@dp.message_handler(state=Form.description)
async def get_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Обери стан меблів:", reply_markup=condition_keyboard)
    await Form.condition.set()

@dp.message_handler(state=Form.condition)
async def get_condition(message: types.Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Залиш свій номер телефону:", reply_markup=phone_keyboard)
    await Form.phone.set()

@dp.message_handler(content_types=['contact', 'text'], state=Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone = message.contact.phone_number if message.contact else message.text

    text_group = f"""
📍 <b>Місто:</b> {user_data['city']}
📦 <b>Категорія:</b> {user_data['category']}
📝 <b>Опис:</b> {user_data['description']}
🔧 <b>Стан:</b> {user_data['condition']}
📞 <b>Контакт:</b> @{message.from_user.username if message.from_user.username else 'номер вручну'}
"""

    text_owner = f"""
Нова заявка!

Імʼя: @{message.from_user.username}
Телефон: {phone}
Місто: {user_data['city']}
Категорія: {user_data['category']}
Опис: {user_data['description']}
Стан: {user_data['condition']}
"""

    photo_id = user_data['photo']
    await bot.send_photo(GROUP_ID, photo_id, caption=text_group)
    await bot.send_photo(OWNER_ID, photo_id, caption=text_owner)

    await message.answer("✅ Дякуємо! Заявку надіслано.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
