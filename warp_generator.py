import base64
import httpx
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8"
}

# Используем эндпоинты Cloudflare с портом 4500 (как в рабочем примере)
COUNTRY_ENDPOINTS = {
    "de": {"name": "🇩🇪 Германия", "endpoint": "engage.cloudflareclient.com:4500"},
    "nl": {"name": "🇳🇱 Нидерланды", "endpoint": "162.159.192.1:4500"},
    "us": {"name": "🇺🇸 США", "endpoint": "162.159.193.1:4500"},
    "jp": {"name": "🇯🇵 Япония", "endpoint": "162.159.194.1:4500"}
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

    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=15.0) as client:
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
            print(f"[ERROR] Ошибка обработки ответа: {e}")
            return None

def build_amnezia_wg_config(warp_data):
    if not warp_data: 
        return None
        
    # Вставляем структуру из твоего рабочего конфига
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
