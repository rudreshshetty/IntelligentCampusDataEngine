"""Backfill missing student contact data.

Usage:
  python backfill_students.py         # runs in non-dry mode and applies updates
  python backfill_students.py --dry  # shows what would change without applying

The script uses the MONGODB_URI environment variable (defaults to mongodb://localhost:27017/)
and the `rk_world` database and `students` collection (same as `app.py`).
"""
import os
import random
import argparse
from pymongo import MongoClient
from bson.objectid import ObjectId

DEFAULT_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "rk_world"
COLLECTION = "students"

PHONE_PREFIXES = ["9", "8", "7"]


def gen_phone():
    # Generate a 10-digit phone number starting with common Indian prefixes
    prefix = random.choice(PHONE_PREFIXES)
    return prefix + ''.join(str(random.randint(0, 9)) for _ in range(9))


def gen_email(name, username=None):
    base = username or (name or "student").lower().replace(' ', '.')
    num = random.randint(10, 999)
    # fixed domain per requirements
    domain = "example.com"
    return f"{base}{num}@{domain}"


def main(dry=False, force=False):
    client = MongoClient(DEFAULT_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    students = db[COLLECTION]

    # Select all students; we'll decide per-student whether to update
    cursor = students.find({})
    updates = []
    count = 0
    for s in cursor:
        sid = str(s.get("_id"))
        name = s.get("name") or s.get("username") or "student"
        username = s.get("username")
        update = {}
        if force or not s.get("email"):
            update["email"] = gen_email(name, username)
        if force or not s.get("phone"):
            update["phone"] = gen_phone()
        if force or not s.get("parent_contact"):
            # parent contact often differs; generate another phone
            update["parent_contact"] = gen_phone()

        if update:
            updates.append((sid, update))

    if not updates:
        print("No students need backfilling. Nothing to do.")
        return

    print(f"Found {len(updates)} students to update.")
    if dry:
        for sid, upd in updates:
            print(f"Would update {sid}: {upd}")
        return

    for sid, upd in updates:
        students.update_one({"_id": ObjectId(sid)}, {"$set": upd})
        count += 1

    print(f"Applied updates to {count} students.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill missing student contact data')
    parser.add_argument('--dry', action='store_true', help='Dry run (do not modify DB)')
    parser.add_argument('--force', action='store_true', help='Also overwrite existing values')
    args = parser.parse_args()
    main(dry=args.dry, force=args.force)
