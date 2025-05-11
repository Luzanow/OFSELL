
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
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📍 Вибрати місто"))
    await message.answer("Привіт! Щоб почати оформлення заявки, натисніть кнопку нижче:", reply_markup=markup)

# Міста з емодзі
city_options = {
    "Київ 🏙️": "Київ 🏙️",
    "Харків 🏙️": "Харків 🏙️",
    "Одеса 🌊": "Одеса 🌊",
    "Дніпро 🌆": "Дніпро 🌆",
    "Львів 🏞️": "Львів 🏞️"
}

# Стан меблів
conditions = ["✅ Гарний", "⚠️ Середній", "❌ Потребує ремонту"]

# Класи станів
class SellForm(StatesGroup):
    choosing_city = State()
    choosing_category = State()
    entering_description = State()
    entering_color = State()
    choosing_condition = State()
    choosing_quantity = State()
    uploading_photos = State()
    entering_price = State()
    confirming = State()


@dp.message_handler(commands="done", state="*")
async def confirm_final(message: types.Message, state: FSMContext):
    data = user_data.get(message.from_user.id)
    if not data or not data.get("items"):
        await message.answer("Немає даних для заявки.")


    # Запускаємо вибір категорій після вибору міста
    await category_step(message, state)
    return

    caption = "<b>Заявка на викуп меблів</b>\n\n"
    all_photos = []
    for i, item in enumerate(data["items"], 1):
        caption += f"<b>{i}. {item['category']}</b>\n"
        caption += f"Опис: {item['description']}\n"
        caption += f"Колір: {item['color']}\n"
        caption += f"Стан: {item['condition']}\n"
        caption += f"Кількість: {item['quantity']} шт.\n"
        if item.get("price"):
            caption += f"Ціна: {item['price']} грн/шт\n"
        caption += "\n"
        all_photos += item.get("photos", [])

    caption += f"Місто: {data['city']}"

    # Надсилання медіа-посту в групу
    media_group = []
    for i, photo_id in enumerate(all_photos[:10]):
        media_group.append(InputMediaPhoto(media=photo_id, caption=caption if i == 0 else ""))

    if media_group:
        await bot.send_media_group(chat_id=GROUP_ID, media=media_group)

    # Кнопка Придбати під постом
    button = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🛒 Придбати", url="https://t.me/Luzanow")
    )
    await bot.send_message(chat_id=GROUP_ID, text=caption, reply_markup=button)

    # Надсилання адміну
    await bot.send_message(chat_id=ADMIN_ID, text="Нова заявка на викуп меблів:")
    await bot.send_message(chat_id=ADMIN_ID, text=caption)

    await message.answer("✅ Заявка надіслана.")
    await state.finish()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)


@dp.message_handler(state=SellForm.choosing_category)
async def category_step(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["selected_categories"] = []
    
    categories = [
        "Стіл Лофт", "Стіл ДСП", "Офісне крісло", "Стільці",
        "Шафи", "Тумби", "Стелажі", "Сейфи", "Офісна техніка", "Інші меблі"
    ]

    markup = InlineKeyboardMarkup(row_width=2)
    for cat in categories:
        markup.insert(InlineKeyboardButton(f"◻️ {cat}", callback_data=f"cat_{cat}"))
    markup.add(InlineKeyboardButton("✅ Завершити вибір", callback_data="cat_done"))
    await message.answer("Оберіть меблі, які хочете продати:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"), state=SellForm.choosing_category)
async def toggle_category(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    category = callback.data[4:]
    selected = user_data[user_id].setdefault("selected_categories", [])

    if category == "done":
        if not selected:
            await callback.answer("Оберіть хоча б одну категорію.")
            return
        await callback.message.edit_text("✅ Категорії збережено.")
        await SellForm.next()
        return

    if category in selected:
        selected.remove(category)
    else:
        selected.append(category)

    
    categories = [
        "Стіл Лофт", "Стіл ДСП", "Офісне крісло", "Стільці",
        "Шафи", "Тумби", "Стелажі", "Сейфи", "Офісна техніка", "Інші меблі"
    ]

    markup = InlineKeyboardMarkup(row_width=2)
    for cat in categories:
        symbol = "☑️" if cat in selected else "◻️"
        markup.insert(InlineKeyboardButton(f"{symbol} {cat}", callback_data=f"cat_{cat}"))
    markup.add(InlineKeyboardButton("✅ Завершити вибір", callback_data="cat_done"))

    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer("Оновлено")


# Далі — опис, колір, стан, кількість, фото, ціна після категорій

@dp.message_handler(state=SellForm.entering_description)
async def enter_description(message: types.Message, state: FSMContext):
    item = user_data[message.from_user.id].setdefault("current_item", {})
    item["description"] = message.text
    await message.answer("Оберіть колір:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Білий", "Сірий", "Чорний", "Коричневий", "Інший"))
    await SellForm.entering_color.set()

