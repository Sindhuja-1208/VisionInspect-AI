import os

from dotenv import load_dotenv
from pymongo import MongoClient


# ==========================================
# Load Environment Variables
# ==========================================

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI is not configured in the .env file"
    )


# ==========================================
# MongoDB Connection
# ==========================================

client = MongoClient(
    MONGODB_URI,
    tls=True,
    serverSelectionTimeoutMS=15000,
    connectTimeoutMS=15000,
    socketTimeoutMS=15000,
    retryWrites=True,
)


# ==========================================
# Database
# ==========================================

DATABASE_NAME = "visioninspect_ai"

db = client[DATABASE_NAME]


# ==========================================
# Collections
# ==========================================

users_collection = db["users"]
inspections_collection = db["inspections"]


# ==========================================
# Get Database
# ==========================================

def get_database():
    return db


# ==========================================
# Connection Test
# ==========================================

def check_database_connection():
    try:
        client.admin.command("ping")
        return True
    except Exception as e:
        print("MongoDB connection error:", e)
        return False


# ==========================================
# Create Indexes
# ==========================================

try:
    users_collection.create_index(
        "email",
        unique=True
    )

    inspections_collection.create_index(
        "user_id"
    )

    inspections_collection.create_index(
        "created_at"
    )

    inspections_collection.create_index(
        "category"
    )

    inspections_collection.create_index(
        "result"
    )

    print("MongoDB indexes ready.")

except Exception as e:
    print("MongoDB index creation warning:", e)