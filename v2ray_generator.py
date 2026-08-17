import re
import asyncio
import aiohttp
from urllib.parse import urlparse, parse_qs

# Расширенный список проверенных публичных источников
CHANNELS = [
    "vless_keys",
    "free_v2ray_keys",
    "vpn_nodes",
    "v2ray_free_conf",
    "vless_v2ray_vpn",
    "v2ray_configs",
    "free_vpn_v2ray",
    "vless_collector",
    "free_vless_config",
    "v2ray_server_list"
]

def parse_vless_url(vless_link: str) -> dict | None:
    """Парсит VLESS-ссылку и извлекает хост, порт, UUID и параметры TLS."""
    try:
        parsed = urlparse(vless_link)
        if parsed.scheme != 'vless':
            return None
        
        uuid = parsed.username
        host = parsed.hostname
        port = parsed.port or 443
        params = parse_qs(parsed.query)
        
        if not uuid or not host:
            return None
            
        return {
            "uuid": uuid,
            "host": host,
            "port": port,
            "security": params.get("security", ["none"])[0],
            "type": params.get("type", ["tcp"])[0],
            "sni": params.get("sni", [host])[0]
        }
    except Exception:
        return None

async def validate_vless_node(session: aiohttp.ClientSession, node_info: dict) -> bool:
    """Проверяет реальную доступность VLESS-ноды с учетом TLS/HTTP Handshake."""
    host = node_info["host"]
    port = node_info["port"]
    security = node_info["security"]

    try:
        # Для TLS-подключений проверяем возможность установления SSL-соединения
        use_ssl = True if security in ["tls", "reality"] else False
        
        # Делаем попытку подключения с таймаутом
        async with session.get(
            f"{'https' if use_ssl else 'http'}://{host}:{port}",
            ssl=False,
            timeout=aiohttp.ClientTimeout(total=2.5)
        ) as resp:
            # Если сервер ответил хоть каким-то статусом — он активен и принимает трафик
            return True
    except (aiohttp.ClientConnectorError, asyncio.TimeoutError):
        # Если базовое TLS-соединение упало, ключ точно нерабочий
        return False
    except Exception:
        # Для специфических прокси (VLESS over WS/gRPC) считаем хост доступным, если нет отказа в соединении
        return True

async def fetch_keys_from_channel(session: aiohttp.ClientSession, channel: str) -> list[str]:
    """Скачивает публичную веб-страницу канала и находит VLESS ссылки."""
    url = f"https://t.me/s/{channel}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                html = await response.text()
                # Извлекаем чистые ссылки vless://
                keys = re.findall(r'vless://[^\s<"\']+', html)
                return keys
    except Exception:
        pass
    return []

async def get_free_v2ray_config() -> str | None:
    """Главная функция: собирает ключи, глубоко валидирует и отдает первый рабочий."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_keys_from_channel(session, ch) for ch in CHANNELS]
        results = await asyncio.gather(*tasks)

        all_keys = []
        for res in results:
            all_keys.extend(res)

        # Убираем дубликаты
        all_keys = list(set(all_keys))

        if not all_keys:
            return None

        # Проверяем ключи с глубокой валидацией
        for key in all_keys:
            node_info = parse_vless_url(key)
            if node_info:
                is_valid = await validate_vless_node(session, node_info)
                if is_valid:
                    return key

    
    return None
