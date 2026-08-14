import telebot
from telebot import types
import qrcode
from io import BytesIO
import uuid
import os

# Безопасное получение токена из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Бессрочные шаблоны узлов для разных стран и клиентов (Amnezia, Happ, v2raytun, v2rayNG и др.)
BASE_CONFIGS = {
    "germany": {
        "name": "🇩🇪 Германия (Aegis DE - Low Ping)",
        "vless_template": "vless://{user_uuid}@de-aegis.freevless.net:443?security=reality&encryption=none&pbk=KEY_DE&type=tcp&sni=microsoft.com#Aegis-Germany-🇩🇪",
        "amnezia_template": "vpn://de-aegis.freevless.net/awg?key={user_uuid}"
    },
    "netherlands": {
        "name": "🇳🇱 Нидерланды (Aegis NL - High Speed)",
        "vless_template": "vless://{user_uuid}@nl-aegis.freevless.net:443?security=reality&encryption=none&pbk=KEY_NL&type=tcp&sni=microsoft.com#Aegis-Netherlands-🇳🇱",
        "amnezia_template": "vpn://nl-aegis.freevless.net/awg?key={user_uuid}"
    },
    "usa": {
        "name": "🇺🇸 США (Aegis US - US Regional)",
        "vless_template": "vless://{user_uuid}@us-aegis.freevless.net:443?security=reality&encryption=none&pbk=KEY_US&type=tcp&sni=microsoft.com#Aegis-USA-🇺🇸",
        "amnezia_template": "vpn://us-aegis.freevless.net/awg?key={user_uuid}"
    },
    "japan": {
        "name": "🇯🇵 Япония (Aegis JP - Asia Pacific)",
        "vless_template": "vless://{user_uuid}@jp-aegis.freevless.net:443?security=reality&encryption=none&pbk=KEY_JP&type=tcp&sni=microsoft.com#Aegis-Japan-🇯🇵",
        "amnezia_template": "vpn://jp-aegis.freevless.net/awg?key={user_uuid}"
    }
}

bot = telebot.TeleBot(BOT_TOKEN)

# Генерация уникального бессрочного VLESS-ключа
def generate_vless(country_key):
    unique_id = str(uuid.uuid4())
    template = BASE_CONFIGS[country_key]["vless_template"]
    return template.format(user_uuid=unique_id)

# Генерация уникального ключа для Amnezia
def generate_amnezia(country_key):
    unique_id = str(uuid.uuid4())
    template = BASE_CONFIGS[country_key]["amnezia_template"]
    return template.format(user_uuid=unique_id)

# Генератор QR-кода в оперативной памяти
def generate_qr(data_string):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = BytesIO()
    bio.name = 'aegis_qr.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# Главное меню с обновленным оформлением
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn_locations = types.InlineKeyboardButton("🌍 Выбрать локацию (IP)", callback_data="show_locations")
    btn_apps = types.InlineKeyboardButton("📲 Совместимые клиенты", callback_data="show_apps")
    btn_mobile = types.InlineKeyboardButton("📱 Инструкция: Смартфон", callback_data="info_mobile")
    btn_pc = types.InlineKeyboardButton("💻 Инструкция: ПК", callback_data="info_pc")
    keyboard.add(btn_locations, btn_apps, btn_mobile, btn_pc)
    return keyboard

# Меню выбора стран
def get_countries_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for code, data in BASE_CONFIGS.items():
        btn = types.InlineKeyboardButton(data["name"], callback_data=f"get_{code}")
        keyboard.add(btn)
        
    btn_back = types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="main_menu")
    keyboard.add(btn_back)
    return keyboard

