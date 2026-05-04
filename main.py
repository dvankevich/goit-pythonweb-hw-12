import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware  # Імпортуємо Middleware
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.db.session import get_db
from src.api.contact_api import router as contact_router
from src.api import auth, users, health
from src.api.users import limiter
from src.db.redis_client import check_redis_connection, redis_client
from src.config.app_config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, який виконується ПРИ ЗАПУСКУ
    if settings.ENABLE_REDIS:
        is_connected = await check_redis_connection()
        if not is_connected:
            logging.warning(
                "!!! Redis is enabled but not accessible. Application will work without cache. !!!"
            )
    else:
        logging.info("Redis caching is disabled by configuration.")

    yield  # Тут застосунок працює і приймає запити

    # Код, який виконується ПРИ ВИМКНЕННІ
    if settings.ENABLE_REDIS:
        await redis_client.aclose()
        logging.info("Redis connection closed.")


app = FastAPI(
    title="Contacts API",
    lifespan=lifespan,
    # title="Contacts API", swagger_ui_parameters={"defaultModelsExpandDepth": -1} # щоб прибрати схему
)
app.state.limiter = limiter

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,  # Список дозволених джерел
    allow_credentials=True,  # Дозволити передачу Cookies та Authorization headers
    allow_methods=["*"],  # Дозволити всі методи (GET, POST, PUT, DELETE тощо)
    allow_headers=["*"],  # Дозволити всі заголовки
)
# -------------------------


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


app.include_router(health.router)
app.include_router(contact_router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Welcome to Contacts API. Go to /docs for Swagger UI."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
