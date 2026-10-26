from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_claim():
    response = client.post(
        "/api/claims/",
        json={
            "claimant_name": "Aarav Sharma",
            "policy_number": "POL-1001",
            "claim_type": "hospitalization",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["claimant_name"] == "Aarav Sharma"
    assert data["policy_number"] == "POL-1001"
    assert data["claim_type"] == "hospitalization"
    assert data["status"] == "submitted"
    assert "claim_id" in data


def test_get_claims():
    created = client.post(
        "/api/claims/",
        json={
            "claimant_name": "Meera Patel",
            "policy_number": "POL-1002",
            "claim_type": "hospitalization",
        },
    )

    claim_id = created.json()["claim_id"]
    response = client.get("/api/claims/")

    assert response.status_code == 200
    assert any(c["claim_id"] == claim_id for c in response.json())


def test_get_claim_by_id():
    created = client.post(
        "/api/claims/",
        json={
            "claimant_name": "Riya Shah",
            "policy_number": "POL-1003",
            "claim_type": "hospitalization",
        },
    )

    claim_id = created.json()["claim_id"]
    response = client.get(f"/api/claims/{claim_id}")

    assert response.status_code == 200
    assert response.json()["claim_id"] == claim_id


def test_get_missing_claim():
    response = client.get("/api/claims/nonexistent-id")

    assert response.status_code == 404


def test_create_claim_with_missing_fields():
    response = client.post(
        "/api/claims/",
        json={"claimant_name": "Aarav Sharma"},
    )

    assert response.status_code == 422


def test_health_endpoint_still_works():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}