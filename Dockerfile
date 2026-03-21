FROM python:3.10-slim
WORKDIR /app
COPY bot.py .
CMD ["python", "bot.py"]
