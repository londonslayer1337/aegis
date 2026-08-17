import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

# Импортируем генератор подписок
from v2ray_generator import get_free_v2ray_config

# Берем токен из переменных окружения Railway/Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТЕЛЕГРАМ_ТОКЕН")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню управления ботом."""
    buttons = [
        [InlineKeyboardButton(text="⚡ Получить AmneziaWG (Файл)", callback_data="get_awg")],
        [InlineKeyboardButton(text="🌐 Получить VLESS (Подписка Happ)", callback_data="get_vless")],
        [InlineKeyboardButton(text="❓ Инструкция по настройке", callback_data="get_help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Приветственное сообщение."""
    await message.answer(
        "👋 **Привет!**\n\n"
        "Выбери нужный протокол ниже, чтобы получить бесплатную конфигурацию VPN:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "get_awg")
async def send_awg(callback: types.CallbackQuery):
    """Отправка AmneziaWG конфигурационного файла с твоим рабочим шаблоном."""
    await callback.answer("Готовлю файл...")
    
    # Твой основной рабочий шаблон AmneziaWG
    awg_config = """[Interface]
PrivateKey = wPbLOeUinrqiorXrdwX0TI1Q4lTwrRRM3i2tCcZ/tEg=
Address = 172.16.0.2, 2606:4700:110:86cb:4ac1:7a24:a574:85e1
DNS = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111, 2606:4700:4700::1001
MTU = 1280
Jc = 19
Jmin = 76
Jmax = 322
S1 = 0
S2 = 0
S3 = 0
S4 = 0
H1 = 1
H2 = 2
H3 = 3
H4 = 4
I1 = <b 0x000100602112a442ff28ec860ce31adf94cf190b80220006706a6e617468000000060015313839343237343137323a436d42325a3246795977000000002400047d73d4d4802a0008a3b15ee41d3ecabc00250000002600148972b9890cdb1001c1ce2f8be724c92ad8c88c1a802800045e24362a>

[Peer]
PublicKey = bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=
AllowedIPs = 0.0.0.0/0
Endpoint = engage.cloudflareclient.com:4500
PersistentKeepalive = 25"""

    # Формируем файл прямо в оперативной памяти
    file_bytes = awg_config.encode('utf-8')
    document = BufferedInputFile(file_bytes, filename="AmneziaWG_Free.conf")

    caption = (
        "⚡ **Твой конфигурационный файл AmneziaWG готов!**\n\n"
        "1. Скачай файл `.conf` ниже.\n"
        "2. Импортируй его в приложение **AmneziaWG**.\n"
        "3. Включи переключатель для защиты трафика."
    )
    
    await callback.message.answer_document(
        document=document,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "get_vless")
async def send_vless(callback: types.CallbackQuery):
    """Выдача авто-подписки VLESS для Happ/v2rayNG."""
    await callback.answer("Получаю актуальную подписку...")
    
    sub_url = await get_free_v2ray_config()
    
    text = (
        "🌐 **Твоя ссылка на авто-обновляемую подписку VLESS:**\n\n"
        f"`{sub_url}`\n\n"
        "📌 **Как добавить в Happ / v2rayNG:**\n"
        "1. Нажми на ссылку выше, чтобы скопировать её.\n"
        "2. Открой **Happ** ➔ нажми **`+`** в правом верхнем углу.\n"
        "3. Выбери **Add Subscription** (Добавить подписку) / **Import via URL**.\n"
        "4. Вставь ссылку, сохрани и нажми **Обновить (Update)**.\n\n"
        "🔄 *Приложение авто-обновляет список и само выбирает рабочий сервер.*"
    )
    
    await callback.message.answer(
        text=text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "get_help")
async def send_help(callback: types.CallbackQuery):
    """Раздел справки."""
    await callback.answer()
    
    help_text = (
        "📖 **Инструкция по выбору протокола:**\n\n"
        "🔹 **AmneziaWG**: Идеален для Android, iOS и ПК. Стойко обходит блокировки DPI на уровне провайдеров.\n\n"
        "🔹 **VLESS (Happ)**: Использует подписку с сотнями узлов. Если один сервер заблокируют, приложение автоматически переключит тебя на рабочий."
    )
    
    await callback.message.answer(
        text=help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def main():
    print("🚀 Бот успешно запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
