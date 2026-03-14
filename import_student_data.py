#!/usr/bin/env python
"""Import student data from Excel files into MongoDB"""

import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB Connection
MONGO_URL = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("MONGO_DB_NAME", "rk_world")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client[DATABASE_NAME]
    students_collection = db["students"]
    print("✓ Connected to MongoDB successfully")
except Exception as e:
    print(f"✗ Error connecting to MongoDB: {e}")
    exit(1)

def import_excel_data(file_path, section_name):
    """Import student data from an Excel file"""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        print(f"\n📋 Reading {os.path.basename(file_path)}")
        print(f"   Columns found: {list(df.columns)}")
        print(f"   Total rows: {len(df)}")
        
        students_list = []
        for idx, row in df.iterrows():
            # Convert row to dictionary and handle NaN values
            student_dict = row.to_dict()
            # Remove NaN values
            student_dict = {k: v for k, v in student_dict.items() if pd.notna(v)}
            
            # Map common column names and ensure required fields
            mapped_student = {}
            
            # Map column names flexibly
            for col, value in student_dict.items():
                col_lower = str(col).lower().strip()
                
                if 'name' in col_lower:
                    mapped_student['name'] = str(value).strip()
                elif 'username' in col_lower or 'user name' in col_lower:
                    mapped_student['username'] = str(value).strip()
                elif 'email' in col_lower:
                    mapped_student['email'] = str(value).strip()
                elif 'phone' in col_lower or 'mobile' in col_lower or 'contact' in col_lower:
                    mapped_student['phone'] = str(value).strip()
                elif 'enrollment' in col_lower or 'enroll' in col_lower or 'id' in col_lower or 'roll' in col_lower:
                    mapped_student['enrollment_no'] = str(value).strip()
                elif 'semester' in col_lower:
                    try:
                        mapped_student['semester'] = int(value)
                    except:
                        mapped_student['semester'] = str(value).strip()
                elif 'branch' in col_lower or 'department' in col_lower or 'dept' in col_lower:
                    mapped_student['branch'] = str(value).strip()
                elif 'section' in col_lower:
                    mapped_student['section'] = str(value).strip()
                elif 'admission' in col_lower or 'date' in col_lower or 'doa' in col_lower:
                    try:
                        if isinstance(value, str):
                            mapped_student['admission_date'] = datetime.strptime(value, '%d-%m-%Y')
                        else:
                            mapped_student['admission_date'] = value
                    except:
                        mapped_student['admission_date'] = value
                else:
                    # Keep other columns as-is
                    mapped_student[col_lower] = value
            
            # Add section if not already in data
            if 'section' not in mapped_student:
                mapped_student['section'] = section_name
            
            # Ensure name field exists
            if 'name' not in mapped_student and 'username' in mapped_student:
                mapped_student['name'] = mapped_student['username']
            
            if 'name' in mapped_student:  # Only add if we have at least a name
                students_list.append(mapped_student)
        
        return students_list
    
    except Exception as e:
        print(f"✗ Error reading {file_path}: {e}")
        return []

# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("STUDENT DATA IMPORT TOOL")
    print("=" * 60)
    
    # Define file paths and their section mappings
    excel_files = {
        r"c:\Users\Rahul\Downloads\a sec list.xls": "A",
        r"c:\Users\Rahul\Downloads\bsec list.xls": "B",
        r"c:\Users\Rahul\Downloads\c sec list.xls": "C"
    }
    
    all_students = []
    
    # Read all Excel files
    for file_path, section in excel_files.items():
        if os.path.exists(file_path):
            students = import_excel_data(file_path, section)
            all_students.extend(students)
            print(f"   ✓ Loaded {len(students)} students from {section} section")
        else:
            print(f"   ✗ File not found: {file_path}")
    
    if all_students:
        print(f"\n📊 Total students to import: {len(all_students)}")
        
        # Clear existing data
        confirm = input("\n⚠️  This will DELETE all existing student data. Continue? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            try:
                deleted_count = students_collection.delete_many({}).deleted_count
                print(f"   ✓ Deleted {deleted_count} existing students")
                
                # Insert new data
                result = students_collection.insert_many(all_students)
                print(f"   ✓ Inserted {len(result.inserted_ids)} new students")
                
                print("\n✓ Data import completed successfully!")
                
                # Show sample
                print("\n📋 Sample of imported data:")
                sample = students_collection.find_one()
                if sample:
                    print(f"   {sample}")
            
            except Exception as e:
                print(f"✗ Error during import: {e}")
        else:
            print("Import cancelled.")
    else:
        print("\n✗ No student data found in Excel files")
