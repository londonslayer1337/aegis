import os
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F, html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, BufferedInputFile, InlineKeyboardMarkup, 
    InlineKeyboardButton, CallbackQuery
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
        "Выбери локацию сервера для генерации конфига с обходом DPI:"
    )
    await message.answer(text, reply_markup=get_country_keyboard(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("geo_"))
async def generate_warp_callback(callback: CallbackQuery):
    await callback.answer("⏳ Генерирую...")
    country_code = callback.data.split("_")[1]
    
    status_msg = await callback.message.answer("🔍 <b>Регистрируем ключ...</b>", parse_mode=ParseMode.HTML)
    warp_data = await asyncio.to_thread(register_warp_account, country_code)

    if not warp_data:
        await status_msg.edit_text("❌ <b>Ошибка!</b> Похоже, Cloudflare блокирует этот сервер. Попробуй сменить регион или сервис.", parse_mode=ParseMode.HTML)
        return

    config_content = build_amnezia_wg_config(warp_data)
    filename = f"Amnezia_{country_code.upper()}_{callback.from_user.id}.conf"
    input_file = BufferedInputFile(config_content.encode("utf-8"), filename=filename)

    await status_msg.delete()
    await callback.message.answer_document(
        document=input_file,
        caption=f"✅ <b>Конфиг готов для {warp_data['country_name']}!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_country_keyboard()
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
