# Стейдж 1: Збірка залежностей
FROM python:3.13-slim AS builder

# Встановлюємо системні залежності для збірки (наприклад, для psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Налаштовуємо Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Встановлюємо poetry
RUN pip install poetry==2.3.2

# Копіюємо файли конфігурації залежностей
COPY pyproject.toml poetry.lock ./

# Встановлюємо тільки основні залежності застосунку
RUN poetry install --only main --no-root && rm -rf $POETRY_CACHE_DIR

# Стейдж 2: Фінальний образ
FROM python:3.13-slim AS runtime

# Встановлюємо libpq для роботи з PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Копіюємо встановлені залежності з першого стейджу
COPY --from=builder /app/.venv /app/.venv

# Копіюємо код застосунку
COPY . .

RUN chmod +x /app/entrypoint.sh

# Компілюємо весь код проекту ТА всі встановлені залежності у venv
RUN python -m compileall /app/.venv/lib/python3.13/site-packages . /usr/local/lib/python3.13

# Експонуємо порт
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl --fail http://localhost:8000/healthcheck || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
