FROM python:3.10-slim

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install --with-deps

COPY . .

CMD ["python", "main.py"]
