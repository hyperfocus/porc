# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY porc_api/ ./porc_api/
COPY porc_core/ ./porc_core/
COPY porc_worker/ ./porc_worker/
COPY pine/ ./pine/
COPY porc_common/ ./porc_common/
COPY schemas/ ./schemas/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && mkdir -p /tmp/porc-metadata /tmp/porc-runs /tmp/porc-audit

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh api"]
