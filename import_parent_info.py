#!/usr/bin/env python3
"""
import_parent_info.py

Extract parent (father) name and contact number from PDF documents and
update the corresponding student records in the MongoDB database.

Usage:
    python import_parent_info.py file1.pdf file2.pdf ...

This script tries to do rudimentary text extraction from each PDF using
PyPDF2. It searches for enrollment numbers (assumed to follow a pattern)
and looks for nearby text that could be father name and phone number.

Because PDF layouts vary widely, the script prints what it parses and
allows you to confirm before updating the DB. You may need to tweak the
regular expressions or manual post-processing depending on the actual
format of your PDFs.
"""

import os
import re
import sys
from pymongo import MongoClient

# You may need to install PyPDF2: pip install PyPDF2
try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 is required for PDF parsing. Install with `pip install PyPDF2`.")
    sys.exit(1)

MONGO_URL = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGO_DB_NAME", "rk_world")

# regex patterns (modify as needed)
ENROLL_RE = re.compile(r"(\b[0-9A-Z]{6,}\b)")  # simple alnum token guess
PHONE_RE = re.compile(r"(\b\d{10}\b)")
# attempt father name preceded by 'Father' or 'Fathers' etc
FATHER_RE = re.compile(r"Father\s*[:\-]?\s*([A-Za-z ]{3,})")


def parse_pdf(path):
    """Extract lines of text from a PDF file."""
    try:
        reader = PdfReader(path)
    except Exception as e:
        print(f"Failed to open {path}: {e}")
        return []

    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text())
        except Exception:
            continue
    return texts


def extract_info(text):
    """Return list of dicts with enrollment, father_name, father_contact if found."""
    results = []
    lines = text.split("\n") if text else []
    for line in lines:
        enroll = None
        phone = None
        father = None
        # find enrollment
        m = ENROLL_RE.search(line)
        if m:
            enroll = m.group(1)
        # father name
        m = FATHER_RE.search(line)
        if m:
            father = m.group(1).strip()
        m = PHONE_RE.search(line)
        if m:
            phone = m.group(1)
        if enroll:
            results.append({"enrollment": enroll, "father": father, "phone": phone, "line": line})
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_parent_info.py file1.pdf file2.pdf ...")
        sys.exit(1)

    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    try:
        client.server_info()
    except Exception as e:
        print("MongoDB connection error:", e)
        sys.exit(1)
    db = client[DB_NAME]
    students = db["students"]

    updates = []
    for pdf in sys.argv[1:]:
        if not os.path.exists(pdf):
            print("File not found:", pdf)
            continue
        print(f"Parsing {pdf}...")
        texts = parse_pdf(pdf)
        for text in texts:
            info_list = extract_info(text)
            for info in info_list:
                enroll = info.get("enrollment")
                father = info.get("father")
                phone = info.get("phone")
                if not father and not phone:
                    continue
                updates.append((enroll, father, phone, info.get("line")))

    if not updates:
        print("No matching info found in provided PDFs.")
        return

    print("\nFound the following extracted records:")
    for enroll, father, phone, line in updates:
        print(enroll, father or "(no father)", phone or "(no phone)", "->", line)

    confirm = input("Apply these updates to the database? (yes/no) ")
    if confirm.lower() not in ["yes", "y"]:
        print("Update cancelled.")
        return

    for enroll, father, phone, _ in updates:
        query = {"enrollment_no": enroll}
        set_fields = {}
        if father:
            set_fields["father_name"] = father
        if phone:
            set_fields["father_contact"] = phone
        if set_fields:
            result = students.update_many(query, {"$set": set_fields})
            print(f"Updated {result.modified_count} records for {enroll}")

    print("Done.")


if __name__ == "__main__":
    main()
