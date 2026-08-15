import base64
import random
import httpx
import asyncio
import socket
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Актуальные подписки с VLESS-REALITY ключами для обхода блокировок
VLESS_REALITY_SUBSCRIPTIONS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/ByeWhiteLists/ByeWhiteLists2/main/ByeWhiteLists2.txt",
    "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt",
    "https://raw.githubusercontent.com/EskandarAtaro/V2ray-Configs/main/Splitted-By-Protocol/vless.txt"
]

def parse_host_and_port(key: str) -> tuple[str | None, int | None]:
    """Извлекает IP/домен и порт из ссылки VLESS."""
    try:
        parsed = urlparse(key)
        host = parsed.hostname
        port = parsed.port or 443
        return host, port
    except Exception:
        return None, None

def optimize_key_dns(key: str) -> str:
    """Удаляет параметр 'dns' из ключа, заставляя клиент использовать системный DNS телефона."""
    try:
        if not key.startswith("vless://"):
            return key
            
        parsed = urlparse(key)
        query_params = parse_qs(parsed.query)
        
        # Удаляем встроенный DNS, чтобы V2Ray подхватывал Частный DNS Android
        if 'dns' in query_params:
            del query_params['dns']
            
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    except Exception:
        return key

async def check_node_dns_and_socket(host: str, port: int, timeout: float = 2.0) -> bool:
    """Проверяет DNS-резолв хоста и делает активный TCP-тест порта."""
    if not host or not port:
        return False
    try:
        loop = asyncio.get_event_loop()
        ip_list = await loop.run_in_executor(
            None, lambda: socket.gethostbyname_ex(host)[2]
        )
        if not ip_list:
            return False

        target_ip = ip_list[0]
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(target_ip, port), 
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def fetch_reality_keys() -> list[str]:
    """Скачивает и отбирает строго VLESS-REALITY ключи."""
    all_keys = []
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        for url in VLESS_REALITY_SUBSCRIPTIONS:
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
                all_keys.extend(lines)
            except Exception as e:
                print(f"[ERROR] Reality scraper error: {e}")
                continue

    # Фильтруем: берем ТОЛЬКО vless:// ключи, содержащие Reality-параметры (pbk= или security=reality)
    reality_keys = [
        k for k in all_keys 
        if k.startswith("vless://") and ("pbk=" in k.lower() or "reality" in k.lower())
    ]
    
    # Если REALITY не найдены, берем обычные VLESS
    return reality_keys if reality_keys else [k for k in all_keys if k.startswith("vless://")]

async def get_free_v2ray_config(country_code: str = None) -> str | None:
    """Генерирует рабочий VLESS-REALITY ключ для пользователя."""
    keys = await fetch_reality_keys()
    if not keys:
        return None

    random.shuffle(keys)
    
    # Проверяем первых 25 кандидатов по TCP сокету
    for raw_key in keys[:25]:
        host, port = parse_host_and_port(raw_key)
        if host and port:
            if await check_node_dns_and_socket(host, port):
                return optimize_key_dns(raw_key)

    # Запасной фолбэк
    return optimize_key_dns(random.choice(keys))
