import os
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv

load_dotenv('/root/kuzkabuh/.env')

BOT_TOKEN = os.getenv('KUZKABUH_BOT_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PATH = os.getenv('KUZKABUH_WEBHOOK_PATH')
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 8001
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
FLASK_ADMIN_API = os.getenv('FLASK_ADMIN_API')

# FSM
class OrderStates(StatesGroup):
    waiting_for_inn = State()
    waiting_for_email = State()
    waiting_for_phone = State()
    waiting_for_contact_time = State()
    waiting_for_service = State()
    waiting_for_urgency = State()
    confirm = State()

# Клавиатуры
main_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Оставить заявку", callback_data="new_order"))
cancel_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
back_cancel_kb = InlineKeyboardMarkup(row_width=2)
back_cancel_kb.add(
    InlineKeyboardButton("⬅️ Назад", callback_data="back"),
    InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
)
time_kb = InlineKeyboardMarkup(row_width=2)
time_kb.add(
    InlineKeyboardButton("Сегодня 14:00-16:00", callback_data="time_14_16"),
    InlineKeyboardButton("Сегодня 16:00-18:00", callback_data="time_16_18"),
    InlineKeyboardButton("Завтра 10:00-12:00", callback_data="time_tomorrow_10_12"),
    InlineKeyboardButton("Завтра 12:00-14:00", callback_data="time_tomorrow_12_14"),
)
services = [
    "Бухгалтерское обслуживание",
    "Регистрация ИП/ООО",
    "Сдача отчетности",
    "Консультация",
    "Другое"
]
service_kb = InlineKeyboardMarkup(row_width=1)
for service in services:
    service_kb.add(InlineKeyboardButton(service, callback_data=f"service_{service}"))
urgency_kb = InlineKeyboardMarkup(row_width=2)
urgency_kb.add(
    InlineKeyboardButton("Обычная", callback_data="urgency_normal"),
    InlineKeyboardButton("Срочно", callback_data="urgency_urgent"),
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "👋 Добро пожаловать! Нажмите кнопку ниже чтобы оставить заявку.",
        reply_markup=main_kb
    )

@dp.callback_query_handler(lambda c: c.data == "new_order")
async def process_new_order(callback_query: types.CallbackQuery, state: FSMContext):
    await OrderStates.waiting_for_inn.set()
    await callback_query.message.answer(
        "Введите ИНН (10 или 12 цифр):",
        reply_markup=cancel_kb
    )
    await callback_query.answer()

@dp.message_handler(lambda m: not re.fullmatch(r'\d{10}|\d{12}', m.text), state=OrderStates.waiting_for_inn)
async def invalid_inn(message: types.Message):
    await message.answer("❗️ ИНН должен содержать 10 или 12 цифр. Попробуйте снова.", reply_markup=cancel_kb)

@dp.message_handler(lambda m: re.fullmatch(r'\d{10}|\d{12}', m.text), state=OrderStates.waiting_for_inn)
async def process_inn(message: types.Message, state: FSMContext):
    await state.update_data(inn=message.text)
    await OrderStates.next()
    await message.answer("Введите ваш Email:", reply_markup=back_cancel_kb)

@dp.message_handler(lambda m: not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", m.text), state=OrderStates.waiting_for_email)
async def invalid_email(message: types.Message):
    await message.answer("❗️ Введите корректный email. Пример: example@mail.ru", reply_markup=back_cancel_kb)

@dp.message_handler(lambda m: re.fullmatch(r"[^@]+@[^@]+\.[^@]+", m.text), state=OrderStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await OrderStates.next()
    await message.answer("Введите ваш телефон (например, +7 (999) 123-45-67):", reply_markup=back_cancel_kb)

@dp.message_handler(lambda m: not re.fullmatch(r"\+7\s?\(?\d{3}\)?\s?\d{3}-?\d{2}-?\d{2}", m.text), state=OrderStates.waiting_for_phone)
async def invalid_phone(message: types.Message):
    await message.answer("❗️ Введите телефон в формате +7 (XXX) XXX-XX-XX", reply_markup=back_cancel_kb)

@dp.message_handler(lambda m: re.fullmatch(r"\+7\s?\(?\d{3}\)?\s?\d{3}-?\d{2}-?\d{2}", m.text), state=OrderStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await OrderStates.next()
    await message.answer("Выберите желаемое время для связи:", reply_markup=time_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("time_"), state=OrderStates.waiting_for_contact_time)
async def process_contact_time(callback_query: types.CallbackQuery, state: FSMContext):
    time_value = callback_query.data.replace("time_", "").replace("_", " ").capitalize()
    await state.update_data(contact_time=time_value)
    await OrderStates.next()
    await callback_query.message.edit_text("Выберите услугу:", reply_markup=service_kb)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("service_"), state=OrderStates.waiting_for_service)
async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
    service_value = callback_query.data.replace("service_", "")
    await state.update_data(service=service_value)
    await OrderStates.next()
    await callback_query.message.edit_text("Укажите срочность:", reply_markup=urgency_kb)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("urgency_"), state=OrderStates.waiting_for_urgency)
async def process_urgency(callback_query: types.CallbackQuery, state: FSMContext):
    urgency_value = "Срочно" if callback_query.data == "urgency_urgent" else "Обычная"
    await state.update_data(urgency=urgency_value)
    data = await state.get_data()
    summary = (
        f"<b>Проверьте данные:</b>\n"
        f"ИНН: <code>{data['inn']}</code>\n"
        f"Email: <code>{data['email']}</code>\n"
        f"Телефон: <code>{data['phone']}</code>\n"
        f"Время связи: <code>{data['contact_time']}</code>\n"
        f"Услуга: <code>{data['service']}</code>\n"
        f"Срочность: <code>{data['urgency']}</code>\n\n"
        "Все верно?"
    )
    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("✅ Да, отправить", callback_data="confirm"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
    )
    await OrderStates.next()
    await callback_query.message.edit_text(summary, reply_markup=confirm_kb, parse_mode=ParseMode.HTML)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "confirm", state=OrderStates.confirm)
async def process_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Отправка в Flask-админку
    try:
        requests.post(
            FLASK_ADMIN_API,
            json={
                "inn": data['inn'],
                "email": data['email'],
                "phone": data['phone'],
                "contact_time": data['contact_time'],
                "service": data['service'],
                "urgency": data['urgency']
            },
            timeout=5
        )
    except Exception as e:
        await callback_query.message.edit_text("Ошибка при сохранении заявки. Попробуйте позже.")
        await state.finish()
        await callback_query.answer()
        return

    # Сообщение админу
    msg = (
        f"💼 <b>Новая заявка!</b>\n"
        f"ИНН: <code>{data['inn']}</code>\n"
        f"Email: <code>{data['email']}</code>\n"
        f"Телефон: <code>{data['phone']}</code>\n"
        f"Время связи: <code>{data['contact_time']}</code>\n"
        f"Услуга: <code>{data['service']}</code>\n"
        f"Срочность: <code>{data['urgency']}</code>"
    )
    await bot.send_message(ADMIN_ID, msg, parse_mode=ParseMode.HTML)
    await callback_query.message.edit_text("Спасибо! Ваша заявка принята.", reply_markup=None)
    await state.finish()
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text("Заявка отменена.", reply_markup=None)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "back", state="*")
async def process_back(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == OrderStates.waiting_for_email.state:
        await OrderStates.waiting_for_inn.set()
        await callback_query.message.edit_text("Введите ИНН (10 или 12 цифр):", reply_markup=cancel_kb)
    elif current_state == OrderStates.waiting_for_phone.state:
        await OrderStates.waiting_for_email.set()
        await callback_query.message.edit_text("Введите ваш Email:", reply_markup=back_cancel_kb)
    elif current_state == OrderStates.waiting_for_contact_time.state:
        await OrderStates.waiting_for_phone.set()
        await callback_query.message.edit_text("Введите ваш телефон (например, +7 (999) 123-45-67):", reply_markup=back_cancel_kb)
    elif current_state == OrderStates.waiting_for_service.state:
        await OrderStates.waiting_for_contact_time.set()
        await callback_query.message.edit_text("Выберите желаемое время для связи:", reply_markup=time_kb)
    elif current_state == OrderStates.waiting_for_urgency.state:
        await OrderStates.waiting_for_service.set()
        await callback_query.message.edit_text("Выберите услугу:", reply_markup=service_kb)
    elif current_state == OrderStates.confirm.state:
        await OrderStates.waiting_for_urgency.set()
        await callback_query.message.edit_text("Укажите срочность:", reply_markup=urgency_kb)
    await callback_query.answer()

# ====== WEBHOOK ======
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=["message", "callback_query"])

async def on_shutdown(dp):
    await bot.delete_webhook()
    await storage.close()
    await storage.wait_closed()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
