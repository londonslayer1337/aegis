import base64
import base64
import random
import httpx
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8"
}

# Приоритетные IP из диапазона 188.114.x.x, которые лучше всего проходят ТСПУ
COUNTRY_ENDPOINTS = {
    "de": {
        "name": "🇩🇪 Германия",
        "clean_ips": [
            "188.114.96.1", "188.114.96.2", "188.114.96.3", "188.114.96.4", "188.114.96.5",
            "188.114.96.8", "188.114.96.10", "188.114.97.1", "188.114.97.2", "188.114.97.3",
            "188.114.97.4", "188.114.97.5", "188.114.97.8", "188.114.97.10"
        ]
    },
    "nl": {
        "name": "🇳🇱 Нидерланды",
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
        "clean_ips": ["162.159.192.1", "162.159.192.2", "188.114.96.1", "188.114.96.2"]
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
        "clean_ips": ["162.159.192.1", "162.159.192.2", "188.114.96.1", "188.114.96.2"]
    },
    "nl": {
        "name": "🇳🇱 Нидерланды",
        "clean_ips": ["188.114.98.1", "188.114.98.2", "188.114.99.1", "188.114.99.2"]
    },
    "us": {
        "name": "🇺🇸 США",
        "clean_ips": ["162.159.195.1", "162.159.195.2", "162.159.196.1", "162.159.196.2"]
    },
    "jp": {
        "name": "🇯🇵 Япония",
        "clean_ips": ["162.159.194.1", "162.159.194.2", "162.159.197.1", "162.159.197.2"]
    }
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
        "clean_ips": ["162.159.192.1", "162.159.192.2", "188.114.96.1", "188.114.96.2"]
    },
    "nl": {
        "name": "🇳🇱 Нидерланды",
        "clean_ips": ["188.114.98.1", "188.114.98.2", "188.114.99.1", "188.114.99.2"]
    },
    "us": {
        "name": "🇺🇸 США",
        "clean_ips": ["162.159.195.1", "162.159.195.2", "162.159.196.1", "162.159.196.2"]
    },
    "jp": {
        "name": "🇯🇵 Япония",
        "clean_ips": ["162.159.194.1", "162.159.194.2", "162.159.197.1", "162.159.197.2"]
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
            clean_ip = random.choice(country_data["clean_ips"])

            return {
                "private_key": priv_key,
                "v4_addr": res["config"]["interface"]["addresses"]["v4"],
                "v6_addr": res["config"]["interface"]["addresses"]["v6"],
                "peer_pubkey": res["config"]["peers"][0]["public_key"],
                "endpoint": f"{clean_ip}:4500",
                "country_name": country_data["name"]
            }
        except Exception as e:
            print(f"[ERROR] WARP Reg API: {e}")
            return None

def build_amnezia_wg_config(warp_data):
    if not warp_data: 
        return """[Interface]
PrivateKey = igicLUcfe9iVboyeYKR2glpknXjLw/GCH/19OjEe7LA=
Address = 172.16.0.2, 2606:4700:110:8947:acff:f920:abc6:9741
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
PublicKey = bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=
AllowedIPs = 0.0.0.0/0
Endpoint = engage.cloudflareclient.com:4500
PersistentKeepalive = 25
"""

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
