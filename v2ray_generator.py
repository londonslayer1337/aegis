import random
import asyncio

# Полный список надежных публичных подписок VLESS/Xray
SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/morteza-f/v2ray-collector/main/sub/vless",
    "https://raw.githubusercontent.com/Ezzatkhah/VPN-Configs/main/Configs/Vless.txt"
]

async def get_free_v2ray_config() -> str:
    """Генерирует и возвращает прямую ссылку подписки для Happ."""
    await asyncio.sleep(0.1)
    # Случайный выбор подписки для распределения нагрузки между источниками
    return random.choice(SUBSCRIPTION_URL,S)
