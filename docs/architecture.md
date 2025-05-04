# PORC Architecture

PORC consists of:

## 1. porc_core
- Shared logic for blueprint validation, rendering, and state
- Used by both API and CLI

## 2. porc_api
- FastAPI application
- Accepts blueprints from GitHub, Port, or Kafka
- Validates, stores, and orchestrates Terraform runs

## 3. pine (CLI)
- Local developer tool for schema and metadata validation
- `pine validate`, `pine lint`, and future `pine sign`

## 4. porc_worker (optional)
- Kafka or GitHub dispatcher
- Runs background tasks or async Terraform handling

