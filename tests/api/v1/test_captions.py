"""Tests for caption job endpoints."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


def test_create_caption_job_returns_pending(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    """Test caption job creation returns pending job status."""

    async def noop_process(job_id: str) -> None:
        return None

    monkeypatch.setattr(
        "app.api.v1.endpoints.captions.process_caption_job",
        noop_process,
    )

    mock_client = AsyncMock()
    monkeypatch.setattr("app.services.job_store.client", mock_client)

    payload = {
        "character_id": "character_123",
        "image_file": "tests/fixtures/sample.png",
        "current_description": "An existing description.",
    }
    response = client.post("/api/v1/captions", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "job_id" in data


def test_get_caption_job_status(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    """Test retrieving caption job status."""

    async def noop_process(job_id: str) -> None:
        return None

    monkeypatch.setattr(
        "app.api.v1.endpoints.captions.process_caption_job",
        noop_process,
    )

    mock_client = AsyncMock()
    monkeypatch.setattr("app.services.job_store.client", mock_client)

    payload = {
        "character_id": "character_456",
        "image_file": "tests/fixtures/sample.png",
    }
    create_response = client.post("/api/v1/captions", json=payload, headers=auth_headers)
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    # Mock get to return the job data
    from app.schemas.job import CaptionJobData, JobStatus

    job = CaptionJobData(
        job_id=job_id,
        character_id=payload["character_id"],
        image_file=payload["image_file"],
        current_description=payload.get("current_description"),
        created_by="test_user_123",  # from JWT sub
        status=JobStatus.pending,
    )
    mock_client.get.return_value = job.model_dump_json().encode("utf-8")

    status_response = client.get(f"/api/v1/captions/{job_id}", headers=auth_headers)
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert data["character_id"] == payload["character_id"]
    assert data["status"] == "pending"
    assert data["result"] is None


def test_caption_endpoints_require_auth(client: TestClient) -> None:
    """Test caption endpoints require JWT authorization."""
    response = client.post(
        "/api/v1/captions",
        json={"character_id": "character_789", "image_file": "foo.png"},
    )
    assert response.status_code == 401

    response = client.get("/api/v1/captions/nonexistent-job")
    assert response.status_code == 401
