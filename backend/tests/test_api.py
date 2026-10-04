import os
os.environ["JWT_SECRET"]="test-secret"
from fastapi.testclient import TestClient
from app import app
client=TestClient(app)

def test_health():
    r=client.get("/health")
    assert r.status_code==200
    assert r.json()["service"].startswith("data-center")

def test_login():
    r=client.post("/api/auth/login",json={"username":"admin","password":"admin"})
    assert r.status_code==200
    assert "access_token" in r.json()

def test_protected_endpoint():
    r=client.get("/api/auth/me")
    assert r.status_code==401
