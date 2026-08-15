import base64
import random
import httpx
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8"
}

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

    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=12.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            
            res = data.get("result", data)
            if "config" not in res:
                return None

            country_data = COUNTRY_ENDPOINTS.get(country_code, COUNTRY_ENDPOINTS["de"])
            ip = random.choice(country_data["clean_ips"])

            return {
                "private_key": priv_key,
                "public_key": pub_key,
                "v4_addr": res["config"]["interface"]["addresses"]["v4"],
                "v6_addr": res["config"]["interface"]["addresses"]["v6"],
                "peer_pubkey": res["config"]["peers"][0]["public_key"],
                "endpoint": f"{ip}:53",
                "country_name": country_data["name"]
            }
        except Exception as e:
            print(f"[ERROR] API Error: {e}")
            return None

def build_amnezia_wg_config(warp_data):
    if not warp_data: 
        return None
        
    return f"""[Interface]
PrivateKey = {warp_data['private_key']}
Address = {warp_data['v4_addr']}, {warp_data['v6_addr']}
DNS = 1.1.1.1, 1.0.0.1
MTU = 1220
Jc = 5
Jmin = 50
Jmax = 100
S1 = 15
S2 = 20
H1 = 1
H2 = 2
H3 = 3
H4 = 4

[Peer]
PublicKey = {warp_data['peer_pubkey']}
AllowedIPs = 0.0.0.0/0
Endpoint = {warp_data['endpoint']}
PersistentKeepalive = 25
"""
