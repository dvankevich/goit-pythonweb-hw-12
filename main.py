"""Contacts Management API - FastAPI Application.

This module contains the main FastAPI application for the Contacts Management System.
It provides RESTful endpoints for managing contacts, user authentication,
and administrative functions with proper security, rate limiting, and CORS support.

Features:
- User authentication with JWT tokens
- Contact CRUD operations with filtering and search
- Rate limiting to prevent abuse
- Redis caching for performance
- Email verification and password reset
- Avatar upload with Cloudinary integration
- Health monitoring endpoints
- Comprehensive error handling
- OpenAPI/Swagger documentation

Security:
- JWT-based authentication
- Rate limiting with SlowAPI
- CORS middleware for cross-origin requests
- Secret management with Pydantic SecretStr

Architecture:
- Async/await support throughout
- Dependency injection for database sessions
- Middleware for CORS and rate limiting
- Structured error handling
- Lifecycle management for Redis connections
"""

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
    """Manage application lifecycle events.
    
    Handles startup and shutdown events for the FastAPI application.
    On startup, initializes Redis connection if enabled.
    On shutdown, properly closes Redis connection.
    
    Args:
        app: FastAPI application instance.
    
    Yields:
        None: Control is yielded to the application for normal operation.
    """
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
    description="RESTful API for managing contacts with user authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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
    """Handle rate limit exceeded errors.
    
    Provides user-friendly error messages when rate limits are exceeded.
    
    Args:
        request: HTTP request object.
        exc: Rate limit exceeded exception.
    
    Returns:
        JSONResponse: Error response with 429 status code.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


app.include_router(health.router)
app.include_router(contact_router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/",
         summary="Root endpoint",
         description="Returns welcome message and documentation link",
         tags=["General"])
def root():
    """Root endpoint providing API information.
    
    Returns:
        dict: Welcome message with documentation link.
    """
    return {"message": "Welcome to Contacts API. Go to /docs for Swagger UI."}


if __name__ == "__main__":
    """Run the FastAPI application with uvicorn.
    
    Starts the development server on all interfaces (0.0.0.0) on port 8000.
    This allows external access to the API during development.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)
