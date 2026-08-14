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
async def command_warp_handler(message: Message):
    text = (
        f"👋 <b>Привет, {html.quote(message.from_user.full_name)}!</b>\n\n"
        "🌐 <b>AmneziaWG (WARP) Generator</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Создавай индивидуальные конфиги с обходом DPI-блокировок для комфортного просмотра <b>YouTube (4K)</b> "
        "и игры в <b>Roblox</b> без лагов и задержек.\n\n"
        "📍 <b>Выбери локацию сервера:</b>"
    )
    await message.answer(text, reply_markup=get_country_keyboard(), parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def command_help_handler(message: Message):
    help_text = (
        "📖 <b>Справка по использованию бота</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>1️⃣ Как получить конфиг?</b>\n"
        "• Нажмите /warp или /start.\n"
        "• Выберите нужную локацию.\n"
        "• Бот пришлёт файл <code>.conf</code>.\n\n"
        "<b>2️⃣ Как подключить?</b>\n"
        "• Импортируйте полученный файл в приложение <b>AmneziaWG</b>."
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("geo_"))
async def generate_warp_callback(callback: CallbackQuery):
    await callback.answer("⏳ Генерирую...")

    country_code = callback.data.split("_")[1]
    country_info = COUNTRY_ENDPOINTS.get(country_code, COUNTRY_ENDPOINTS["de"])

    status_msg = await callback.message.answer(
        f"🔍 <b>ПРЕДПРОСМОТР ЛОКАЦИИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 <b>Регион:</b> {country_info['name']}\n"
        f"🔑 <b>Эндпоинт:</b> <code>{country_info['endpoint']}</code>\n"
        f"🛡️ <b>Защита:</b> AmneziaWG Anti-DPI (<code>Jc=4</code>, <code>H1-H4</code>)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ <i>Регистрируем ключ в Cloudflare...</i>",
        parse_mode=ParseMode.HTML
    )

    warp_data = await asyncio.to_thread(register_warp_account, country_code)

    if not warp_data:
        await status_msg.edit_text(
            "❌ <b>Ошибка генерации!</b>\nПрокси временно недоступен или Cloudflare отклонил запрос. Попробуйте еще раз.", 
            parse_mode=ParseMode.HTML
        )
        return

    config_content = build_amnezia_wg_config(warp_data)
    file_bytes = config_content.encode("utf-8")
    filename = f"Amnezia_{country_code.upper()}_{callback.from_user.id}.conf"
    input_file = BufferedInputFile(file_bytes, filename=filename)

    await status_msg.delete()
    
    caption_text = (
        f"✅ <b>Конфиг успешно сгенерирован!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Локация:</b> {warp_data['country_name']}\n"
        f"📂 <b>Файл:</b> <code>{filename}</code>\n"
        f"🚀 <b>Назначение:</b> YouTube / Roblox / Anti-DPI\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📥 <b>Инструкция:</b> Скачай файл выше и импортируй его в <b>AmneziaWG</b>!"
    )

    await callback.message.answer_document(
        document=input_file,
        caption=caption_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_country_keyboard()
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
