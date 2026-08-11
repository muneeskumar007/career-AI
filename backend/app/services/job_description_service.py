from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from app.utils.exceptions import ForbiddenException, InvalidTokenException, UserNotFoundException


def _to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise InvalidTokenException("Invalid job description id")


def _to_response(doc: dict) -> JobDescriptionResponse:
    return JobDescriptionResponse(
        id=str(doc["_id"]), title=doc.get("title"), company=doc.get("company"),
        raw_text=doc["raw_text"], created_at=doc["created_at"],
    )


class JobDescriptionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.jds = db.job_descriptions

    async def create(self, user_id: str, payload: JobDescriptionCreate) -> JobDescriptionResponse:
        doc = {
            "user_id": user_id,
            "title": payload.title,
            "company": payload.company,
            "raw_text": payload.raw_text,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.jds.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_response(doc)

    async def get_owned(self, jd_id: str, user_id: str) -> dict:
        doc = await self.jds.find_one({"_id": _to_object_id(jd_id)})
        if not doc:
            raise UserNotFoundException("Job description not found")
        if doc["user_id"] != user_id:
            raise ForbiddenException("You don't have access to this job description")
        return doc

    async def get_response(self, jd_id: str, user_id: str) -> JobDescriptionResponse:
        return _to_response(await self.get_owned(jd_id, user_id))

    async def list_for_user(self, user_id: str) -> list[JobDescriptionResponse]:
        cursor = self.jds.find({"user_id": user_id}).sort("created_at", -1)
        return [_to_response(doc) async for doc in cursor]
