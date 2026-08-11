"""
File storage, behind an interface — same reasoning as EmailService and
LLMProvider. LocalFileStorage is what actually runs; swapping to S3/GCS for
a real multi-instance deployment means writing one class here, not touching
any route or service that calls save()/delete().
"""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config.settings import settings


class FileStorage(ABC):
    @abstractmethod
    async def save(self, content: bytes, extension: str, subdir: str) -> str:
        """Persist content, return a storage key (not a filesystem path —
        callers should not assume local-disk semantics)."""
        ...

    @abstractmethod
    def get_path(self, storage_key: str) -> Path:
        """Resolve a storage key back to a readable local path. For a future
        S3 backend this would instead return a presigned URL or download
        the object to a temp file — the interface stays the same either way."""
        ...

    @abstractmethod
    async def delete(self, storage_key: str) -> None: ...


class LocalFileStorage(FileStorage):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, extension: str, subdir: str) -> str:
        # Never derive the stored filename from user input — a random UUID
        # sidesteps path traversal, collisions, and filename-based attacks
        # entirely. The user's original filename is kept only as metadata.
        safe_subdir = "".join(c for c in subdir if c.isalnum() or c in "-_")
        target_dir = self.base_dir / safe_subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.{extension}"
        storage_key = f"{safe_subdir}/{filename}"
        (target_dir / filename).write_bytes(content)
        return storage_key

    def get_path(self, storage_key: str) -> Path:
        resolved = (self.base_dir / storage_key).resolve()
        # Defence in depth: even though storage_key is never built from raw
        # user input on the write path, refuse to resolve outside base_dir.
        if not str(resolved).startswith(str(self.base_dir)):
            raise ValueError("Resolved path escapes the storage root")
        return resolved

    async def delete(self, storage_key: str) -> None:
        path = self.get_path(storage_key)
        path.unlink(missing_ok=True)


_storage: FileStorage | None = None


def get_file_storage() -> FileStorage:
    global _storage
    if _storage is None:
        _storage = LocalFileStorage()
    return _storage
