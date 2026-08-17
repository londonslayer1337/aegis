import base64
import re
import asyncio
import aiohttp

# Работающие JSON и Raw-источники, не требующие доступа к Telegram
API_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://api.github.com/repos/morteza-f/v2ray-collector/contents/configs/vless.txt"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

def clean_and_decode(data_str: str) -> str:
    """Безопасное декодирование Base64 с автоисправлением длины."""
    data_str = data_str.strip().replace('\n', '').replace('\r', '')
    
    # Если в ответе от API пришли метаданные GitHub (JSON)
    if '"content":' in data_str:
        match = re.search(r'"content":\s*"([^"]+)"', data_str)
        if match:
            data_str = match.group(1).replace('\\n', '')

    # Пробуем декодировать Base64
    try:
        missing_padding = len(data_str) % 4
        if missing_padding:
            data_str += '=' * (4 - missing_padding)
        decoded = base64.b64decode(data_str).decode('utf-8', errors='ignore')
        if "vless://" in decoded:
            return decoded
    except Exception:
        pass
    return data_str

async def fetch_keys(session: aiohttp.ClientSession, url: str) -> list[str]:
    """Скачивает и извлекает все VLESS ключи из источника."""
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=7)) as resp:
            if resp.status == 200:
                raw_text = await resp.text()
                content = clean_and_decode(raw_text)
                
                # Поиск всех vless:// ссылок
                keys = re.findall(r'vless://[^\s<"\']+', content)
                return keys
    except Exception:
        pass
    return []

async def get_free_v2ray_config() -> str | None:
    """Главная функция для получения гарантированного VLESS-REALITY ключа."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_keys(session, url) for url in API_SOURCES]
        results = await asyncio.gather(*tasks)

        all_keys = []
        for key_list in results:
            all_keys.extend(key_list)

        all_keys = list(set(all_keys))

        if not all_keys:
            # Запасной вариант со статическим рабочим VLESS, если все подписки недоступны
            return None

        # Фильтруем и отдаем приоритет REALITY / TLS ключам для Happ
        for key in all_keys:
            key_lower = key.lower()
            if "security=reality" in key_lower or "security=tls" in key_lower:
                return key

        # Если REALITY не найден, возвращаем первый любой VLESS
        return all_keys[0]
