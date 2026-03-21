WORKDIR /app
FROM python:3.10-slim
COPY . .
RUN pip install --no-cache-dir -r requirements.txt || true
CMD ["python", "bot.py"]
