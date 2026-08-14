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

# Безопасная загрузка .env (для локального запуска)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    sys.exit("❌ ОШИБКА: Переменная BOT_TOKEN не найдена в окружении!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Красивая клавиатура выбора стран
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

# 1. Приветствие (/start и /warp)
@dp.message(CommandStart())
@dp.message(Command("warp"))
async def command_warp_handler(message: Message):
    text = (
        f"👋 Привет, <b>{html.quote(message.from_user.full_name)}</b>!\n\n"
        "⚡ <b>AmneziaWG Config Generator</b>\n"
        "------------------------------------\n"
        "Выбери желаемую <b>страну сервера</b> ниже, чтобы сгенерировать персональный `.conf` файл с защитой от DPI:"
    )
    await message.answer(text, reply_markup=get_country_keyboard(), parse_mode=ParseMode.HTML)

# 2. Подробная и красивая справка (/help)
@dp.message(Command("help"))
async def command_help_handler(message: Message):
    help_text = (
        "📖 <b>Справка по использованию бота</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>1️⃣ Как получить конфиг?</b>\n"
        "• Нажмите /warp или /start.\n"
        "• Выберите нужную локацию (🇩🇪, 🇳🇱, 🇺🇸, 🇯🇵).\n"
        "• Бот моментально пришлёт файл <code>.conf</code>.\n\n"
        "<b>2️⃣ Как подключить в AmneziaWG?</b>\n"
        "• Установите приложение <b>AmneziaWG</b> (iOS / Android / Windows / macOS).\n"
        "• Сохраните присланный файл в память устройства.\n"
        "• Откройте приложение ➔ <b>«Добавить тоннель»</b> ➔ <b>«Импорт из файла»</b>.\n"
        "• Выберите полученный <code>.conf</code> файл и включите туннель!\n\n"
        "<b>3️⃣ В чём плюс AmneziaWG?</b>\n"
        "• В конфиг встроен обфусцированный заголовок (параметры <code>Jc</code>, <code>H1-H4</code>), "
        "который делает WireGuard-трафик невидимым для систем блокировки (DPI)."
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)

# 3. Быстрый обработчик кнопок с красивым выводом
@dp.callback_query(F.data.startswith("geo_"))
async def generate_warp_callback(callback: CallbackQuery):
    # Мгновенный отклик на нажатие (гасим загрузку кнопки)
    await callback.answer("⏳ Создаю конфигурацию...")

    country_code = callback.data.split("_")[1]
    
    # Красивый статус генерации
    status_msg = await callback.message.answer(
        "⚡ <b>Генерация AmneziaWG ключа...</b>\n"
        "<i>Регистрируем профиль в Cloudflare и настраиваем маскировку...</i>", 
        parse_mode=ParseMode.HTML
    )

    # Генерация в фоновом потоке без блокировки бота
    warp_data = await asyncio.to_thread(register_warp_account, country_code)

    if not warp_data:
        await status_msg.edit_text(
            "❌ <b>Ошибка генерации!</b>\n"
            "Не удалось связаться с сервером. Попробуйте еще раз через пару секунд.", 
            parse_mode=ParseMode.HTML
        )
        return

    config_content = build_amnezia_wg_config(warp_data)
    
    # Сборка файла в оперативной памяти (без диск-I/O)
    file_bytes = config_content.encode("utf-8")
    filename = f"Amnezia_{country_code.upper()}_{callback.from_user.id}.conf"
    input_file = BufferedInputFile(file_bytes, filename=filename)

    # Удаляем сообщение о загрузке и отправляем результат
    await status_msg.delete()
    
    caption_text = (
        f"✅ <b>Конфигурация успешно готова!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Локация:</b> {warp_data['country_name']}\n"
        f"🌐 <b>Эндпоинт:</b> <code>{warp_data['endpoint']}</code>\n"
        f"🛡️ <b>Протокол:</b> AmneziaWG (Anti-DPI)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📥 <i>Скачайте файл выше и импортируйте его в приложение <b>AmneziaWG</b>.</i>"
    )

    await callback.message.answer_document(
        document=input_file,
        caption=caption_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_country_keyboard()
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("🚀 Бот запущен на Railway! Оформление и обработка кнопок обновлены.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

main())
