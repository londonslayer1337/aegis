import os
import io
import uuid
import telebot
from telebot import types
import qrcode

# ==========================================
# ⚙️ НАСТРОЙКИ И ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ==========================================
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ Ошибка: Переменная BOT_TOKEN не найдена в окружении!")

bot = telebot.TeleBot(BOT_TOKEN)

# Данные вашего сервера (замените при необходимости на реальные)
SERVER_IP = "185.220.100.1"
SERVER_PORT = 443
REALITY_PUBLIC_KEY = "YourPublicKeyHere1234567890abcdef"
SNI_DOMAIN = "yahoo.com"
AMNEZIA_SECRET = "amnezia://config-template-data-here"

# ==========================================
# 🛠️ ГЕНЕРАТОРЫ КОНФИГУРАЦИЙ И QR-КОДОВ
# ==========================================
def generate_vless_config():
    """Генерирует валидную VLESS/REALITY ссылку со случайным UUID"""
    user_uuid = str(uuid.uuid4())
    vless_link = (
        f"vless://{user_uuid}@{SERVER_IP}:{SERVER_PORT}"
        f"?type=tcp&security=reality&pbk={REALITY_PUBLIC_KEY}&fp=chrome"
        f"&sni={SNI_DOMAIN}&sid=12345678&spx=%2F#Aegis_Proxy_VLESS"
    )
    return vless_link, user_uuid

def generate_qr_code(data_string):
    """Создает QR-код в оперативной памяти и возвращает BytesIO объект"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ==========================================
# 🎹 КЛАВИАТУРЫ И МЕНЮ
# ==========================================
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_vless = types.InlineKeyboardButton("🛡️ VLESS / REALITY (Happ / v2raytun)", callback_data="get_vless")
    btn_amnezia = types.InlineKeyboardButton("⚡ Amnezia WG / AWG", callback_data="get_amnezia")
    btn_help = types.InlineKeyboardButton("❓ Инструкция по настройке", callback_data="get_help")
    markup.add(btn_vless, btn_amnezia, btn_help)
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu")
    markup.add(btn_back)
    return markup

# ==========================================
# 🚀 ОБРАБОТЧИКИ КОМАНД И НАВИГАЦИИ
# ==========================================
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    welcome_text = (
        "<b>🛡️ Aegis Proxy — Система Защищенного Доступа</b>\n\n"
        "Добро пожаловать! Бот предоставляет персональные, отказоустойчивые "
        "конфигурации для обхода сетевых ограничений.\n\n"
        "<b>Доступные протоколы:</b>\n"
        "• <code>VLESS-REALITY</code> — маскировка под обычный HTTPS-трафик (для Happ / v2raytun)\n"
        "• <code>AmneziaWG</code> — устойчивый протокол против маскировочных блокировок\n\n"
        "Выберите нужный протокол ниже:"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "main_menu":
        text = "<b>🛡️ Главное меню Aegis Proxy:</b>\n\nВыберите нужный раздел:"
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        except Exception:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif call.data == "get_vless":
        vless_link, user_uuid = generate_vless_config()
        qr_file = generate_qr_code(vless_link)

        caption = (
            "<b>🛡️ Конфигурация VLESS / REALITY</b>\n\n"
            "<b>Ключ подключения:</b>\n"
            f"<code>{vless_link}</code>\n\n"
            f"<b>Ваш UUID:</b> <code>{user_uuid}</code>\n\n"
            "<b>📱 Быстрая установка (Happ / v2raytun):</b>\n"
            "1. Нажмите на текст ключа выше, чтобы скопировать.\n"
            "2. Откройте <b>Happ</b> или <b>v2raytun</b>.\n"
            "3. Нажмите <b>+</b> ➔ <b>Импорт из буфера обмена</b> (Import from Clipboard).\n"
            "4. Или просто отсканируйте QR-код выше прямо из приложения!"
        )

        bot.delete_message(chat_id, message_id)
        bot.send_photo(
            chat_id=chat_id,
            photo=qr_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )

    elif call.data == "get_amnezia":
        qr_file = generate_qr_code(AMNEZIA_SECRET)

        caption = (
            "<b>⚡ Конфигурация AmneziaWG</b>\n\n"
            "<b>Ключ / Конфиг:</b>\n"
            f"<code>{AMNEZIA_SECRET}</code>\n\n"
            "<b>📱 Установка в Amnezia VPN:</b>\n"
            "1. Скопируйте ключ или сохраните QR-код.\n"
            "2. Откройте приложение <b>Amnezia VPN</b>.\n"
            "3. Выберите <i>«Настроить свой сервер»</i> ➔ <i>«Использовать ключ / QR-код»</i>."
        )

        bot.delete_message(chat_id, message_id)
        bot.send_photo(
            chat_id=chat_id,
            photo=qr_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )

    elif call.data == "get_help":
        help_text = (
            "<b>❓ Справка по настройке клиентов</b>\n\n"
            "<b>1. Приложение Happ (Рекомендуется для iOS / Android):</b>\n"
            "Скачайте Happ из App Store или Google Play. Скопируйте VLESS-ключ в боте, "
            "зайдите в приложение и нажмите иконку плюса в верхнем углу.\n\n"
            "<b>2. Приложение v2raytun:</b>\n"
            "Отличная альтернатива для Android. Вставляется через кнопку «Импорт из буфера».\n\n"
            "<b>3. Amnezia VPN:</b>\n"
            "Подходит для ПК (Windows/macOS) и смартфонов. Поддерживает протоколы обхода глубокого анализа трафика (DPI)."
        )
        
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=help_text,
                parse_mode="HTML",
                reply_markup=get_back_keyboard()
            )
        except Exception:
            bot.send_message(chat_id, help_text, parse_mode="HTML", reply_markup=get_back_keyboard())

# ==========================================
# 🟢 ТОЧКА ВХОДА
# ==========================================
if __name__ == '__main__':
    print("🛡️ Aegis Proxy Bot запущен! UUID генерируется корректно.")
    bot.infinity_polling()
