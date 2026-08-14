import os
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F, html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, 
    BufferedInputFile, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)

from warp_generator import register_warp_account, build_amnezia_wg_config, COUNTRY_ENDPOINTS

# Безопасный импорт dotenv для локальных тестов
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    sys.exit("❌ ОШИБКА: Переменная BOT_TOKEN не найдена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатура выбора страны
def get_country_keyboard():
    kb = [
        [
            InlineKeyboardButton(text="🇩🇪 Германия", callback_data="geo_de"),
            InlineKeyboardButton(text="🇳🇱 Нидерланды", callback_data="geo_nl")
        ],
        [
            InlineKeyboardButton(text="🇺🇸 США", callback_data="geo_us"),
            InlineKeyboardButton(text="🇯🇵 Япония", callback_data="geo_jp")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# 1. Команда /start и /warp
@dp.message(CommandStart())
@dp.message(Command("warp"))
async def command_start_handler(message: Message):
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}! 🚀\n\n"
        "Выбери **страну сервера** для генерации AmneziaWG (WARP) конфига.",
        reply_markup=get_country_keyboard(),
        parse_mode=ParseMode.HTML
    )

# 2. Полноценная команда /help
@dp.message(Command("help"))
async def command_help_handler(message: Message):
    help_text = (
        "❓ <b>Инструкция по использованию бота</b>\n\n"
        "<b>1. Как получить конфиг?</b>\n"
        "• Отправь команду /start или /warp.\n"
        "• Выбери нужную страну из списка (Германия, Нидерланды, США, Япония).\n"
        "• Бот моментально сгенерирует и пришлёт файл <code>.conf</code>.\n\n"
        "<b>2. Как подключить AmneziaWG?</b>\n"
        "• Скачай приложение <b>AmneziaWG</b> на телефон или ПК.\n"
        "• Сохрани присланный файл <code>.conf</code> на устройство.\n"
        "• В приложении нажми <b>«Добавить тоннель»</b> ➔ <b>«Импорт из файла»</b> и выбери скачанный файл.\n"
        "• Включи подключение — готово! YouTube и Roblox снова летают без задержек.\n\n"
        "<b>3. В чём особенность AmneziaWG?</b>\n"
        "• Конфиг содержит специальную маскировку (параметры Jc, H1-H4), которая обходит DPI-блокировки провайдеров."
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)

# 3. Обработка нажатия на страну и молниеносная выдача файла
@dp.callback_query(F.data.startswith("geo_"))
async def generate_warp_for_country(callback: CallbackQuery):
    country_code = callback.data.split("_")[1]
    country_info = COUNTRY_ENDPOINTS.get(country_code)

    await callback.answer()
    
    # Моментальная генерация в потоке
    warp_data = await asyncio.to_thread(register_warp_account, country_code)

    if not warp_data:
        await callback.message.answer("❌ <b>Не удалось сгенерировать конфиг.</b> Попробуй еще раз.", parse_mode=ParseMode.HTML)
        return

    config_content = build_amnezia_wg_config(warp_data)
    
    # Сборка файла в памяти без записи на диск
    file_bytes = config_content.encode("utf-8")
    filename = f"Amnezia_{country_code.upper()}_{callback.from_user.id}.conf"
    input_file = BufferedInputFile(file_bytes, filename=filename)

    await callback.message.answer_document(
        document=input_file,
        caption=(
            f"✅ <b>Твой конфиг для {warp_data['country_name']} готов!</b>\n\n"
            f"📍 <b>Локация:</b> {warp_data['country_name']}\n"
            f"🔑 <b>Эндпоинт:</b> <code>{warp_data['endpoint']}</code>\n\n"
            "Импортируй файл в приложение <b>AmneziaWG</b> и подключайся!"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=get_country_keyboard()
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("🚀 Бот успешно запущен на Railway!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
