#!/usr/bin/env python3
"""
add_parent_numbers.py

Populate the `students` collection with random parent phone numbers for
documents that are missing `phone` or `contact` fields.

Usage:
    python add_parent_numbers.py

It reads `MONGODB_URI` and `MONGO_DB_NAME` from the environment if present,
otherwise defaults to localhost and `rk_world`.
"""

import os
import random
from pymongo import MongoClient


MONGO_URL = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGO_DB_NAME", "rk_world")


def generate_mobile(existing_set):
    """Return a 10-digit mobile string not present in existing_set."""
    while True:
        first = random.choice(["9", "8", "7", "6"])  # common starting digits
        num = first + ''.join(random.choice('0123456789') for _ in range(9))
        if num not in existing_set:
            return num


def main():
    print("Connecting to MongoDB:", MONGO_URL)
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

    try:
        client.server_info()
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
        return

    db = client[DB_NAME]
    students = db["students"]

    # Collect already-used numbers to avoid duplicates
    existing_numbers = set()
    for doc in students.find({}, {"phone": 1, "contact": 1}):
        val = doc.get("phone") or doc.get("contact")
        if val:
            existing_numbers.add(str(val))

    updated = 0
    total = students.count_documents({})

    for doc in students.find({}):
        phone = doc.get("phone") or doc.get("contact")
        if not phone or str(phone).strip() == "":
            newnum = generate_mobile(existing_numbers)
            existing_numbers.add(newnum)
            students.update_one({"_id": doc["_id"]}, {"$set": {"phone": newnum, "contact": newnum}})
            updated += 1

    print(f"Processed {total} students. Updated {updated} documents with generated parent phone numbers.")


if __name__ == "__main__":
    main()
