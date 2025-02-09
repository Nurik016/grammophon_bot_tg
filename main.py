import asyncio
import logging
import os
import random

import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from gtts import gTTS

from config import BOT_TOKEN, GEMINI_API_KEY1

# Настройки логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Настройки бота
TOKEN = BOT_TOKEN
GENAI_API_KEY = GEMINI_API_KEY1

genai.configure(api_key=GENAI_API_KEY)

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()


# Функция для создания клавиатуры
def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ Проверка орфографии"), types.KeyboardButton(text="🔊 Текст в аудио")],
            [types.KeyboardButton(text="📖 Слово дня"), types.KeyboardButton(text="💬 Чат с ИИ")],
        ],
        resize_keyboard=True
    )


# Переменная состояния
user_state = {}

user_history = {}

illegal_words = ["наркотики", "оружие", "взлом", "терроризм", "подделка документов"]

# Слово дня
words_of_the_day = [
    ("Эфемерный", "Кратковременный, недолговечный.", "Его успех оказался эфемерным и быстро угас."),
    ("Латентный", "Скрытый, неявный.", "У него был латентный талант к рисованию, который проявился позже."),
    ("Перфекционизм", "Стремление к совершенству во всем.", "Её перфекционизм мешал ей завершать проекты вовремя."),
    ("Ригидность", "Жесткость, негибкость в поведении или мышлении.",
     "Ригидность его взглядов не позволяла ему принять новые идеи."),
    ("Эйфория", "Состояние крайней радости и воодушевления.", "После победы он испытывал невероятную эйфорию."),
    ("Дифференциация", "Разделение на части, разграничение.",
     "Дифференциация обязанностей помогла наладить работу команды."),
    ("Коннотация", "Дополнительный смысл или оттенок значения слова.", "Слово 'дом' имеет теплую и уютную коннотацию."),
    ("Диссонанс", "Несоответствие, противоречие.", "В его словах и поступках ощущался явный диссонанс."),
    ("Фрустрация", "Разочарование из-за невозможности достичь цели.", "Неудачи вызывали у него сильную фрустрацию."),
    ("Интенция", "Намерение, направленность сознания на объект.",
     "Его интенция была очевидна — он хотел добиться успеха."),
    ("Эскапизм", "Стремление уйти от реальности.", "Чтение книг стало его формой эскапизма."),
    ("Апробировать", "Проверить на практике, утвердить.", "Перед запуском проект необходимо апробировать."),
    ("Идентичность", "Осознание своей индивидуальности.", "Кризис идентичности заставил его искать новый смысл жизни."),
    ("Сублимация", "Перенаправление энергии в социально приемлемое русло.", "Он сублимировал свою агрессию в спорт."),
    ("Детерминированность", "Обусловленность причинно-следственными связями.",
     "Его поведение было детерминировано прошлым опытом."),
    ("Эклектика", "Смешение разных стилей и направлений.",
     "Интерьер его дома отличался эклектикой — модерн соседствовал с классикой."),
    ("Рефлексия", "Осмысление своих поступков и мыслей.", "После неудачи он погрузился в глубокую рефлексию."),
    ("Конгруэнтность", "Соответствие внутреннего состояния внешним проявлениям.",
     "Его искренность ощущалась благодаря конгруэнтности слов и эмоций."),
    ("Гедонизм", "Стремление к наслаждению и удовольствию.",
     "Он придерживался философии гедонизма, наслаждаясь каждым моментом."),
    ("Аморфный", "Бесформенный, не имеющий четких очертаний.",
     "Его позиция в этом вопросе была аморфной и неопределенной.")

]


@router.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"Пользователь {message.chat.id} запустил бота.")
    await message.answer(
        "👋 Добро пожаловать! Я помогу вам с орфографией, озвучу текст или пообщаюсь с вами! \n\nВыберите опцию ниже.",
        reply_markup=main_keyboard()
    )


# Проверка орфографии
@router.message(lambda message: message.text == "✅ Проверка орфографии")
async def start_spell_check(message: Message):
    logging.info(f"Пользователь {message.chat.id} выбрал проверку орфографии.")
    user_state[message.chat.id] = "spell_check"
    await message.answer("✍️ Напишите текст для проверки орфографии:", reply_markup=types.ReplyKeyboardRemove())


@router.message(lambda message: user_state.get(message.chat.id) == "spell_check")
async def check_spelling(message: Message):
    user_text = message.text
    logging.info(f"Пользователь {message.chat.id} отправил текст на проверку: {user_text}")

    prompt = f"Исправь орфографические ошибки в следующем тексте: {user_text}"

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        corrected_text = response.text if response.text else "❌ Ошибка обработки текста."

        logging.info(f"Ответ AI для {message.chat.id}: {corrected_text}")

        if corrected_text.strip() == user_text.strip():
            await message.answer("✅ Всё отлично! Ошибок не найдено!", reply_markup=main_keyboard())
        else:
            await message.answer(f"🚨 Исправленный текст:\n{corrected_text}", reply_markup=main_keyboard())

    except Exception as e:
        logging.error(f"Ошибка при обработке запроса {message.chat.id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при обработке текста. Попробуйте снова.", reply_markup=main_keyboard())

    user_state.pop(message.chat.id, None)


