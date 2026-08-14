import base64
import requests
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

# Публичные проверенные WARP-эндпоинты Cloudflare по регионам (IP:Port)
COUNTRY_ENDPOINTS = {
    "de": {
        "name": "🇩🇪 Германия",
import base64
import requests
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

# Оптимизированная сессия для быстрых запросов
http_session = requests.Session()
http_session.headers.update({
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8"
})

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
        format=serialization.PrivateFormat.Raw
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    return (
        base64.b64encode(priv_bytes).decode('utf-8'),
        base64.b64encode(pub_bytes).decode('utf-8')
    )

def register_warp_account(country_code="de"):
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

    try:
        # Таймаут 3 секунды для молниеносного ответа
        response = http_session.post(url, json=payload, timeout=3)
        response.raise_for_status()
        data = response.json()

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
        print(f"[ERROR] Ошибка генерации WARP: {e}")
        return None

