import base64
import re
import asyncio
import aiohttp

# Источники, специализирующиеся на VLESS-REALITY и обходе блокировок
AGGREGATOR_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/morteza-f/v2ray-collector/main/configs/vless.txt"
]

async def fetch_and_decode(session: aiohttp.ClientSession, url: str) -> list[str]:
    """Скачивает и декодирует подписки."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
            if resp.status == 200:
                text = await resp.text()
                # Если подписка зашифрована в Base64 — декодируем
                try:
                    decoded = base64.b64decode(text.strip()).decode('utf-8', errors='ignore')
                except Exception:
                    decoded = text
                
                # Находим все vless:// ключи
                keys = re.findall(r'vless://[^\s<"\']+', decoded)
                return keys
    except Exception:
        pass
    return []

def is_anti_blocking_key(vless_key: str) -> bool:
    """
    Проверяет, содержит ли ключ параметры защиты от блокировок DPI
    (REALITY, gRPC, WebSocket с правильным маскировочным SNI).
    """
    key_lower = vless_key.lower()
    
    # Игнорируем устаревшие и легко блокируемые варианты (обычный TCP без TLS)
    if "security=none" in key_lower:
        return False
        
    # Приоритет для REALITY и защищенных TLS-соединений
    if "security=reality" in key_lower or "security=tls" in key_lower:
        return True
        
    return False

async def get_free_v2ray_config() -> str | None:
    """Собирает самые стойкие VLESS-REALITY ключи для Happ."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_decode(session, url) for url in AGGREGATOR_SOURCES]
        results = await asyncio.gather(*tasks)

        all_keys = []
        for res in results:
            all_keys.extend(res)

        # Убираем дубликаты
        all_keys = list(set(all_keys))

        if not all_keys:
            return None

        # Отбираем только ключи с защитой от DPI (REALITY/TLS)
        robust_keys = [k for k in all_keys if is_anti_blocking_key(k)]

        if robust_keys:
            # Возвращаем самый свежий валидный ключ из начала списка
            return robust_keys[0]
            
        # Если REALITY не найдено, отдаем любой имеющийся VLESS
        if all_keys:
            return all_keys[0]
            
        return None