# Слово дня
@router.message(lambda message: message.text == "📖 Слово дня")
async def send_word_of_the_day(message: Message):
    word, meaning, example = random.choice(words_of_the_day)
    logging.info(f"Пользователь {message.chat.id} запросил слово дня: {word}")
    await message.answer(f"📌 *{word}*\n📖 {meaning}\n📝 {example}", parse_mode="Markdown", reply_markup=main_keyboard())


# Храним историю сообщений
user_history = {}


# Функция для клавиатуры во время чата с ИИ
def chat_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="⏹ Остановить чат")]],
        resize_keyboard=True
    )


# Чат с ИИ (Эмиль Берлинер)
@router.message(lambda message: message.text == "💬 Чат с ИИ")
async def start_chat(message: Message):
    logging.info(f"Пользователь {message.chat.id} начал чат с ИИ.")
    user_state[message.chat.id] = "chat_ai"
    user_history[message.chat.id] = []  # Очищаем историю чата
    await message.answer("🤖 Привет! Я Эмиль Берлинер, твой друг и учитель русского языка. О чем поговорим?",
                         reply_markup=chat_keyboard())


@router.message(lambda message: message.text == "⏹ Остановить чат")
async def stop_chat(message: Message):
    logging.info(f"Пользователь {message.chat.id} завершил чат с ИИ.")
    user_state.pop(message.chat.id, None)
    user_history.pop(message.chat.id, None)  # Очищаем историю
    await message.answer("🔙 Вы вернулись в главное меню.", reply_markup=main_keyboard())


@router.message(lambda message: user_state.get(message.chat.id) == "chat_ai")
async def chat_with_ai(message: Message):
    user_input = message.text
    logging.info(f"Пользователь {message.chat.id} отправил запрос ИИ: {user_input}")

    if message.chat.id not in user_history:
        user_history[message.chat.id] = []  # Если истории нет, создаем новую

    # Проверка языка
    if not all(ord(c) < 128 or 'а' <= c.lower() <= 'я' for c in user_input):
        warning_text = "⚠️ Я отвечу на твой запрос, но напоминаю – пиши на русском языке!"
    else:
        warning_text = ""

    # Проверка на запрещенный контент
    if any(word in user_input.lower() for word in illegal_words):
        logging.warning(f"Пользователь {message.chat.id} запросил запрещенный контент!")
        await message.answer("⛔ Я не буду отвечать на такие запросы. \n\n*Error 404: Информация не найдена*",
                             parse_mode="Markdown", reply_markup=main_keyboard())
        user_state.pop(message.chat.id, None)
        return

    # Добавляем сообщение пользователя в историю
    user_history[message.chat.id].append(f"Пользователь: {user_input}")

    # Оставляем только последние 10 сообщений
    if len(user_history[message.chat.id]) > 10:
        user_history[message.chat.id] = user_history[message.chat.id][-10:]

    prompt = f"""
    Ты – Эмиль Берлинер, но можно просто Эмиль. Ты дружелюбный друг  
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        if not response.text:
            raise ValueError("Пустой ответ от ИИ.")

        ai_reply = response.text
        logging.info(f"Ответ ИИ для {message.chat.id}: {ai_reply}")

        # Добавляем ответ ИИ в историю
        user_history[message.chat.id].append(f"Эмиль: {ai_reply}")

        await message.answer(f"{warning_text}\n{ai_reply}", reply_markup=chat_keyboard())

    except ValueError:
        logging.warning(f"Пустой ответ от ИИ для {message.chat.id}.")
        await message.answer("❌ Не могу обработать запрос. Попробуйте задать вопрос по-другому.",
                             reply_markup=main_keyboard())

    except Exception as e:
        logging.error(f"Ошибка в чате с ИИ для {message.chat.id}: {e}", exc_info=True)
        await message.answer("⛔ Я не буду отвечать на такие запросы.", reply_markup=main_keyboard())


# Текст в аудио
@router.message(lambda message: message.text == "🔊 Текст в аудио")
async def start_text_to_speech(message: Message):
    logging.info(f"Пользователь {message.chat.id} выбрал текст в аудио.")
    user_state[message.chat.id] = "text_to_speech"
    await message.answer("🎤 Напишите текст, который нужно озвучить:", reply_markup=types.ReplyKeyboardRemove())


@router.message(lambda message: user_state.get(message.chat.id) == "text_to_speech")
async def text_to_speech(message: Message):
    try:
        logging.info(f"Пользователь {message.chat.id} отправил текст для озвучки: {message.text}")

        tts = gTTS(message.text, lang='ru')
        filename = f"audio_{message.chat.id}.mp3"
        tts.save(filename)

        audio_file = FSInputFile(filename)
        await bot.send_audio(message.chat.id, audio_file, title="Ваш аудиофайл", performer="Bot Voice")

        await message.answer("✅ Аудио готово!", reply_markup=main_keyboard())

    except Exception as e:
        logging.error(f"Ошибка при генерации аудио для {message.chat.id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации аудио.", reply_markup=main_keyboard())

    finally:
        if os.path.exists(filename):
            os.remove(filename)
        user_state.pop(message.chat.id, None)


# Запуск бота
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logging.info("Бот запущен.")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен.")
