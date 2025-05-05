# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY porc_api/ ./porc_api/

EXPOSE 8000

CMD ["uvicorn", "porc_api.main:app", "--host", "0.0.0.0", "--port", "8000"]