import os
import base64
import requests
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

# Список надежных публичных HTTP/SOCKS5 прокси для обхода Cloudflare-блокировок Railway
FALLBACK_PROXIES = [
    "http://185.199.229.156:7492",
    "http://43.167.165.123:10808",
    "socks5://185.230.125.101:1080",
    "http://103.152.112.162:80"
]

COUNTRY_ENDPOINTS = {
    "de": {"name": "🇩🇪 Германия", "endpoint": "162.159.192.1:2408"},
    "nl": {"name": "🇳🇱 Нидерланды", "endpoint": "162.159.193.1:2408"},
    "us": {"name": "🇺🇸 США", "endpoint": "162.159.195.1:2408"},
    "jp": {"name": "🇯🇵 Япония", "endpoint": "162.159.194.1:2408"}
}
import os
import base64
import httpx
import asyncio
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

# Заголовок, который использует реальное приложение WARP на Android
HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8",
    "CF-Client-Version": "a-6.15-2408271300" 
}

COUNTRY_ENDPOINTS = {
    "de": {"name": "🇩🇪 Германия", "endpoint": "162.159.192.1:2408"},
    "nl": {"name": "🇳🇱 Нидерланды", "endpoint": "162.159.193.1:2408"},
    "us": {"name": "🇺🇸 США", "endpoint": "162.159.195.1:2408"},
    "jp": {"name": "🇯🇵 Япония", "endpoint": "162.159.194.1:2408"}
}

def generate_wg_keys():
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(priv_bytes).decode('utf-8'), base64.b64encode(pub_bytes).decode('utf-8')

async def register_warp_account(country_code="de"):
    priv_key, pub_key = generate_wg_keys()
    url = "https://api.cloudflareclient.com/v0a2158/reg"
    payload = {
        "install_id": "",
        "tos": "2024-01-01T00:00:00.000Z",
        "key": pub_key,
        "fcm_token": "",
        "type": "Android",
        "locale": "en_US"
    }

    # Используем httpx с http2=True (эмуляция браузера/приложения)
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=15.0) as client:
        try:
            response = await client.post(url, json=payload)
            
            # ВАЖНО: Если код не 200, выводим всё в логи, чтобы понять причину
            if response.status_code != 200:
                print(f"[DEBUG ERROR] Статус: {response.status_code}, Ответ: {response.text}")
                return None
            
            data = response.json()
            
            if "result" not in data:
                print(f"[ERROR] Нет ключа 'result' в ответе: {data}")
                return None

            v4_addr = data["result"]["config"]["interface"]["addresses"]["v4"]
            v6_addr = data["result"]["config"]["interface"]["addresses"]["v6"]
            peer_pubkey = data["result"]["config"]["peers"][0]["public_key"]
            country_info = COUNTRY_ENDPOINTS.get(country_code, COUNTRY_ENDPOINTS["de"])

            return {
                "private_key": priv_key,
                "public_key": pub_key,
                "v4_addr": v4_addr,
                "v6_addr": v6_addr,
                "peer_pubkey": peer_pubkey,
                "endpoint": country_info["endpoint"],
                "country_name": country_info["name"]
            }
        except Exception as e:
            print(f"[ERROR] Исключение при запросе: {e}")
            return None

def build_amnezia_wg_config(warp_data):
    if not warp_data: return None
    return f"""[Interface]
PrivateKey = {warp_data['private_key']}
Address = {warp_data['v4_addr']}/32, {warp_data['v6_addr']}/128
DNS = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111

Jc = 4
Jmin = 40
Jmax = 70
S1 = 0
S2 = 0
H1 = 1
H2 = 2
H3 = 3
H4 = 4

[Peer]
PublicKey = {warp_data['peer_pubkey']}
Endpoint = {warp_data['endpoint']}
AllowedIPs = 0.0.0.0/0, ::/0
"""

