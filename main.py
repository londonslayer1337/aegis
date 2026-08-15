import os
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from warp_generator import register_warp_account, build_amnezia_wg_config, COUNTRY_ENDPOINTS

TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher()

def get_country_keyboard():
    buttons = []
    for code, info in COUNTRY_ENDPOINTS.items():
        buttons.append([InlineKeyboardButton(text=f"🌐 {info['name']}", callback_data=f"gen_{code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
@dp.message(Command("warp"))
async def command_warp_handler(message: Message):
    text = (
        "⚡ <b>AmneziaWG (WARP) Generator</b> ⚡\n\n"
        "Этот бот создаст индивидуальный профиль для обхода блокировок и ускорения YouTube / Roblox.\n\n"
        "👇 <b>Выберите страну для подключения:</b>"
    )
    await message.answer(text, reply_markup=get_country_keyboard(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("gen_"))
async def generate_warp_callback(callback: CallbackQuery):
    country_code = callback.data.split("_")[1]
    country_name = COUNTRY_ENDPOINTS.get(country_code, {}).get("name", "выбранную страну")

    await callback.answer(f"⏳ Генерирую конфиг ({country_name})...", show_alert=False)
    
    # Редактируем сообщение, пока идет генерация
    await callback.message.edit_text(
        f"🔄 <b>Запрос к Cloudflare API...</b>\nПожалуйста, подождите 3–5 секунд.",
        parse_mode=ParseMode.HTML
    )

    # Исправленный асинхронный вызов
    warp_data = await register_warp_account(country_code)

    if not warp_data:
        await callback.message.edit_text(
            "❌ <b>Ошибка при генерации!</b>\n\nНе удалось зарегистрировать профиль. Попробуйте ещё раз через команду /warp.",
            parse_mode=ParseMode.HTML
        )
        return

    config_content = build_amnezia_wg_config(warp_data)
    file_bytes = config_content.encode("utf-8")
    input_file = BufferedInputFile(file_bytes, filename=f"AmneziaWG_{country_code.upper()}.conf")

    # Удаляем служебное сообщение и отправляем файл
    await callback.message.delete()
    
    caption_text = (
        f"✅ <b>Конфигурация готова!</b>\n\n"
        f"📍 <b>Локация:</b> {warp_data['country_name']}\n"
        f"🛡️ <b>Протокол:</b> AmneziaWG (DPI Protection)\n"
        f"💡 <b>Инструкция:</b>\n"
        f"1. Скачайте файл ниже.\n"
        f"2. Импортируйте его в приложение <b>AmneziaWG</b>.\n"
        f"3. Включите подключение и проверяйте YouTube!\n\n"
        f"🔄 Для повторной генерации используйте /warp"
    )

    await callback.message.answer_document(
        document=input_file,
        caption=caption_text,
        parse_mode=ParseMode.HTML
    )

async def main():
    if not TOKEN:
        print("Ошибка: Переменная BOT_TOKEN не найдена!")
        return
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
