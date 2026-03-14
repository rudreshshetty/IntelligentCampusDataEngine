"""Set admission date to 07 NOV 2025 for all students."""
import os
from datetime import datetime
from pymongo import MongoClient

DEFAULT_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "rk_world"
COLLECTION = "students"

def main():
    client = MongoClient(DEFAULT_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    students = db[COLLECTION]

    # Set admission date for all students
    admission_date = datetime(2025, 11, 7)
    
    result = students.update_many(
        {},
        {"$set": {"admission_date": admission_date}}
    )
    
    print(f"Updated {result.modified_count} students with admission date: 07 NOV 2025")

if __name__ == '__main__':
    main()
