from pathlib import Path

import pytest

from backend.app.services import document_storage


class FakeBlobClient:
    def __init__(self):
        self.uploaded = None

    def upload_blob(self, data, overwrite, content_settings):
        self.uploaded = {
            "data": data.read(),
            "overwrite": overwrite,
            "content_settings": content_settings,
        }


class FakeBlobService:
    def __init__(self):
        self.client = FakeBlobClient()
        self.container = None
        self.blob = None

    def get_blob_client(self, container, blob):
        self.container = container
        self.blob = blob
        return self.client


def test_azure_upload_uses_private_container_and_blob_path(
    tmp_path, monkeypatch
):
    file_path = tmp_path / "synthetic.pdf"
    file_path.write_bytes(b"%PDF-synthetic-test")

    fake_service = FakeBlobService()

    monkeypatch.setenv("STORAGE_BACKEND", "azure")
    monkeypatch.setenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        "fake-connection-string",
    )
    monkeypatch.setenv(
        "AZURE_STORAGE_CONTAINER",
        "claim-documents",
    )

    monkeypatch.setattr(
        document_storage.BlobServiceClient,
        "from_connection_string",
        lambda connection_string: fake_service,
    )

    result = document_storage.upload_document_to_blob(
        str(file_path),
        "CLM-TEST-001",
        "DOC-TEST-001",
    )

    assert result == {
        "storage_backend": "azure",
        "blob_name": "claims/CLM-TEST-001/synthetic.pdf",
    }
    assert fake_service.container == "claim-documents"
    assert fake_service.blob == "claims/CLM-TEST-001/synthetic.pdf"
    assert fake_service.client.uploaded["data"] == b"%PDF-synthetic-test"
    assert fake_service.client.uploaded["overwrite"] is False


def test_azure_upload_fails_when_connection_string_is_missing(
    tmp_path, monkeypatch
):
    file_path = tmp_path / "synthetic.txt"
    file_path.write_text("Synthetic claim document", encoding="utf-8")

    monkeypatch.setenv("STORAGE_BACKEND", "azure")
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)

    with pytest.raises(
        document_storage.StorageUploadError,
        match="connection string is not configured",
    ):
        document_storage.upload_document_to_blob(
            str(file_path),
            "CLM-TEST-001",
            "DOC-TEST-001",
        )


def test_local_mode_does_not_connect_to_azure(
    tmp_path, monkeypatch
):
    file_path = tmp_path / "synthetic.txt"
    file_path.write_text("Synthetic claim document", encoding="utf-8")

    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)

    result = document_storage.upload_document_to_blob(
        str(file_path),
        "CLM-TEST-001",
        "DOC-TEST-001",
    )

    assert result == {
        "storage_backend": "local",
        "blob_name": None,
    }