FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils libgbm1 libxshmfence1 libu2f-udev libvulkan1 libxss1 libxtst6 libxext6 \
    libxfixes3 libxcb1 libx11-6 libxrender1 libxkbcommon0 libatspi2.0-0 \
    && apt-get clean

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN python -m playwright install chromium

CMD ["python", "main.py"]
