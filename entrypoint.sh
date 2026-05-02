#!/bin/sh
set -e

# Функція для перевірки доступності порту бази даних
wait_for_db() {
  echo "Чекаємо на запуск бази даних ($POSTGRES_HOST:$POSTGRES_PORT)..."
  
  while ! python -c "import socket; s = socket.socket(); s.connect(('$POSTGRES_HOST', int('$POSTGRES_PORT')))" > /dev/null 2>&1; do
    echo "База даних ще недоступна, чекаємо 1 секунду..."
    sleep 1
  done

  echo "База даних доступна!"
}

# Викликаємо перевірку
wait_for_db

# Тепер можна безпечно робити міграції
echo "Виконуємо міграції..."
alembic upgrade head

# Створюємо адміністратора
echo "Перевірка/створення адміністратора..."
python -m src.utils.create_admin

echo "Запускаємо сервер..."
exec uvicorn main:app --host 0.0.0.0 --port 8000