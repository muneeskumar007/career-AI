import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import settings

logger = logging.getLogger(__name__)


class _MongoConnection:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


_connection = _MongoConnection()


async def connect_to_mongo() -> None:
    """Open the Motor client and ensure indexes exist. Called once on app startup."""
    _connection.client = AsyncIOMotorClient(settings.MONGODB_URI)
    _connection.db = _connection.client[settings.MONGODB_DB_NAME]
    await _create_indexes()
    logger.info("Connected to MongoDB database '%s'", settings.MONGODB_DB_NAME)


async def close_mongo_connection() -> None:
    if _connection.client is not None:
        _connection.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    if _connection.db is None:
        raise RuntimeError(
            "Database not initialized. connect_to_mongo() must run before the app "
            "serves requests (see the lifespan handler in main.py)."
        )
    return _connection.db


async def _create_indexes() -> None:
    db = _connection.db
    assert db is not None
    await db.users.create_index("email", unique=True)
    await db.users.create_index("reset_password_token_hash", sparse=True)
    await db.resumes.create_index("user_id")
    await db.resume_analysis.create_index("resume_id")
    await db.resume_analysis.create_index("user_id")
    await db.job_descriptions.create_index("user_id")
    await db.ats_results.create_index([("resume_id", 1), ("job_description_id", 1)])
    await db.ats_results.create_index("user_id")
    await db.interview_questions.create_index("resume_id")
    await db.interviews.create_index("user_id")
    await db.interviews.create_index([("user_id", 1), ("status", 1)])
    await db.interview_answers.create_index("interview_id")
