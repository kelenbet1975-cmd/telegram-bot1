import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import BOT_TOKEN, YANDEX_API_KEY, FOLDER_ID, ADMIN_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ---------- КНОПКИ ----------
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("🤖 AI Консультант"),
    KeyboardButton("📝 Оставить заявку")
)

# ---------- СОСТОЯНИЯ ----------
class Form(StatesGroup):
    name = State()
    phone = State()
    task = State()

# ---------- YANDEX AI ----------
def ask_ai(text):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 1000
        },
        "messages": [
            {"role": "user", "text": text}
        ]
    }

    r = requests.post(url, json=data, headers=headers)
    result = r.json()

    try:
        return result["result"]["alternatives"][0]["message"]["text"]
    except:
        return "⚠️ AI временно недоступен. Попробуйте позже."

# ---------- СТАРТ ----------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    text = (
        "Здравствуйте! 👋\n\n"
        "Я AI-консультант по созданию ботов для бизнеса.\n\n"
        "✅ Помогаю:\n"
        "• Привлекать клиентов\n"
        "• Автоматизировать продажи\n"
        "• Делать Telegram-ботов под ключ\n\n"
        "Нажмите кнопку ниже 👇"
    )
    await message.answer(text, reply_markup=main_kb)

# ---------- AI ЧАТ ----------
@dp.message_handler(lambda m: m.text == "🤖 AI Консультант")
async def ai_start(message: types.Message):
    await message.answer(
        "Задайте ваш вопрос 👇\n\n"
        "Например:\n"
        "• Сколько стоит бот?\n"
        "• Зачем бизнесу бот?\n"
        "• Какие функции возможны?",
        reply_markup=main_kb
    )

@dp.message_handler(lambda m: m.text not in ["🤖 AI Консультант", "📝 Оставить заявку"])
async def ai_chat(message: types.Message):
    answer = ask_ai(message.text)
    await message.answer(answer, reply_markup=main_kb)

# ---------- ЗАЯВКА ----------
@dp.message_handler(lambda m: m.text == "📝 Оставить заявку")
async def form_start(message: types.Message):
    await message.answer("Введите ваше имя:")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await Form.phone.set()

@dp.message_handler(state=Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Опишите задачу:")
    await Form.task.set()

@dp.message_handler(state=Form.task)
async def get_task(message: types.Message, state: FSMContext):
    data = await state.get_data()

    text = (
        "📩 НОВАЯ ЗАЯВКА\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📝 Задача: {message.text}\n\n"
        f"🆔 ID: {message.from_user.id}"
    )

    await bot.send_message(ADMIN_ID, text)

    await message.answer(
        "✅ Заявка принята!\n\n"
        "Менеджер уже получил вашу заявку и напишет вам здесь.",
        reply_markup=main_kb
    )

    # АВТО ОТВЕТ КЛИЕНТУ
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Здравствуйте! Мы получили вашу заявку ✅ Скоро с вами свяжемся."
    )

    await state.finish()

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    print("🚀 Bot started...")
    executor.start_polling(dp, skip_updates=True)
