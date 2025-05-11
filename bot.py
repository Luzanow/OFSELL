
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text

API_TOKEN = "YOUR_BOT_TOKEN"
GROUP_ID = -1001234567890  # заміни на ID твоєї групи
ADMIN_ID = 123456789  # заміни на твій Telegram ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

user_data = {}

class SellForm(StatesGroup):
    choosing_city = State()
    choosing_category = State()
    entering_description = State()
    entering_color = State()
    entering_quantity = State()
    uploading_photos = State()
    entering_name = State()
    entering_phone = State()
    confirm_submission = State()

@dp.message_handler(commands='start', state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    user_data[message.from_user.id] = {"items": []}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📍 Вибрати місто")
    await message.answer("Вітаю! Спершу оберіть місто:", reply_markup=markup)

@dp.message_handler(Text(equals="📍 Вибрати місто"))
async def choose_city(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Київ", "Київська область")
    markup.add("Харків", "Харківська область")
    markup.add("Львів", "Львівська область")
    markup.add("Одеса", "Одеська область")
    markup.add("Дніпро", "Дніпропетровська область")
    await message.answer("Оберіть місто або область:", reply_markup=markup)
    await SellForm.choosing_city.set()

@dp.message_handler(state=SellForm.choosing_city)
async def save_city(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["city"] = message.text
    markup = InlineKeyboardMarkup(row_width=2)
    for cat in ["Стіл", "Стілець", "Шафа", "Тумба", "Інше"]:
        markup.insert(InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    markup.add(InlineKeyboardButton("✅ Завершити вибір", callback_data="cat_done"))
    await message.answer("Що хочете продати? Оберіть категорії:", reply_markup=markup)
    await SellForm.choosing_category.set()

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"), state=SellForm.choosing_category)
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "cat_done":
        await callback.message.edit_text("Введіть опис першої позиції:")
        await SellForm.entering_description.set()
    else:
        cat = callback.data[4:]
        user_data[callback.from_user.id]["items"].append({
            "category": cat,
            "description": "",
            "color": "",
            "quantity": 1,
            "photos": []
        })
        await callback.answer(f"Додано: {cat}")

@dp.message_handler(state=SellForm.entering_description)
async def enter_description(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["items"][-1]["description"] = message.text
    markup = InlineKeyboardMarkup(row_width=2)
    for color in ["Червоний", "Синій", "Зелений", "Білий", "Чорний", "Інше"]:
        markup.insert(InlineKeyboardButton(color, callback_data=f"color_{color}"))
    await message.answer("Оберіть колір:", reply_markup=markup)
    await SellForm.entering_color.set()

@dp.callback_query_handler(lambda c: c.data.startswith("color_"), state=SellForm.entering_color)
async def choose_color(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data[6:]
    user_data[callback.from_user.id]["items"][-1]["color"] = color
    user_data[callback.from_user.id]["items"][-1]["quantity"] = 1
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("➖", callback_data="qty_minus"),
        InlineKeyboardButton("1", callback_data="qty_val"),
        InlineKeyboardButton("➕", callback_data="qty_plus")
    ).add(InlineKeyboardButton("➡️ Далі", callback_data="to_photos"))
    await callback.message.answer("Вкажіть кількість:", reply_markup=markup)
    await SellForm.entering_quantity.set()

@dp.callback_query_handler(lambda c: c.data.startswith("qty_"), state=SellForm.entering_quantity)
async def handle_quantity(callback: types.CallbackQuery, state: FSMContext):
    item = user_data[callback.from_user.id]["items"][-1]
    if callback.data == "qty_plus":
        item["quantity"] += 1
    elif callback.data == "qty_minus" and item["quantity"] > 1:
        item["quantity"] -= 1
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("➖", callback_data="qty_minus"),
        InlineKeyboardButton(str(item["quantity"]), callback_data="qty_val"),
        InlineKeyboardButton("➕", callback_data="qty_plus")
    ).add(InlineKeyboardButton("➡️ Далі", callback_data="to_photos"))
    await callback.message.edit_reply_markup(reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "to_photos", state=SellForm.entering_quantity)
async def to_photos(callback: types.CallbackQuery, state: FSMContext):
    await SellForm.uploading_photos.set()
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("➡️ Далі", callback_data="to_name"))
    await callback.message.answer("Надішліть до 10 фото або натисніть ➡️ Далі для пропуску.", reply_markup=markup)

@dp.message_handler(content_types=["photo"], state=SellForm.uploading_photos)
async def upload_photo(message: types.Message, state: FSMContext):
    photos = user_data[message.from_user.id]["items"][-1]["photos"]
    if len(photos) < 10:
        photos.append(message.photo[-1].file_id)

@dp.callback_query_handler(lambda c: c.data == "to_name", state=SellForm.uploading_photos)
async def to_name(callback: types.CallbackQuery, state: FSMContext):
    await SellForm.entering_name.set()
    await callback.message.answer("Введіть ваше імʼя:")

@dp.message_handler(state=SellForm.entering_name)
async def get_name(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["name"] = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("📱 Поділитись номером", request_contact=True)
    )
    await SellForm.entering_phone.set()
    await message.answer("Поділіться номером телефону:", reply_markup=markup)

@dp.message_handler(content_types=["contact"], state=SellForm.entering_phone)
async def get_phone(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["phone"] = message.contact.phone_number
    await finish_application(message)

async def finish_application(message):
    uid = message.from_user.id
    data = user_data[uid]
    caption = "<b>Заявка на викуп меблів</b>

"
    for i, item in enumerate(data["items"], 1):
        caption += f"<b>{i}. {item['category']}</b>
"
        caption += f"Опис: {item['description']}
"
        caption += f"Колір: {item['color']}
"
        caption += f"Кількість: {item['quantity']} шт.

"
    caption += f"Місто: {data['city']}"

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🛒 Купити", url="https://t.me/Luzanow")
    )

    # Відправити в групу
    first_photo = None
    for item in data["items"]:
        if item["photos"]:
            first_photo = item["photos"][0]
            break

    if first_photo:
        await bot.send_photo(GROUP_ID, first_photo, caption=caption, reply_markup=markup)
    else:
        await bot.send_message(GROUP_ID, caption, reply_markup=markup)

    # Відправити адміну
    details = caption + f"

Імʼя: {data['name']}
Телефон: {data['phone']}"
    await bot.send_message(ADMIN_ID, details)
    for item in data["items"]:
        for pid in item["photos"]:
            await bot.send_photo(ADMIN_ID, pid)

