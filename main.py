import os
import io
import telebot
from telebot import types
import qrcode

# ==========================================
# ⚙️ НАСТРОЙКИ
# ==========================================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
# Сюда вставь свой готовый конфиг Amnezia/WireGuard
AMNEZIA_CONFIG = "amnezia://ВАШ_КОНФИГ_ЗДЕСЬ_ДЛИННАЯ_СТРОКА"

bot = telebot.TeleBot(BOT_TOKEN)

# Настройка команд
bot.set_my_commands([
    types.BotCommand("/start", "Запуск бота"),
    types.BotCommand("/config", "Получить конфиг"),
    types.BotCommand("/help", "Как настроить Amnezia")
])

# ==========================================
# 🛠️ ФУНКЦИИ
# ==========================================
def generate_qr(data):
    qr = qrcode.make(data)
    bio = io.BytesIO()
    bio.name = 'amnezia.png'
    qr.save(bio, 'PNG')
    bio.seek(0)
    return bio

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔑 Получить конфиг", callback_data="get_config"),
        types.InlineKeyboardButton("📘 Инструкция по установке", callback_data="get_help")
    )
    return markup

# ==========================================
# 🚀 ОБРАБОТЧИКИ
# ==========================================
@bot.message_handler(commands=['start', 'config', 'help'])
def handle_commands(message):
    if message.text == '/help':
        get_help(message)
    else:
        bot.send_message(
            message.chat.id,
            "<b>🛡️ Aegis Amnezia Proxy</b>\n\n"
            "Ваш защищенный доступ к сети одним нажатием.",
            parse_mode="HTML",
            reply_markup=get_main_markup()
        )

def get_help(message):
    text = (
        "<b>📘 Настройка Amnezia VPN:</b>\n\n"
        "1. Скопируйте конфиг из раздела «Получить конфиг».\n"
        "2. Откройте приложение <b>Amnezia VPN</b>.\n"
        "3. Выберите «Настроить свой сервер» -> «Использовать ключ/QR».\n"
        "4. Вставьте скопированный текст."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    ))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == "main_menu":
        bot.edit_message_text("<b>🛡️ Aegis Amnezia Proxy</b>", chat_id, call.message.message_id, 
                              parse_mode="HTML", reply_markup=get_main_markup())
        
    elif call.data == "get_help":
        get_help(call.message)
        
    elif call.data == "get_config":
        caption = (
            "<b>⚡ Ваш AmneziaWG Конфиг:</b>\n\n"
            "<code>" + AMNEZIA_CONFIG + "</code>\n\n"
            "<i>(Просто нажми на текст выше, чтобы скопировать)</i>"
        )
        bot.send_photo(chat_id, generate_qr(AMNEZIA_CONFIG), caption=caption, parse_mode="HTML", 
                       reply_markup=types.InlineKeyboardMarkup().add(
                           types.InlineKeyboardButton("⬅️ В главное меню", callback_data="main_menu")))

if __name__ == '__main__':
    bot.infinity_polling()
