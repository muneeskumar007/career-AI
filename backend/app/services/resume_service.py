import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.resume import BasicInfo, ResumeStatus
from app.schemas.resume import ResumeDetailResponse, ResumeListResponse, ResumeResponse
from app.services.parsing.text_extraction import extract_text
from app.utils.exceptions import ForbiddenException, InvalidTokenException, UserNotFoundException
from app.utils.file_storage import get_file_storage
from app.utils.file_validation import validate_upload

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Matches common resume phone formats: +1 415-555-0100, (415) 555-0100, 415.555.0100, etc.
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")


def _to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise InvalidTokenException("Invalid resume id")


def _extract_basic_info(raw_text: str) -> BasicInfo:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    email_match = EMAIL_PATTERN.search(raw_text)
    phone_match = PHONE_PATTERN.search(raw_text)

    # Heuristic: the candidate's name is very reliably the first non-empty
    # line on a resume that isn't itself an email/phone/URL. Refined further
    # by spaCy PERSON-entity detection in Module 3's deeper parse.
    name = None
    for line in lines[:3]:
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line) or "http" in line.lower():
            continue
        if 2 <= len(line.split()) <= 5 and len(line) < 60:
            name = line
            break

    return BasicInfo(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0).strip() if phone_match else None,
    )


def _to_response(doc: dict) -> ResumeResponse:
    return ResumeResponse(
        id=str(doc["_id"]),
        original_filename=doc["original_filename"],
        file_type=doc["file_type"],
        file_size_bytes=doc["file_size_bytes"],
        basic_info=doc["basic_info"],
        status=doc["status"],
        created_at=doc["created_at"],
    )


class ResumeService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.resumes = db.resumes
        self.storage = get_file_storage()

    async def upload(self, user_id: str, filename: str, content: bytes) -> ResumeResponse:
        extension = validate_upload(filename, content)
        raw_text = extract_text(content, extension)
        basic_info = _extract_basic_info(raw_text)
        storage_key = await self.storage.save(content, extension, subdir=user_id)

        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "original_filename": filename,
            "storage_key": storage_key,
            "file_type": extension,
            "file_size_bytes": len(content),
            "raw_text": raw_text,
            "basic_info": basic_info.model_dump(),
            "status": ResumeStatus.UPLOADED.value,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.resumes.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_response(doc)

    async def get_owned(self, resume_id: str, user_id: str) -> dict:
        """Fetch a resume, raising if it doesn't exist or belongs to someone
        else. Every resume-scoped endpoint must go through this — this is
        the single place ownership is enforced."""
        doc = await self.resumes.find_one({"_id": _to_object_id(resume_id)})
        if not doc:
            raise UserNotFoundException("Resume not found")
        if doc["user_id"] != user_id:
            raise ForbiddenException("You don't have access to this resume")
        return doc

    async def get_detail(self, resume_id: str, user_id: str) -> ResumeDetailResponse:
        doc = await self.get_owned(resume_id, user_id)
        return ResumeDetailResponse(
            id=str(doc["_id"]),
            original_filename=doc["original_filename"],
            file_type=doc["file_type"],
            file_size_bytes=doc["file_size_bytes"],
            basic_info=doc["basic_info"],
            status=doc["status"],
            created_at=doc["created_at"],
            raw_text=doc["raw_text"],
        )

    async def list_for_user(self, user_id: str) -> ResumeListResponse:
        cursor = self.resumes.find({"user_id": user_id}).sort("created_at", -1)
        items = [_to_response(doc) async for doc in cursor]
        return ResumeListResponse(items=items, total=len(items))

    async def delete(self, resume_id: str, user_id: str) -> None:
        doc = await self.get_owned(resume_id, user_id)
        await self.storage.delete(doc["storage_key"])
        await self.resumes.delete_one({"_id": doc["_id"]})
