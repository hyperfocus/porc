from fastapi import FastAPI, Request
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI()

# Connect to MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/porc")
client = MongoClient(mongo_uri)
db = client.get_database()
runs = db.runs

@app.post("/submit")
async def submit(request: Request):
    data = await request.json()
    data["status"] = "submitted"
    data["submitted_at"] = datetime.utcnow().isoformat()
    result = runs.insert_one(data)
    return {"run_id": str(result.inserted_id)}

@app.post("/build")
async def build(request: Request):
    data = await request.json()
    data["status"] = "build_started"
    data["build_started"] = datetime.utcnow().isoformat()
    return {"message": "Build triggered", "timestamp": data["build_started"]}

@app.post("/plan")
async def plan(request: Request):
    data = await request.json()
    data["status"] = "plan_queued"
    data["plan_started"] = datetime.utcnow().isoformat()
    data["tfe_run_id"] = "fake-run-id"
    return {"message": "Plan started", "run_id": data["tfe_run_id"]}

@app.post("/apply")
async def apply(request: Request):
    data = await request.json()
    data["status"] = "apply_started"
    data["apply_started"] = datetime.utcnow().isoformat()
    return {"message": "Apply started"}

@app.get("/status")
async def status(run_id: str):
    run = runs.find_one({"_id": run_id})
    return run if run else {"error": "Run not found"}

@app.get("/summary")
async def summary():
    all_runs = list(runs.find())
    return {"runs": all_runs}