import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "brownies2024")

# IANA timezone for Mexico City; handles DST shifts automatically
LOCAL_TZ = ZoneInfo("America/Mexico_City")


def now_local():
    """Return current datetime in Mexico City timezone (aware)."""
    return datetime.now(tz=LOCAL_TZ)


def to_local(dt):
    """Convert a datetime from Mongo (naive UTC) to local timezone.

    Mongo stores datetimes as UTC without tzinfo, so we treat naive
    instances as UTC and then convert to LOCAL_TZ. If dt is already
    aware, it is simply converted to LOCAL_TZ.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TZ)


client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.brownies
    await db.clients.create_index("name", unique=True)
    await db.deliveries.create_index("created_at")
    await db.expenses.create_index("date")


async def close_db():
    global client
    if client:
        client.close()


def get_db():
    return db
