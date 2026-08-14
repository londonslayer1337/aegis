import os
import asyncio
import logging
import sys
from dotenv import load_dotenv

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

load_dotenv()
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

@dp.message(CommandStart())
@dp.message(Command("warp"))
async def command_start_handler(message: Message):
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}! 🚀\n\n"
        "Выбери **страну сервера** для генерации AmneziaWG (WARP) конфига.\n"
        "Подходит для комфортного просмотра YouTube и игры в Roblox без задержек!",
        reply_markup=get_country_keyboard(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data.startswith("geo_"))
async def generate_warp_for_country(callback: CallbackQuery):
    country_code = callback.data.split("_")[1]
    country_info = COUNTRY_ENDPOINTS.get(country_code)

    await callback.answer()
    
    # 1. Показываем предварительный просмотр выбранной локации
    status_msg = await callback.message.edit_text(
        f"🔍 <b>ПРЕДПРОСМОТР ЛОКАЦИИ:</b>\n"
        f"📍 Регион: {country_info['name']}\n"
        f"🌐 Эндпоинт: <code>{country_info['endpoint']}</code>\n\n"
        f"⏳ <i>Регистрирую ключ и формирую .conf файл...</i>",
        parse_mode=ParseMode.HTML
    )

    # 2. Генерируем ключ в фоновом потоке
    warp_data = await asyncio.to_thread(register_warp_account, country_code)

    if not warp_data:
        await status_msg.edit_text("❌ <b>Не удалось сгенерировать конфиг.</b> Попробуй позже.", parse_mode=ParseMode.HTML)
        return

    config_content = build_amnezia_wg_config(warp_data)
    
    # 3. Отправка конфига из OЗУ
    file_bytes = config_content.encode("utf-8")
    filename = f"Amnezia_{country_code.upper()}_{callback.from_user.id}.conf"
    input_file = BufferedInputFile(file_bytes, filename=filename)

    await status_msg.delete()
    await callback.message.answer_document(
        document=input_file,
        caption=(
            f"✅ <b>Твой конфиг для {warp_data['country_name']} готов!</b>\n\n"
            f"📍 <b>Локация:</b> {warp_data['country_name']}\n"
            f"🔑 <b>Эндпоинт:</b> <code>{warp_data['endpoint']}</code>\n\n"
            "1. Скачай файл <code>.conf</code>\n"
            "2. Импортируй его в приложение <b>AmneziaWG</b>\n"
            "3. Наслаждайся быстрым интернетом!"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=get_country_keyboard()
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("🚀 Бот запущен! Выбор стран (DE, NL, US, JP) работает.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
