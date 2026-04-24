# Внешние зависимости
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
# Внутренние модули
from web_app.src.core import cfg


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, login_url: str = "/login"):
        super().__init__(app)
        self.login_url = login_url
        self.exclude_paths = [
            "/auth/login",
            "/static",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)

            # Проверяем если статус 401 и путь не исключен
            if (response.status_code == 401 and
                    not any(request.url.path.startswith(path) for path in self.exclude_paths)):

                # Для HTML запросов - редирект
                if "text/html" in request.headers.get("accept", ""):
                    return RedirectResponse(url=self.login_url)

                # Для API запросов - JSON ответ
                else:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": "Требуется аутентификация",
                            "redirect_url": self.login_url
                        }
                    )

            return response

        except HTTPException as exc:
            if exc.status_code == 401:
                if "text/html" in request.headers.get("accept", ""):
                    return RedirectResponse(url=self.login_url)
                else:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": exc.detail,
                            "redirect_url": self.login_url
                        }
                    )
            raise exc

        except Exception as exc:
            cfg.logger.error(f"Unexpected error: {exc}")
            raise exc