FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium-headless-shell \
    && playwright install-deps chromium-headless-shell

COPY . .

CMD ["python", "main.py"]