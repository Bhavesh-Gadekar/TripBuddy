FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY packages/tripbuddy_core /packages/tripbuddy_core
RUN pip install --no-cache-dir -e /packages/tripbuddy_core

COPY services/mcp_server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/mcp_server/app /app/app
COPY tests /app/tests

ENV PYTHONPATH=/app:/packages/tripbuddy_core

EXPOSE 8001

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8001"]

