import os
import re
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv

# 1. Загружаем .env
load_dotenv('/root/kuzkabuh/.env')

BOT_TOKEN       = os.getenv('KUZKABUH_BOT_TOKEN')
WEBHOOK_HOST    = os.getenv('WEBHOOK_HOST')
WEBHOOK_PATH    = os.getenv('KUZKABUH_WEBHOOK_PATH')
WEBHOOK_URL     = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST     = "0.0.0.0"
WEBAPP_PORT     = 8001

ADMIN_ID        = int(os.getenv('ADMIN_TELEGRAM_ID'))
ADMIN_USER      = os.getenv('ADMIN_USER')
ADMIN_PASS      = os.getenv('ADMIN_PASS')
FLASK_ADMIN_API = os.getenv('FLASK_ADMIN_API')

# 2. FSM — состояния
class OrderStates(StatesGroup):
    waiting_for_inn          = State()
    waiting_for_email        = State()
    waiting_for_name         = State()
    waiting_for_phone        = State()
    waiting_for_contact_time = State()
    waiting_for_service      = State()
    waiting_for_urgency      = State()
    confirm                  = State()

# 3. Клавиатуры
main_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Оставить заявку", callback_data="new_order")
)
cancel_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("❌ Отмена", callback_data="cancel")
)
back_cancel_kb = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("⬅️ Назад", callback_data="back"),
    InlineKeyboardButton("❌ Отмена", callback_data="cancel")
)
time_kb = InlineKeyboardMarkup(row_width=2).add(
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
for svc in services:
    service_kb.add(InlineKeyboardButton(svc, callback_data=f"service_{svc}"))
urgency_kb = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("Обычная", callback_data="urgency_normal"),
    InlineKeyboardButton("Срочно",   callback_data="urgency_urgent")
)

# 4. Бот и диспетчер
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 5. Хэндлеры

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "👋 Добро пожаловать! Нажмите кнопку ниже, чтобы оставить заявку.",
        reply_markup=main_kb
    )

@dp.callback_query_handler(lambda c: c.data=="new_order")
async def process_new_order(cq: types.CallbackQuery, state: FSMContext):
    await OrderStates.waiting_for_inn.set()
    await cq.message.answer("Введите ИНН (10 или 12 цифр):", reply_markup=cancel_kb)
    await cq.answer()

# Ввод ИНН
@dp.message_handler(lambda m: not re.fullmatch(r'\d{10}|\d{12}', m.text),
                    state=OrderStates.waiting_for_inn)
async def invalid_inn(message: types.Message):
    await message.answer("❗️ ИНН должен быть 10 или 12 цифр.", reply_markup=cancel_kb)

@dp.message_handler(lambda m: re.fullmatch(r'\d{10}|\d{12}', m.text),
                    state=OrderStates.waiting_for_inn)
async def process_inn(message: types.Message, state: FSMContext):
    await state.update_data(inn=message.text)
    await OrderStates.next()
    await message.answer("Введите ваш Email:", reply_markup=back_cancel_kb)

# Ввод Email
@dp.message_handler(lambda m: not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", m.text),
                    state=OrderStates.waiting_for_email)
async def invalid_email(message: types.Message):
    await message.answer("❗️ Некорректный email. Пример: example@mail.ru", reply_markup=back_cancel_kb)

