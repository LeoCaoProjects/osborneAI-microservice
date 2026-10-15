FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x wait-for-it.sh

EXPOSE 5002

CMD ["./wait-for-it.sh", "notification-db", "5432", "python", "app.py"]