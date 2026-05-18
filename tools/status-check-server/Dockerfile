FROM python:3.12.10-slim

WORKDIR /app

RUN adduser --system --uid 65532 --group appuser

COPY app.py /app/app.py

USER 65532:65532

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).read()" || exit 1

CMD ["python", "/app/app.py"]
