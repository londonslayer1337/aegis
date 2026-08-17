import re
import socket
import asyncio
import aiohttp

# Список 10 публичных Telegram-каналов с VLESS/V2Ray ключами
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

def is_server_alive(ip: str, port: int, timeout=2.5) -> bool:
    """Проверяет доступность сервера по TCP-порту."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def parse_vless_ip_port(vless_link: str):
    """Извлекает IP/хост и порт из ссылки VLESS."""
    match = re.search(r'@([^:]+):(\d+)', vless_link)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

async def fetch_keys_from_channel(session: aiohttp.ClientSession, channel: str) -> list[str]:
    """Скачивает публичную веб-страницу канала и находит VLESS ссылки."""
    url = f"https://t.me/s/{channel}"
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                html = await response.text()
                # Находим все vless:// ключи
                keys = re.findall(r'vless://[^\s<"\']+', html)
                return keys
    except Exception:
        pass
    return []

async def get_free_v2ray_config() -> str | None:
    """Главная функция: собирает ключи, чекает пинг и отдает первый рабочий."""
    async with aiohttp.ClientSession() as session:
        all_keys = []
        tasks = [fetch_keys_from_channel(session, ch) for ch in CHANNELS]
        results = await asyncio.gather(*tasks)

        for res in results:
            all_keys.extend(res)

        # Убираем дубликаты
        all_keys = list(set(all_keys))

        if not all_keys:
            return None

        # Проверяем ключи на живой TCP-порт
        for key in all_keys:
            ip, port = parse_vless_ip_port(key)
            if ip and port:
                # Запускаем проверку в отдельном потоке, чтобы не блокировать asyncio
                loop = asyncio.get_running_loop()
                alive = await loop.run_in_executor(None, is_server_alive, ip, port)
                if alive:
                    return key
return None
