from fastapi.testclient import TestClient
from porc_dag_api import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_generate_dag():
    payload = {
        "modules": [
            {"name": "network", "depends_on": []},
            {"name": "db", "depends_on": ["network"]},
            {"name": "app", "depends_on": ["network"]},
            {"name": "frontend", "depends_on": ["app"]}
        ]
    }
    response = client.post("/dag", json=payload)
    assert response.status_code == 200
    assert "execution_order" in response.json()
    assert "dag_image_url" in response.json()