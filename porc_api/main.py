
import logging
from fastapi import FastAPI, Request, Path
from porc_core.github_client import get_github_client
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()
mongo = AsyncIOMotorClient("mongodb://mongo:27017")
db = mongo.porc
runs = db.runs

@app.post("/blueprint")
async def submit_blueprint(request: Request):
    # trimmed version
    return {"run_id": "porc-<timestamp>"}
