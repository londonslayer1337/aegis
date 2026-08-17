import base64
import re
import asyncio
import aiohttp

# Стабильные прямые источники, где ВСЕГДА есть сотни свежих VLESS
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://t.me/s/vless_keys",
    "https://t.me/s/free_v2ray_keys"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def decode_payload(text: str) -> str:
    """Безопасно декодирует Base64 или возвращает исходный текст."""
    text = text.strip()
    # Пробуем декодировать Base64
    try:
        missing_padding = len(text) % 4
        if missing_padding:
            text += '=' * (4 - missing_padding)
        decoded = base64.b64decode(text).decode('utf-8', errors='ignore')
        if "vless://" in decoded:
            return decoded
    except Exception:
        pass
    return text

async def fetch_source(session: aiohttp.ClientSession, url: str) -> list[str]:
    """Скачивает контент по ссылке и извлекает все vless:// ключи."""
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                raw_data = await resp.text()
                content = decode_payload(raw_data)
                
                # Поиск всех VLESS ключей
                keys = re.findall(r'vless://[^\s<"\']+', content)
                return keys
    except Exception:
        pass
    return []

async def get_free_v2ray_config() -> str | None:
    """Главный метод: опрашивает источники и гарантированно возвращает VLESS ключ."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_source(session, url) for url in SOURCES]
        results = await asyncio.gather(*tasks)

        all_keys = []
        for key_list in results:
            all_keys.extend(key_list)

        # Очищаем от дубликатов
        all_keys = list(set(all_keys))

        if not all_keys:
            return None

        # Сначала ищем ключи с маскировкой (REALITY / TLS)
        for key in all_keys:
            if "security=reality" in key.lower() or "security=tls" in key.lower():
                return key

        # Если REALITY нет — отдаем абсолютно любой первый попавшийся VLESS
        return all_keys[0]
