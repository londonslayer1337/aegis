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

# База серверов с реальными/валидными структурами REALITY
# Важно: pbk должен быть валидным 43-символьным base64url ключом
SERVERS = {
    "nl": {
        "name": "🇳🇱 Нидерланды (Амстердам)",
        "ip": "185.220.100.1",
        "port": 443,
        "pbk": "1234567890123456789012345678901234567890123",  # 43-символьный тестовый ключ
        "sni": "yahoo.com"
    },
    "de": {
        "name": "🇩🇪 Германия (Франкфурт)",
        "ip": "185.220.100.2",
        "port": 443,
        "pbk": "1234567890123456789012345678901234567890123",
        "sni": "www.google.com"
    },
    "fi": {
        "name": "🇫🇮 Финляндия (Хельсинки)",
        "ip": "185.220.100.3",
        "port": 443,
        "pbk": "1234567890123456789012345678901234567890123",
        "sni": "www.microsoft.com"
    }
}

AMNEZIA_SECRET = "amnezia://config-template-data-here"

# ==========================================
# 🛠️ ГЕНЕРАТОРЫ КОНФИГУРАЦИЙ И QR
# ==========================================
def generate_vless_config(server_key):
    """Генерирует валидную VLESS/REALITY ссылку с гарантированным UUID"""
    srv = SERVERS.get(server_key, SERVERS["nl"])
    user_uuid = str(uuid.uuid4())
    
    # Формируем VLESS ссылку без лишних спецсимволов в хеше
    vless_link = (
        f"vless://{user_uuid}@{srv['ip']}:{srv['port']}"
        f"?type=tcp&security=reality&pbk={srv['pbk']}&fp=chrome"
        f"&sni={srv['sni']}&sid=12345678&spx=%2F#Aegis_{server_key.upper()}"
    )
    return vless_link, user_uuid, srv['name']

def generate_qr_code(data_string):
    """Генерация QR-кода в BytesIO без сохранения на диск"""
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
    btn_vless = types.InlineKeyboardButton("🌐 Выбор локации VLESS / REALITY", callback_data="menu_countries")
    btn_amnezia = types.InlineKeyboardButton("⚡ Amnezia WG / AWG", callback_data="get_amnezia")
    btn_help = types.InlineKeyboardButton("❓ Инструкция по настройке", callback_data="get_help")
    markup.add(btn_vless, btn_amnezia, btn_help)
    return markup

def get_countries_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for code, data in SERVERS.items():
        markup.add(types.InlineKeyboardButton(data["name"], callback_data=f"get_vless_{code}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))
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
        "Выберите нужный раздел ниже:"
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

    elif call.data == "menu_countries":
        text = "<b>🌐 Выберите страну сервера:</b>\n\nВсе локации поддерживают протокол REALITY."
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=get_countries_keyboard()
            )
        except Exception:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_countries_keyboard())

    elif call.data.startswith("get_vless_"):
        server_code = call.data.replace("get_vless_", "")
        vless_link, user_uuid, country_name = generate_vless_config(server_code)
        qr_file = generate_qr_code(vless_link)

        caption = (
            f"<b>🛡️ Конфигурация VLESS / REALITY ({country_name})</b>\n\n"
            "<b>Ключ подключения:</b>\n"
            f"<code>{vless_link}</code>\n\n"
            f"<b>Ваш UUID:</b> <code>{user_uuid}</code>\n\n"
            "<b>📱 Быстрая установка (Happ / v2raytun):</b>\n"
            "1. Нажмите на текст ключа выше, чтобы скопировать.\n"
            "2. Откройте <b>Happ</b> или <b>v2raytun</b>.\n"
            "3. Нажмите <b>+</b> ➔ <b>Импорт из буфера обмена</b>.\n"
            "4. Или отсканируйте QR-код прямо из приложения!"
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
            "Скопируйте VLESS-ключ в боте, откройте Happ и нажмите иконку плюса в верхнем углу.\n\n"
            "<b>2. Приложение v2raytun:</b>\n"
            "Отличная альтернатива для Android. Вставляется через кнопку «Импорт из буфера».\n\n"
            "<b>3. Amnezia VPN:</b>\n"
            "Подходит для ПК и смартфонов. Поддерживает протоколы обхода блокировок."
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
    print("🛡️ Aegis Proxy Bot запущен!")
    bot.infinity_polling()
