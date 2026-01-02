# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# установим зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# скопируем код (не включает большие данные, db в .gitignore)
COPY . /app

# создаём папку data, если нет (фактически её заменит bind-mount)
RUN mkdir -p /app/data

CMD ["python", "app.py"]
