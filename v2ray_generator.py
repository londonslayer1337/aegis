import base64
import random
import httpx
import re

VLESS_SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/mft00/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/v2raywg/v2ray/main/v2ray"
]

# Словарик для поиска страны в хэштегах ключей
COUNTRY_PATTERNS = {
    "de": [r"germany", r"de", r"🇩🇪", r"германия"],
    "nl": [r"netherlands", r"dutch", r"nl", r"🇳🇱", r"нидерланды"],
    "us": [r"united states", r"usa", r"us", r"🇺🇸", r"сша"],
    "jp": [r"japan", r"jp", r"🇯🇵", r"япония"]
}

async def fetch_all_keys() -> list[str]:
    """Скачивает и декодирует все ключи из подписок."""
    all_keys = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
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
                print(f"[ERROR] VLESS Scraper: {e}")
                continue
    return all_keys

async def get_free_v2ray_config(country_code: str = None) -> str | None:
    """
    Возвращает ключ с фильтрацией по стране (de, nl, us, jp).
    Если страна не указана или не найдена — отдаёт случайный ключ.
    """
    keys = await fetch_all_keys()
    if not keys:
        return None

    # Если страна запрошена
    if country_code and country_code in COUNTRY_PATTERNS:
        patterns = COUNTRY_PATTERNS[country_code]
        matched_keys = []

        for key in keys:
            # Ищем совпадения в хэштеге ключа (всё что после '#')
            hashtag = key.split("#")[-1].lower() if "#" in key else ""
            
            for pattern in patterns:
                if re.search(pattern, hashtag, re.IGNORECASE):
                    matched_keys.append(key)
                    break

        if matched_keys:
            return random.choice(matched_keys)

    # Если под конкретную страну ничего не нашлось или страна не передана — рандом
    return random.choi
ce(keys)
