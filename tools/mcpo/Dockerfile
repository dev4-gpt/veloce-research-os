FROM python:3.12.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir mcpo uv

EXPOSE 8000

CMD ["uvx", "mcpo", "--host", "0.0.0.0", "--port", "8000", "--api-key", "change-me", "--", "uvx", "mcp-server-time", "--local-timezone=America/New_York"]
