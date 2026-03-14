from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, ServerSelectionTimeoutError
import os

# Read connection settings from environment with sensible defaults
MONGO_URL = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("MONGO_DB_NAME", "rk_world")

client = None
db = None
try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    # Force a server selection to validate connection
    client.server_info()
    db = client[DATABASE_NAME]
except ServerSelectionTimeoutError as e:
    print(f"Error: Cannot connect to MongoDB at {MONGO_URL}: {e}")
    client = None
    db = None


def create_collections():
    """Create all required MongoDB collections (no-op when DB unreachable)."""
    if db is None:
        print("No database connection available — cannot create collections.")
        return

    collections_to_create = [
        "users",
        "students",
        "lecturers",
        "attendance",
        "assignments",
        "events",
        "fees",
        "marks",
        "employees",
        "payslips",
        "punch_records",
        "marked_attendance",
        "quizzes",
        "quiz_submissions",
    ]

    for collection_name in collections_to_create:
        try:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"✓ Collection '{collection_name}' created successfully")
            else:
                print(f"• Collection '{collection_name}' already exists")
        except CollectionInvalid as e:
            print(f"✗ Error creating collection '{collection_name}': {e}")


if __name__ == "__main__":
    create_collections()
    print("\nAll collections ready (if DB was reachable)")
