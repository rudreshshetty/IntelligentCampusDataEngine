#!/usr/bin/env python
"""Extract student data from Excel Attendance Reports"""

import win32com.client as win32
from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB Connection
MONGO_URL = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("MONGO_DB_NAME", "rk_world")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[DATABASE_NAME]
    students_collection = db["students"]
    print("✓ Connected to MongoDB successfully\n")
except Exception as e:
    print(f"✗ Error connecting to MongoDB: {e}")
    exit(1)

def extract_students_from_excel(file_path, section_name):
    """Extract student data from attendance report Excel file"""
    
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    excel.Visible = False
    
    students_list = []
    
    try:
        workbook = excel.Workbooks.Open(file_path)
        sheet = workbook.Sheets(1)  # First sheet
        
        used_range = sheet.UsedRange
        rows_count = used_range.Rows.Count
        cols_count = used_range.Columns.Count
        
        print(f"Processing {os.path.basename(file_path)}")
        print(f"  Sheet: '{sheet.Name}' | {rows_count} rows × {cols_count} columns")
        
        # Print all data to find the student list
        print("  Scanning for student data...")
        
        # Look for header row with student names
        header_row = None
        for row in range(1, min(rows_count + 1, 30)):  # Check first 30 rows
            row_data = []
            for col in range(1, min(cols_count + 1, 5)):
                cell_value = sheet.Cells(row, col).Value
                row_data.append(str(cell_value) if cell_value else "")
            row_text = " ".join(row_data).lower()
            if "roll no" in row_text or "name" in row_text or "student" in row_text:
                header_row = row
                print(f"    Found potential header at row {row}")
                break
        
        if not header_row:
            # If not found, look for the datastructure by checking for rows with data
            print("    Scanning entire sheet for student records...")
            for row in range(1, rows_count + 1):
                # Get first column - should contain roll numbers or names
                col1 = sheet.Cells(row, 1).Value
                col2 = sheet.Cells(row, 2).Value
                
                if col1 and col2:
                    cell_str = str(col1).strip()
                    # Check if it looks like a roll number or student entry
                    if (cell_str.isdigit() or 
                        any(x in cell_str.lower() for x in ['s-', 'roll', 'reg', 'enroll'])):
                        header_row = row - 1
                        print(f"    Found student data starting at row {row}")
                        break
        
        if header_row:
            print(f"  Data structure detected. Extracting students...")
            
            # Get header row to understand the structure
            headers = []
            for col in range(1, min(cols_count + 1, 10)):
                headers.append(sheet.Cells(header_row, col).Value)
            print(f"  Headers detected: {headers}")
            
            # Extract students starting from data row
            data_start_row = header_row + 1
            
            for row in range(data_start_row, rows_count + 1):
                # Get row data - looking for: SlNo, USN/Enrollment, Name, etc.
                col1 = sheet.Cells(row, 1).Value  # Sl.No (skip)
                col2 = sheet.Cells(row, 2).Value  # USN/Enrollment
                col3 = sheet.Cells(row, 3).Value  # Name
                col4 = sheet.Cells(row, 4).Value  # Course Code (optional)
                
                # Check if row has student data
                if not col2 or not col3:
                    continue
                
                col2_str = str(col2).strip()
                col3_str = str(col3).strip()
                
                # Skip if it looks like a summary row or header
                if col2_str.lower() in ['usn', 'total', 'grand total', 'subtotal', 'enrollment', '']:
                    continue
                if any(x in col2_str.lower() for x in ['total', 'course']):
                    continue
                
                # Skip empty or non-student rows
                if not col2_str or not col3_str:
                    continue
                
                # Create student record
                student_dict = {
                    'enrollment_no': col2_str,  # USN
                    'name': col3_str,  # Name
                    'section': section_name,
                    'branch': 'School of Applied Science',  # From the header
                }
                
                # Try to extract additional info if available
                if col4 and str(col4).strip():
                    student_dict['course_code'] = str(col4).strip()
                
                students_list.append(student_dict)
                
                if len(students_list) % 10 == 0:
                    print(f"    Extracted {len(students_list)} students...")
        
        else:
            print("  ! Could not detect student data structure")
            print("  Sample of first 20 rows:")
            for row in range(1, min(21, rows_count + 1)):
                row_data = []
                for col in range(1, min(6, cols_count + 1)):
                    row_data.append(sheet.Cells(row, col).Value)
                print(f"    Row {row}: {row_data}")
        
        workbook.Close(SaveChanges=False)
    
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            excel.Quit()
        except:
            pass
    
    return students_list

# Main execution
if __name__ == "__main__":
    print("=" * 70)
    print("STUDENT DATA EXTRACTION FROM ATTENDANCE REPORTS")
    print("=" * 70 + "\n")
    
    files = {
        r"c:\Users\Rahul\Downloads\a sec list.xls": "A",
        r"c:\Users\Rahul\Downloads\bsec list.xls": "B",
        r"c:\Users\Rahul\Downloads\c sec list.xls": "C"
    }
    
    all_students = []
    
    for file_path, section in files.items():
        if os.path.exists(file_path):
            students = extract_students_from_excel(file_path, section)
            all_students.extend(students)
            print(f"  ✓ Extracted {len(students)} students from Section {section}\n")
        else:
            print(f"  ✗ File not found: {file_path}\n")
    
    if all_students:
        print(f"\n{'='*70}")
        print(f"SUMMARY: Total {len(all_students)} students ready to import")
        print('='*70)
        
        # Show sample
        print("\nSample students:")
        for student in all_students[:3]:
            print(f"  • {student}")
        
        print("\n⚠️  This will DELETE all existing student data.")
        print("Proceeding with import...\n")
        
        if True:  # Auto-confirm
            try:
                # Clear existing data
                deleted_count = students_collection.delete_many({}).deleted_count
                print(f"\n✓ Deleted {deleted_count} existing students")
                
                # Insert new data
                result = students_collection.insert_many(all_students)
                print(f"✓ Inserted {len(result.inserted_ids)} new students")
                
                print("\n✓ Data import completed successfully!")
                
                # Verify
                total = students_collection.count_documents({})
                print(f"✓ Total students in database now: {total}")
            
            except Exception as e:
                print(f"✗ Error during import: {e}")
        else:
            print("Import cancelled.")
    else:
        print("\n✗ No student data extracted from Excel files")
