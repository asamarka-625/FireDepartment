# Внешние зависимости
from typing import Dict
from fastapi import Request


# Dependency для получения информации о соединении
def get_connection_info(request: Request) -> Dict[str, str]:
    user_agent = request.headers.get("User-Agent", "NoAgent")

    ip = request.headers.get("X-Forwarded-For")
    if ip:
        ip = ip.split(",")[0].strip()
    else:
        ip = request.headers.get("X-Real-IP") or request.client.host or "NoIP"

    return {"user_agent": user_agent, "ip": ip}