@dp.message_handler(state=SellForm.entering_color)
async def enter_color(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["current_item"]["color"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Гарний", "⚠️ Середній", "❌ Потребує ремонту")
    await message.answer("Оберіть стан меблів:", reply_markup=kb)
    await SellForm.choosing_condition.set()

@dp.message_handler(state=SellForm.choosing_condition)
async def enter_condition(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["current_item"]["condition"] = message.text
    kb = InlineKeyboardMarkup(row_width=3).add(
        InlineKeyboardButton("➖", callback_data="qty_dec"),
        InlineKeyboardButton("1", callback_data="qty_val"),
        InlineKeyboardButton("➕", callback_data="qty_inc")
    ).add(InlineKeyboardButton("➡️ Далі", callback_data="qty_next"))
    user_data[message.from_user.id]["current_item"]["quantity"] = 1
    await message.answer("Вкажіть кількість:", reply_markup=kb)
    await SellForm.choosing_quantity.set()


@dp.callback_query_handler(lambda c: c.data in ["qty_dec", "qty_inc", "qty_next"], state=SellForm.choosing_quantity)
async def handle_quantity(callback: types.CallbackQuery, state: FSMContext):
    data = user_data[callback.from_user.id]
    current = data["current_item"]
    qty = current.get("quantity", 1)

    if callback.data == "qty_dec" and qty > 1:
        qty -= 1
    elif callback.data == "qty_inc":
        qty += 1
    elif callback.data == "qty_next":
        await callback.message.answer("Надішліть фото (до 10):")
        await SellForm.uploading_photos.set()
        return

    current["quantity"] = qty
    kb = InlineKeyboardMarkup(row_width=3).add(
        InlineKeyboardButton("➖", callback_data="qty_dec"),
        InlineKeyboardButton(str(qty), callback_data="qty_val"),
        InlineKeyboardButton("➕", callback_data="qty_inc")
    ).add(InlineKeyboardButton("➡️ Далі", callback_data="qty_next"))
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=SellForm.uploading_photos)
async def handle_photos(message: types.Message, state: FSMContext):
    item = user_data[message.from_user.id]["current_item"]
    photos = item.setdefault("photos", [])
    if len(photos) >= 10:
        await message.answer("Максимум 10 фото. Введіть ціну або пропустіть:")
        await SellForm.entering_price.set()
        return

    photos.append(message.photo[-1].file_id)
    await message.answer(f"Фото {len(photos)} з 10 додано. Надішліть ще або напишіть 'Готово'.")

@dp.message_handler(lambda m: m.text.lower() == "готово", state=SellForm.uploading_photos)
async def done_photos(message: types.Message, state: FSMContext):
    await message.answer("Хочете вказати свою ціну за одиницю? Якщо ні — натисніть 'Пропустити'", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Пропустити"))
    await SellForm.entering_price.set()

@dp.message_handler(state=SellForm.entering_price)
async def handle_price(message: types.Message, state: FSMContext):
    if message.text.lower() != "пропустити":
        user_data[message.from_user.id]["current_item"]["price"] = message.text
    user_data[message.from_user.id]["items"].append(user_data[message.from_user.id]["current_item"])
    user_data[message.from_user.id]["current_item"] = {}
    await message.answer("✅ Позицію збережено.")
    await message.answer("Щоб завершити заявку — натисніть /done")



@dp.message_handler(commands="myitems", state="*")
async def show_items(message: types.Message, state: FSMContext):
    items = user_data.get(message.from_user.id, {}).get("items", [])
    if not items:
        await message.answer("У вас немає збережених позицій.")
        return

    for i, item in enumerate(items):
        caption = f"<b>{i+1}. {item['category']}</b>\nОпис: {item['description']}\nКолір: {item['color']}\nСтан: {item['condition']}\nКількість: {item['quantity']}"
        if item.get("price"):
            caption += f"\nЦіна: {item['price']} грн/шт"
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_{i}"),
            InlineKeyboardButton("🗑️ Видалити", callback_data=f"delete_{i}")
        )
        if item.get("photos"):
            await bot.send_photo(chat_id=message.chat.id, photo=item["photos"][0], caption=caption, parse_mode="HTML", reply_markup=markup)
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("delete_"), state="*")
async def delete_item(callback: types.CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    user_data[callback.from_user.id]["items"].pop(idx)
    await callback.answer("Видалено.")
    await callback.message.edit_text("Позицію видалено.")

@dp.callback_query_handler(lambda c: c.data.startswith("edit_"), state="*")
async def edit_item(callback: types.CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    item = user_data[callback.from_user.id]["items"][idx]
    user_data[callback.from_user.id]["current_item"] = item
    user_data[callback.from_user.id]["edit_index"] = idx
    await callback.message.answer("Редагуємо позицію. Введіть новий опис:")
    await SellForm.entering_description.set()

@dp.message_handler(state=SellForm.entering_price)
async def handle_price_editable(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if message.text.lower() != "пропустити":
        user_data[uid]["current_item"]["price"] = message.text

    index = user_data[uid].get("edit_index")
    if index is not None:
        user_data[uid]["items"][index] = user_data[uid]["current_item"]
        user_data[uid]["edit_index"] = None
        await message.answer("✅ Позицію оновлено.")
    else:
        user_data[uid]["items"].append(user_data[uid]["current_item"])
    user_data[uid]["current_item"] = {}
    await message.answer("Щоб завершити заявку — натисніть /done")
if name == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