@dp.message_handler(lambda m: re.fullmatch(r"[^@]+@[^@]+\.[^@]+", m.text),
                    state=OrderStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await OrderStates.next()
    await message.answer("Введите ваше имя:", reply_markup=back_cancel_kb)

# Ввод Имени
@dp.message_handler(lambda m: len(m.text.strip())<2,
                    state=OrderStates.waiting_for_name)
async def invalid_name(message: types.Message):
    await message.answer("❗️ Имя должно быть минимум 2 символа.", reply_markup=back_cancel_kb)

@dp.message_handler(state=OrderStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await OrderStates.next()
    await message.answer(
        "Введите ваш телефон (+7XXXXXXXXXX или 8XXXXXXXXXX):",
        reply_markup=back_cancel_kb
    )

# Ввод телефона
@dp.message_handler(lambda m: not re.fullmatch(r'^(?:\+7|8)\d{10}$', m.text),
                    state=OrderStates.waiting_for_phone)
async def invalid_phone(message: types.Message):
    await message.answer(
        "❗️ Неверный формат. Пример: +71231234567 или 81231234567",
        reply_markup=back_cancel_kb
    )

@dp.message_handler(lambda m: re.fullmatch(r'^(?:\+7|8)\d{10}$', m.text),
                    state=OrderStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await OrderStates.next()
    await message.answer("Выберите желаемое время для связи:", reply_markup=time_kb)

# Выбор времени
@dp.callback_query_handler(lambda c: c.data.startswith("time_"),
                           state=OrderStates.waiting_for_contact_time)
async def process_contact_time(cq: types.CallbackQuery, state: FSMContext):
    slot = cq.data.replace("time_","").replace("_"," ").capitalize()
    await state.update_data(contact_time=slot)
    await OrderStates.next()
    await cq.message.edit_text("Выберите услугу:", reply_markup=service_kb)
    await cq.answer()

# Выбор услуги
@dp.callback_query_handler(lambda c: c.data.startswith("service_"),
                           state=OrderStates.waiting_for_service)
async def process_service(cq: types.CallbackQuery, state: FSMContext):
    svc = cq.data.replace("service_","")
    await state.update_data(service=svc)
    await OrderStates.next()
    await cq.message.edit_text("Укажите срочность:", reply_markup=urgency_kb)
    await cq.answer()

# Выбор срочности
@dp.callback_query_handler(lambda c: c.data.startswith("urgency_"),
                           state=OrderStates.waiting_for_urgency)
async def process_urgency(cq: types.CallbackQuery, state: FSMContext):
    urg = "Срочно" if cq.data=="urgency_urgent" else "Обычная"
    await state.update_data(urgency=urg)

    d = await state.get_data()
    summary = (
        f"<b>Проверьте данные:</b>\n"
        f"ИНН: <code>{d['inn']}</code>\n"
        f"Email: <code>{d['email']}</code>\n"
        f"Имя: <code>{d['name']}</code>\n"
        f"Телефон: <code>{d['phone']}</code>\n"
        f"Время связи: <code>{d['contact_time']}</code>\n"
        f"Услуга: <code>{d['service']}</code>\n"
        f"Срочность: <code>{d['urgency']}</code>\n\n"
        "Все верно?"
    )
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Да, отправить", callback_data="confirm"),
        InlineKeyboardButton("❌ Отмена",       callback_data="cancel")
    )
    await OrderStates.next()
    await cq.message.edit_text(summary, reply_markup=kb, parse_mode="HTML")
    await cq.answer()

# Подтверждение
@dp.callback_query_handler(lambda c: c.data=="confirm", state=OrderStates.confirm)
async def process_confirm(cq: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ok = False
    try:
        resp = requests.post(
            FLASK_ADMIN_API,
            json={
                "inn":          data['inn'],
                "email":        data['email'],
                "name":         data['name'],
                "phone":        data['phone'],
                "contact_time": data['contact_time'],
                "service":      data['service'],
                "urgency":      data['urgency'],
            },
            auth=(ADMIN_USER, ADMIN_PASS),
            timeout=5
        )
        ok = resp.ok
    except Exception as e:
        print("API error:", e)
        ok = False

    # уведомляем админа в Telegram
    admin_msg = (
        f"💼 <b>Новая заявка!</b>\n"
        f"ИНН: <code>{data['inn']}</code>\n"
        f"Email: <code>{data['email']}</code>\n"
        f"Имя: <code>{data['name']}</code>\n"
        f"Телефон: <code>{data['phone']}</code>\n"
        f"Время связи: <code>{data['contact_time']}</code>\n"
        f"Услуга: <code>{data['service']}</code>\n"
        f"Срочность: <code>{data['urgency']}</code>"
    )
    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")

    if ok:
        await cq.message.edit_text("✅ Заявка принята и сохранена.", reply_markup=None)
    else:
        await cq.message.edit_text("❌ Ошибка при сохранении. Попробуйте позже.", reply_markup=None)

    await state.finish()
    await cq.answer()

# Отмена
@dp.callback_query_handler(lambda c: c.data=="cancel", state="*")
async def process_cancel(cq: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await cq.message.edit_text("⚠️ Заявка отменена.", reply_markup=None)
    await cq.answer()

# Назад
@dp.callback_query_handler(lambda c: c.data=="back", state="*")
async def process_back(cq: types.CallbackQuery, state: FSMContext):
    cur = await state.get_state()
    if cur == OrderStates.waiting_for_email.state:
        await OrderStates.waiting_for_inn.set()
        await cq.message.edit_text("Введите ИНН (10 или 12 цифр):", reply_markup=cancel_kb)
    elif cur == OrderStates.waiting_for_name.state:
        await OrderStates.waiting_for_email.set()
        await cq.message.edit_text("Введите ваш Email:", reply_markup=back_cancel_kb)
    elif cur == OrderStates.waiting_for_phone.state:
        await OrderStates.waiting_for_name.set()
        await cq.message.edit_text("Введите ваше имя:", reply_markup=back_cancel_kb)
    elif cur == OrderStates.waiting_for_contact_time.state:
        await OrderStates.waiting_for_phone.set()
        await cq.message.edit_text(
            "Введите ваш телефон (+7XXXXXXXXXX или 8XXXXXXXXXX):",
            reply_markup=back_cancel_kb
        )
    elif cur == OrderStates.waiting_for_service.state:
        await OrderStates.waiting_for_contact_time.set()
        await cq.message.edit_text("Выберите время:", reply_markup=time_kb)
    elif cur == OrderStates.waiting_for_urgency.state:
        await OrderStates.waiting_for_service.set()
        await cq.message.edit_text("Выберите услугу:", reply_markup=service_kb)
    elif cur == OrderStates.confirm.state:
        await OrderStates.waiting_for_urgency.set()
        await cq.message.edit_text("Укажите срочность:", reply_markup=urgency_kb)
    await cq.answer()

# WEBHOOK
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=["message","callback_query"])

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
        host=WEBAPP_HOST, port=WEBAPP_PORT
    )