# Команда /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    welcome_text = (
        "🌌 **Aegis Proxy** | *Roblox Network Gateway*\n"
        "───────────────────────────────\n\n"
        "👋 **Добро пожаловать в Aegis Proxy!**\n\n"
        "Твой надежный персональный щит от блокировок, высокого пинга и ограничений чата.\n\n"
        "⚡ **Главные преимущества:**\n"
        "• 🇩🇪🇳🇱🇺🇸🇯🇵 Доступ к 4 ключевым регионам\n"
        "• 🎙 Полный доступ к голосовому и текстовому чату Roblox\n"
        "• 🚀 Высокая скорость для YouTube (4K) и Telegram\n"
        "• ♾ Бессрочные VLESS (Reality) и Amnezia ключи\n\n"
        "Выбери раздел в меню ниже, чтобы начать:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Обработчик инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    bot.answer_callback_query(call.id)
    
    if call.data == "main_menu":
        text = (
            "🛡️ **Aegis Proxy — Главное меню**\n"
            "───────────────────────────────\n"
            "Выбери нужный раздел для настройки подключения:"
        )
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif call.data == "show_locations":
        text = (
            "🌍 **Выбор узловой локации**\n"
            "───────────────────────────────\n"
            "Выбери оптимальный сервер для твоих задач:\n\n"
            "• **🇩🇪 Германия / 🇳🇱 Нидерланды**\n"
            "  └ *Минимальный пинг, идеально для игр и YouTube*\n\n"
            "• **🇺🇸 США / 🇯🇵 Япония**\n"
            "  └ *Доступ к региональным серверам Roblox*"
        )
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_countries_keyboard()
        )

    # Выдача бессрочного ключа и QR-кода
    elif call.data.startswith("get_"):
        country_code = call.data.split("_")[1]
        
        if country_code in BASE_CONFIGS:
            country_info = BASE_CONFIGS[country_code]
            vless_key = generate_vless(country_code)
            amnezia_key = generate_amnezia(country_code)
            
            qr_file = generate_qr(vless_key)
            
            caption = (
                f"🛡️ **{country_info['name']}**\n"
                "───────────────────────────────\n"
                "✨ *Конфигурация успешно сгенерирована!*\n\n"
                "📲 **Для Happ / v2raytun / v2rayNG / Streisand:**\n"
                "Отсканируй QR-код выше или нажми на VLESS-ключ для копирования:\n"
                f"`{vless_key}`\n\n"
                "🛡️ **Для Amnezia VPN:**\n"
                "Нажми на ссылку для копирования:\n"
                f"`{amnezia_key}`\n"
                "───────────────────────────────\n"
                "💡 *Скопированный ключ вставляется в приложение в 1 клик.*"
            )
            
            bot.send_photo(
                call.message.chat.id, 
                photo=qr_file, 
                caption=caption, 
                parse_mode="Markdown", 
                reply_markup=get_countries_keyboard()
            )

    elif call.data == "show_apps":
        text = (
            "📲 **Поддерживаемые приложения**\n"
            "───────────────────────────────\n"
            "1. **Happ** *(iOS / Android)* — быстрая работа с VLESS по QR и ссылкам.\n"
            "2. **v2raytun** *(Android / iOS)* — лаконичный клиент с поддержкой VLESS-Reality.\n"
            "3. **Amnezia VPN** *(Android / iOS / PC)* — поддержка ключей `vpn://`.\n"
            "4. **v2rayNG** *(Android)* / **Streisand** *(iOS)* / **NekoBox** *(PC)*."
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "info_mobile":
        text = (
            "📱 **Быстрый старт на смартфоне**\n"
            "───────────────────────────────\n"
            "1. Установи **Happ**, **v2raytun** или **Amnezia VPN**.\n"
            "2. В боте выбери страну и нажми на ключ (он скопируется в буфер).\n"
            "3. В приложении нажми **«+» ➔ «Импорт из буфера»** (или отсканируй QR-код).\n"
            "4. Запусти подключение и играй без ограничений!"
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "info_pc":
        text = (
            "💻 **Быстрый старт на ПК**\n"
            "───────────────────────────────\n"
            "1. Установи **NekoBox**, **v2rayN** или **Amnezia VPN**.\n"
            "2. Скопируй VLESS или Amnezia ключ из бота.\n"
            "3. В программе нажмите комбинацию **`Ctrl + V`**.\n"
            "4. Активируйте режим **System Proxy**."
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

if __name__ == '__main__':
    print("🛡️ Aegis Proxy Bot запущен!")
    bot.infinity_polling()
