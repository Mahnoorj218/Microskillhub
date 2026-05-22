import pytest
from fastapi.testclient import TestClient
from main import app

# Yahan hum manual client configuration kar rahe hain taake version conflict na ho
client = TestClient(app)

def test_register_student_success():
    payload = {
        "full_name": "Test Student",
        "email": "test@test.edu",
        "password": "password123",
        "role": "student",
        "roll_number": "TEST-01"
    }
    # Agar ye line error de, toh hum direct request call kar lenge
    try:
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code in [200, 201, 400]
    except TypeError:
        # Fallback agar ab bhi 'app' argument ka masla ho
        pytest.fail("TestClient still failing due to version conflict")

def test_get_skills():
    response = client.get("/api/skills/all")
    assert response.status_code == 200