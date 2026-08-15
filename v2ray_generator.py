import base64
import random
import httpx
import re
import asyncio
import socket
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Проверенные динамические подписки VLESS / WARP / Xray
VLESS_SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/mft00/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/v2raywg/v2ray/main/v2ray",
    "https://raw.githubusercontent.com/EskandarAtaro/V2ray-Configs/main/Splitted-By-Protocol/vless.txt"
]

def parse_host_and_port(key: str) -> tuple[str | None, int | None]:
    """Извлекает IP/домен и порт из ссылки VLESS / VMess / Trojan / SS."""
    try:
        if key.startswith("vmess://"):
            b64_data = key.replace("vmess://", "")
            b64_data += "=" * ((4 - len(b64_data) % 4) % 4)
            decoded = base64.b64decode(b64_data).decode('utf-8', errors='ignore')
            import json
            data = json.loads(decoded)
            return data.get("add"), int(data.get("port", 443))
        else:
            parsed = urlparse(key)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme in ["vless", "trojan"] else 80)
            return host, port
    except Exception:
        return None, None

def optimize_key_dns(key: str) -> str:
    """Исправляет параметры ключа, настраивая чистый DNS (1.1.1.1) и убирает конфликты."""
    try:
        if not key.startswith("vless://"):
            return key
            
        parsed = urlparse(key)
        query_params = parse_qs(parsed.query)
        
        # Настройка параметров для обхода блокировок и чистого DNS
        query_params['dns'] = ['1.1.1.1']
        
        # Если в ключе нет зашифрованного SNI, ставим стандартный TLS/Cloudflare
        if 'security' not in query_params:
            query_params['security'] = ['tls']
            
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    except Exception:
        return key

async def check_node_dns_and_socket(host: str, port: int, timeout: float = 2.0) -> bool:
    """Проверяет DNS-резолв и делает активное TCP-рукопожатие с узлом."""
    if not host or not port:
        return False
    try:
        # 1. Проверка DNS резолвинга
        loop = asyncio.get_event_loop()
        ip_list = await loop.run_in_executor(
            None, lambda: socket.gethostbyname_ex(host)[2]
        )
        if not ip_list:
            return False

        # 2. Проверка TCP сокета
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
                print(f"[ERROR] Scraper fetch: {e}")
                continue
    return all_keys

async def get_free_v2ray_config(country_code: str = None) -> str | None:
    """Ищет живой ключ с проверкой сокета и настройкой DNS."""
    keys = await fetch_all_keys()
    if not keys:
        return None

    # Приоритет VLESS ключам (они работают лучше всего)
    vless_keys = [k for k in keys if k.startswith("vless://")]
    candidate_keys = vless_keys if vless_keys else keys

    random.shuffle(candidate_keys)
    
    # Проверяем первые 20 кандидатов на доступность и DNS
    for raw_key in candidate_keys[:20]:
        host, port = parse_host_and_port(raw_key)
        if host and port:
            is_alive = await check_node_dns_and_socket(host, port)
            if is_alive:
                # Оптимизируем ключ под DNS 1.1.1.1
                return optimize_key_dns(raw_key)

    # Запасной вариант
    if candidate_keys:
        return optimize_key_dns(random.choice(candidate_keys))
    
    return None
