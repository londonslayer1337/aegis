import base64
import random
import httpx
import re
import asyncio
from urllib.parse import urlparse

# Источники с частым обновлением ключей
VLESS_SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/mft00/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/v2raywg/v2ray/main/v2ray"
]

COUNTRY_PATTERNS = {
    "de": [r"germany", r"de", r"🇩🇪", r"германия"],
    "nl": [r"netherlands", r"dutch", r"nl", r"🇳🇱", r"нидерланды"],
    "us": [r"united states", r"usa", r"us", r"🇺🇸", r"сша"],
    "jp": [r"japan", r"jp", r"🇯🇵", r"япония"]
}

def parse_host_and_port(key: str) -> tuple[str | None, int | None]:
    """Извлекает IP/домен и порт из VLESS, VMess, Trojan, SS ссылок."""
    try:
        if key.startswith("vmess://"):
            # VMess ключи обычно запакованы в base64 json
            b64_data = key.replace("vmess://", "")
            # Добавляем паддинг
            b64_data += "=" * ((4 - len(b64_data) % 4) % 4)
            decoded = base64.b64decode(b64_data).decode('utf-8', errors='ignore')
            import json
            data = json.loads(decoded)
            return data.get("add"), int(data.get("port", 443))
        else:
            # Для vless://, trojan://, ss://
            parsed = urlparse(key)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme in ["vless", "trojan"] else 80)
            return host, port
    except Exception:
        return None, None

async def check_node_alive(host: str, port: int, timeout: float = 2.5) -> bool:
    """Проверяет доступность сервера через TCP-подключение."""
    if not host or not port:
        return False
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), 
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def fetch_all_keys() -> list[str]:
    all_keys = []
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        for url in VLESS_SUBSCRIPTION_URLS:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                
                raw_text = response.text.strip()
                try:
                    decoded = base64.b64decode(raw_text).decode('utf-8', errors='ignore')
                except Exception:
                    decoded = raw_text

                lines = [line.strip() for line in decoded.splitlines() if line.strip()]
                valid_keys = [
                    k for k in lines 
                    if k.startswith(("vless://", "vmess://", "trojan://", "ss://"))
                ]
                all_keys.extend(valid_keys)
            except Exception as e:
                print(f"[ERROR] VLESS Scraper: {e}")
                continue
    return all_keys

async def get_free_v2ray_config(country_code: str = None) -> str | None:
    """Отбирает ключи и проверяет их доступность перед выдачей."""
    keys = await fetch_all_keys()
    if not keys:
        return None

    # Фильтрация по стране, если передана
    candidate_keys = []
    if country_code and country_code in COUNTRY_PATTERNS:
        patterns = COUNTRY_PATTERNS[country_code]
        for key in keys:
            hashtag = key.split("#")[-1].lower() if "#" in key else ""
            for pattern in patterns:
                if re.search(pattern, hashtag, re.IGNORECASE):
                    candidate_keys.append(key)
                    break

    if not candidate_keys:
        candidate_keys = keys

    # Перемешиваем и проверяем случайные ключи на живой TCP-сокет
    random.shuffle(candidate_keys)
    
    # Проверяем первые 15 кандидатов, чтобы не заставлять пользователя долго ждать
    for key in candidate_keys[:15]:
        host, port = parse_host_and_port(key)
        if host and port:
            is_alive = await check_node_alive(host, port)
            if is_alive:
                return key

    # Если среди проверенных никто не ответил, возвращаем случайный из кандидатов
    return random.choice(candidate_keys) if candidate_key
    s else None
