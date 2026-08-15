FROM python:3.11-slim

WORKDIR /app

# Отключаем создание pyc файлов и включение буферизации вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем файл зависимостей
COPY requirements.txt .

# Обновляем pip и устанавливаем ТОЛЬКО готовые скомпилированные wheels (--only-binary=:all:)
# Это предотвратит любую попытку компиляции Rust/C и падение сборки
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --only-binary=:all: -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запуск бота
CMD ["python", "main
.py"]
