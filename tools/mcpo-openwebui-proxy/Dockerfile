FROM python:3.12.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY app.py /app/app.py

EXPOSE 8080

CMD ["python", "/app/app.py"]
