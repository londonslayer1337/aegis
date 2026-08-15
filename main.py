import asyncio
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, BotCommand
from aiogram.filters import CommandStart, Command

from warp_generator import register_warp_account, build_amnezia_wg_config
from v2ray_generator import get_free_v2ray_config

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Получить AmneziaWG (WARP)", callback_data="get_warp")],
        [InlineKeyboardButton(text="⚡ Получить VLESS / Happ ключ", callback_data="get_vless")]
    ])

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню / Перезапуск"),
        BotCommand(command="vless", description="Получить свежий VLESS ключ")
    ]
    await bot.set_my_commands(commands)

@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 **Привет!** Выбери нужный тип VPN подключения:\n\n"
        "• **AmneziaWG**: Конфиг-файл для приложения AmneziaWG.\n"
        "• **VLESS / Happ**: Строка-ключ для приложений Happ, v2rayNG, NekoBox.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("vless"))
async def vless_cmd(message: Message):
    status_msg = await message.answer("🔎 Ищу рабочий VLESS ключ...")
    key = await get_free_v2ray_config()
    
    if key:
        msg = (
            "✅ **Твой VLESS / Xray ключ:**\n\n"
            f"`{key}`\n\n"
            "📌 **Инструкция:**\n"
            "1. Нажмите на ключ, чтобы скопировать.\n"
            "2. Откройте **Happ**, **v2rayNG** или **NekoBox**.\n"
            "3. Нажмите **Импорт из буфера обмена**."
        )
        await status_msg.edit_text(msg, parse_mode="Markdown")
    else:
        await status_msg.edit_text("❌ Не удалось получить ключ. Попробуйте еще раз позже.")

@router.callback_query(F.data == "get_warp")
async def handle_warp(callback: CallbackQuery):
    await callback.message.answer("⚙️ Генерирую AmneziaWG профиль...")
    
    warp_data = await register_warp_account("de")
    config_text = build_amnezia_wg_config(warp_data)
    
    file_bytes = config_text.encode("utf-8")
    input_file = BufferedInputFile(file_bytes, filename="AmneziaWARP.conf")
    
    await callback.message.answer_document(
        document=input_file,
        caption="✅ **Твой AmneziaWG конфиг готов!**\nИмпортируй файл в приложение AmneziaWG.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "get_vless")
async def handle_vless(callback: CallbackQuery):
    status_msg = await callback.message.answer("🔎 Ищу рабочий VLESS ключ...")
    key = await get_free_v2ray_config()
    
    if key:
        msg = (
            "✅ **Твой VLESS / Xray ключ:**\n\n"
            f"`{key}`\n\n"
            "📌 **Инструкция:**\n"
            "1. Нажмите на ключ, чтобы скопировать.\n"
            "2. Откройте **Happ**, **v2rayNG** или **NekoBox**.\n"
            "3. Нажмите **Импорт из буфера обмена**."
        )
        await status_msg.edit_text(msg, parse_mode="Markdown")
    else:
        await status_msg.edit_text("❌ Не удалось получить ключ. Попробуйте еще раз позже.")
        
    await callback.answer()

async def main():
    dp.include_router(router)
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
