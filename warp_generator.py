import base64
import random
import httpx
import asyncio
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8"
}

# Набор рабочих UDP-портов для обхода DPI
WORKING_PORTS = [500, 1701, 2408, 4500, 5000, 50100]

# Полный список Clean IP Cloudflare по странам (по 14 адресов на каждую страну)
COUNTRY_ENDPOINTS = {
    "de": {
        "name": "🇩🇪 Германия",
        "clean_ips": [
            "162.159.192.1", "162.159.192.2", "162.159.192.3", "162.159.192.4", "162.159.192.5",
            "162.159.192.8", "162.159.192.10", "162.159.193.1", "162.159.193.2", "162.159.193.3",
            "162.159.193.4", "162.159.193.5", "162.159.193.8", "162.159.193.10"
        ]
    },
    "nl": {
        "name": "🇳🇱 Нидерланды",
        "clean_ips": [
            "188.114.96.1", "188.114.96.2", "188.114.96.3", "188.114.96.4", "188.114.96.5",
            "188.114.96.8", "188.114.96.10", "188.114.97.1", "188.114.97.2", "188.114.97.3",
            "188.114.97.4", "188.114.97.5", "188.114.97.8", "188.114.97.10"
        ]
    },
    "us": {
        "name": "🇺🇸 США",
        "clean_ips": [
            "162.159.195.1", "162.159.195.2", "162.159.195.3", "162.159.195.4", "162.159.195.5",
            "162.159.195.8", "162.159.195.10", "162.159.196.1", "162.159.196.2", "162.159.196.3",
            "162.159.196.4", "162.159.196.5", "162.159.196.8", "162.159.196.10"
        ]
    },
    "jp": {
        "name": "🇯🇵 Япония",
        "clean_ips": [
            "162.159.194.1", "162.159.194.2", "162.159.194.3", "162.159.194.4", "162.159.194.5",
            "162.159.194.8", "162.159.194.10", "162.159.197.1", "162.159.197.2", "162.159.197.3",
            "162.159.197.4", "162.159.197.5", "162.159.197.8", "162.159.197.10"
        ]
    }
}

async def is_endpoint_alive(ip: str, port: int, timeout: float = 1.2) -> bool:
    """Быстрая проверка доступности комбинации IP:Port по TCP handshake."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def get_working_endpoint(country_code="de") -> str:
    """Перебирает случайные комбинации IP и портов из пула страны до первого живого."""
    country_data = COUNTRY_ENDPOINTS.get(country_code, COUNTRY_ENDPOINTS["de"])
    ips = country_data["clean_ips"].copy()
    random.shuffle(ips)
    
    for ip in ips:
        ports = WORKING_PORTS.copy()
        random.shuffle(ports)
        for port in ports:
            if await is_endpoint_alive(ip, port):
                print(f"[CHECK] Найден рабочий эндпоинт: {ip}:{port}")
                return f"{ip}:{port}"
                
    # Фоллбэк на случай, если TCP блокируется провайдером
    fallback_ip = random.choice(country_data["clean_ips"])
    fallback_port = random.choice(WORKING_PORTS)
    print(f"[CHECK] Живых эндпоинтов не найдено, задействован дефолт: {fallback_ip}:{fallback_port}")
    return f"{fallback_ip}:{fallback_port}"

def generate_wg_keys():
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    priv_bytes = private_key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption()
    )
    pub_bytes = public_key.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw
    )
    
    priv_b64 = base64.b64encode(priv_bytes).decode('utf-8')
    pub_b64 = base64.b64encode(pub_bytes).decode('utf-8')
    
    return priv_b64, pub_b64

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

    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=12.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            
            res = data.get("result", data)
            if "config" not in res:
                print(f"[ERROR] Неожиданный формат API: {data}")
                return None

            v4_addr = res["config"]["interface"]["addresses"]["v4"]
            v6_addr = res["config"]["interface"]["addresses"]["v6"]
            peer_pubkey = res["config"]["peers"][0]["public_key"]
            country_info = COUNTRY_ENDPOINTS.get(country_code, COUNTRY_ENDPOINTS["de"])

            # Подбираем 100% живой эндпоинт из 14 IP выбранной страны
            endpoint = await get_working_endpoint(country_code)

            return {
                "private_key": priv_key,
                "public_key": pub_key,
                "v4_addr": v4_addr,
                "v6_addr": v6_addr,
                "peer_pubkey": peer_pubkey,
                "endpoint": endpoint,
                "country_name": country_info["name"]
            }
        except Exception as e:
            print(f"[ERROR] Ошибка выполнения запроса к API: {e}")
            return None

def build_amnezia_wg_config(warp_data):
    if not warp_data: 
        return None
        
    return f"""[Interface]
PrivateKey = {warp_data['private_key']}
Address = {warp_data['v4_addr']}, {warp_data['v6_addr']}
DNS = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111, 2606:4700:4700::1001
MTU = 1280
Jc = 19
Jmin = 76
Jmax = 322
S1 = 0
S2 = 0
S3 = 0
S4 = 0
H1 = 1
H2 = 2
H3 = 3
H4 = 4
I1 = <b 0x000100602112a442ff28ec860ce31adf94cf190b80220006706a6e617468000000060015313839343237343137323a436d42325a3246795977000000002400047d73d4d4802a0008a3b15ee41d3ecabc00250000002600148972b9890cdb1001c1ce2f8be724c92ad8c88c1a802800045e24362a>

[Peer]
PublicKey = {warp_data['peer_pubkey']}
AllowedIPs = 0.0.0.0/0
Endpoint = {warp_data['endpoint']}
PersistentKeepalive = 25
"""
