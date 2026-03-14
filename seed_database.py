from pymongo import MongoClient
from datetime import datetime

# MongoDB Connection
MONGO_URL = "mongodb://localhost:27017/"
DATABASE_NAME = "rk_world"

client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
users = db["users"]
students = db["students"]
lecturers = db["lecturers"]
employees = db["employees"]

def seed_users():
    """Insert demo users into the users collection"""
    
    # Clear existing users (optional)
    users.delete_many({})
    
    demo_users = [
        # ==================== STUDENTS ====================
        {
            "username": "student1",
            "password": "pass",
            "role": "student",
            "name": "Rahul Kumar",
            "email": "rahul.kumar@university.edu"
        },
        {
            "username": "student2",
            "password": "pass",
            "role": "student",
            "name": "Priya Singh",
            "email": "priya.singh@university.edu"
        },
        {
            "username": "student3",
            "password": "pass",
            "role": "student",
            "name": "Aman Patel",
            "email": "aman.patel@university.edu"
        },
        {
            "username": "student4",
            "password": "pass",
            "role": "student",
            "name": "Neha Sharma",
            "email": "neha.sharma@university.edu"
        },
        {
            "username": "student5",
            "password": "pass",
            "role": "student",
            "name": "Vikas Gupta",
            "email": "vikas.gupta@university.edu"
        },
        {
            "username": "student6",
            "password": "pass",
            "role": "student",
            "name": "Anjali Verma",
            "email": "anjali.verma@university.edu"
        },
        {
            "username": "student7",
            "password": "pass",
            "role": "student",
            "name": "Rohan Desai",
            "email": "rohan.desai@university.edu"
        },
        {
            "username": "student8",
            "password": "pass",
            "role": "student",
            "name": "Kavya Reddy",
            "email": "kavya.reddy@university.edu"
        },
        {
            "username": "student9",
            "password": "pass",
            "role": "student",
            "name": "Arjun Nair",
            "email": "arjun.nair@university.edu"
        },
        {
            "username": "student10",
            "password": "pass",
            "role": "student",
            "name": "Divya Chakraborty",
            "email": "divya.chakraborty@university.edu"
        },
        {
            "username": "student11",
            "password": "pass",
            "role": "student",
            "name": "Vishal Pandey",
            "email": "vishal.pandey@university.edu"
        },
        {
            "username": "student12",
            "password": "pass",
            "role": "student",
            "name": "Shreya Bansal",
            "email": "shreya.bansal@university.edu"
        },
        {
            "username": "student13",
            "password": "pass",
            "role": "student",
            "name": "Nikhil Agarwal",
            "email": "nikhil.agarwal@university.edu"
        },
        {
            "username": "student14",
            "password": "pass",
            "role": "student",
            "name": "Pooja Khanna",
            "email": "pooja.khanna@university.edu"
        },
        {
            "username": "student15",
            "password": "pass",
            "role": "student",
            "name": "Saurabh Singh",
            "email": "saurabh.singh@university.edu"
        },
        
        # ==================== LECTURERS ====================
        {
            "username": "lecturer1",
            "password": "pass",
            "role": "lecturer",
            "name": "Dr. John Smith",
            "email": "john.smith@university.edu",
            "subject": "Mathematics"
        },
        {
            "username": "lecturer2",
            "password": "pass",
            "role": "lecturer",
            "name": "Prof. Sarah Johnson",
            "email": "sarah.johnson@university.edu",
            "subject": "Physics"
        },
        {
            "username": "lecturer3",
            "password": "pass",
            "role": "lecturer",
            "name": "Mrs. Emily Davis",
            "email": "emily.davis@university.edu",
            "subject": "Chemistry"
        },
        {
            "username": "lecturer4",
            "password": "pass",
            "role": "lecturer",
            "name": "Mr. Robert Wilson",
            "email": "robert.wilson@university.edu",
            "subject": "English"
        },
        {
            "username": "lecturer5",
            "password": "pass",
            "role": "lecturer",
            "name": "Dr. Michael Brown",
            "email": "michael.brown@university.edu",
            "subject": "Computer Science"
        },
        {
            "username": "lecturer6",
            "password": "pass",
            "role": "lecturer",
            "name": "Prof. Lisa Anderson",
            "email": "lisa.anderson@university.edu",
            "subject": "Biology"
        },
        {
            "username": "lecturer7",
            "password": "pass",
            "role": "lecturer",
            "name": "Dr. James Taylor",
            "email": "james.taylor@university.edu",
            "subject": "Economics"
        },
        {
            "username": "lecturer8",
            "password": "pass",
            "role": "lecturer",
            "name": "Mrs. Angela Martinez",
            "email": "angela.martinez@university.edu",
            "subject": "History"
        },
        
        # ==================== ADMINS ====================
        {
            "username": "admin1",
            "password": "pass",
            "role": "admin",
            "name": "Admin User",
            "email": "admin@university.edu",
            "permissions": "Full Access"
        },
        {
            "username": "admin2",
            "password": "pass",
            "role": "admin",
            "name": "Manager",
            "email": "manager@university.edu",
            "permissions": "Full Access"
        }
    ]
    
    result = users.insert_many(demo_users)
    return result.inserted_ids

def seed_students():
    """Insert demo student details"""
    
    students.delete_many({})
    
    student_details = [
        {
            "username": "student1",
            "name": "Rahul Kumar",
            "email": "rahul.kumar@university.edu",
            "phone": "9876543210",
            "enrollment_no": "CS001",
            "semester": 3,
            "branch": "Computer Science",
            "admission_date": datetime(2023, 8, 15)
        },
        {
            "username": "student2",
            "name": "Priya Singh",
            "email": "priya.singh@university.edu",
            "phone": "9876543211",
            "enrollment_no": "CS002",
            "semester": 3,
            "branch": "Computer Science",
            "admission_date": datetime(2023, 8, 15)
        },
        {
            "username": "student3",
            "name": "Aman Patel",
            "email": "aman.patel@university.edu",
            "phone": "9876543212",
            "enrollment_no": "EC001",
            "semester": 2,
            "branch": "Electronics",
            "admission_date": datetime(2024, 8, 20)
        },
        {
            "username": "student4",
            "name": "Neha Sharma",
            "email": "neha.sharma@university.edu",
            "phone": "9876543213",
            "enrollment_no": "ME001",
            "semester": 4,
            "branch": "Mechanical Engineering",
            "admission_date": datetime(2023, 7, 10)
        },
        {
            "username": "student5",
            "name": "Vikas Gupta",
            "email": "vikas.gupta@university.edu",
            "phone": "9876543214",
            "enrollment_no": "CS003",
            "semester": 1,
            "branch": "Computer Science",
            "admission_date": datetime(2024, 9, 1)
        },
        {
            "username": "student6",
            "name": "Anjali Verma",
            "email": "anjali.verma@university.edu",
            "phone": "9876543215",
            "enrollment_no": "EC002",
            "semester": 2,
            "branch": "Electronics",
            "admission_date": datetime(2024, 8, 20)
        },
        {
            "username": "student7",
            "name": "Rohan Desai",
            "email": "rohan.desai@university.edu",
            "phone": "9876543216",
            "enrollment_no": "ME002",
            "semester": 3,
            "branch": "Mechanical Engineering",
            "admission_date": datetime(2023, 8, 15)
        },
        {
            "username": "student8",
            "name": "Kavya Reddy",
            "email": "kavya.reddy@university.edu",
            "phone": "9876543217",
            "enrollment_no": "CS004",
            "semester": 2,
            "branch": "Computer Science",
            "admission_date": datetime(2024, 8, 20)
        },
        {
            "username": "student9",
            "name": "Arjun Nair",
            "email": "arjun.nair@university.edu",
            "phone": "9876543218",
            "enrollment_no": "CE001",
            "semester": 4,
            "branch": "Civil Engineering",
            "admission_date": datetime(2023, 7, 10)
        },
        {
            "username": "student10",
            "name": "Divya Chakraborty",
            "email": "divya.chakraborty@university.edu",
            "phone": "9876543219",
            "enrollment_no": "CS005",
            "semester": 1,
            "branch": "Computer Science",
            "admission_date": datetime(2024, 9, 1)
        },
        {
            "username": "student11",
            "name": "Vishal Pandey",
            "email": "vishal.pandey@university.edu",
            "phone": "9876543220",
            "enrollment_no": "EC003",
            "semester": 3,
            "branch": "Electronics",
            "admission_date": datetime(2023, 8, 15)
        },
        {
            "username": "student12",
            "name": "Shreya Bansal",
            "email": "shreya.bansal@university.edu",
            "phone": "9876543221",
            "enrollment_no": "IT001",
            "semester": 2,
            "branch": "Information Technology",
            "admission_date": datetime(2024, 8, 20)
        },
        {
            "username": "student13",
            "name": "Nikhil Agarwal",
            "email": "nikhil.agarwal@university.edu",
            "phone": "9876543222",
            "enrollment_no": "CS006",
            "semester": 4,
            "branch": "Computer Science",
            "admission_date": datetime(2023, 7, 10)
        },
        {
            "username": "student14",
            "name": "Pooja Khanna",
            "email": "pooja.khanna@university.edu",
            "phone": "9876543223",
            "enrollment_no": "ME003",
            "semester": 1,
            "branch": "Mechanical Engineering",
            "admission_date": datetime(2024, 9, 1)
        },
        {
            "username": "student15",
            "name": "Saurabh Singh",
            "email": "saurabh.singh@university.edu",
            "phone": "9876543224",
            "enrollment_no": "CE002",
            "semester": 2,
            "branch": "Civil Engineering",
            "admission_date": datetime(2024, 8, 20)
        }
    ]
    
    result = students.insert_many(student_details)
    return result.inserted_ids

def seed_lecturers():
    """Insert demo lecturer details"""
    
    lecturers.delete_many({})
    
    lecturer_details = [
        {
            "username": "lecturer1",
            "name": "Dr. John Smith",
            "email": "john.smith@university.edu",
            "phone": "9876543220",
            "subject": "Mathematics",
            "qualification": "Ph.D",
            "experience": "15 years",
            "department": "Science",
            "join_date": datetime(2010, 1, 15)
        },
        {
            "username": "lecturer2",
            "name": "Prof. Sarah Johnson",
            "email": "sarah.johnson@university.edu",
            "phone": "9876543221",
            "subject": "Physics",
            "qualification": "Ph.D",
            "experience": "12 years",
            "department": "Science",
            "join_date": datetime(2012, 3, 20)
        },
        {
            "username": "lecturer3",
            "name": "Mrs. Emily Davis",
            "email": "emily.davis@university.edu",
            "phone": "9876543222",
            "subject": "Chemistry",
            "qualification": "M.Sc",
            "experience": "8 years",
            "department": "Science",
            "join_date": datetime(2016, 6, 10)
        },
        {
            "username": "lecturer4",
            "name": "Mr. Robert Wilson",
            "email": "robert.wilson@university.edu",
            "phone": "9876543223",
            "subject": "English",
            "qualification": "M.A",
            "experience": "10 years",
            "department": "Humanities",
            "join_date": datetime(2014, 9, 1)
        },
        {
            "username": "lecturer5",
            "name": "Dr. Michael Brown",
            "email": "michael.brown@university.edu",
            "phone": "9876543224",
            "subject": "Computer Science",
            "qualification": "Ph.D",
            "experience": "11 years",
            "department": "Engineering",
            "join_date": datetime(2013, 2, 10)
        },
        {
            "username": "lecturer6",
            "name": "Prof. Lisa Anderson",
            "email": "lisa.anderson@university.edu",
            "phone": "9876543225",
            "subject": "Biology",
            "qualification": "Ph.D",
            "experience": "14 years",
            "department": "Science",
            "join_date": datetime(2010, 8, 5)
        },
        {
            "username": "lecturer7",
            "name": "Dr. James Taylor",
            "email": "james.taylor@university.edu",
            "phone": "9876543226",
            "subject": "Economics",
            "qualification": "Ph.D",
            "experience": "9 years",
            "department": "Commerce",
            "join_date": datetime(2015, 4, 15)
        },
        {
            "username": "lecturer8",
            "name": "Mrs. Angela Martinez",
            "email": "angela.martinez@university.edu",
            "phone": "9876543227",
            "subject": "History",
            "qualification": "M.A",
            "experience": "7 years",
            "department": "Humanities",
            "join_date": datetime(2017, 7, 20)
        }
    ]
    
    result = lecturers.insert_many(lecturer_details)
    return result.inserted_ids

def seed_employees():
    """Insert demo employee details"""
    
    employees.delete_many({})
    
    employee_details = [
        {
            "name": "Rajesh Kumar",
            "email": "rajesh@university.edu",
            "phone": "9876543230",
            "position": "Librarian",
            "department": "Library",
            "salary": 35000,
            "hire_date": datetime(2015, 5, 12)
        },
        {
            "name": "Sunita Verma",
            "email": "sunita@university.edu",
            "phone": "9876543231",
            "position": "Office Manager",
            "department": "Administration",
            "salary": 30000,
            "hire_date": datetime(2018, 2, 1)
        },
        {
            "name": "Harsh Patel",
            "email": "harsh@university.edu",
            "phone": "9876543232",
            "position": "System Administrator",
            "department": "IT",
            "salary": 40000,
            "hire_date": datetime(2019, 7, 15)
        },
        {
            "name": "Meera Singh",
            "email": "meera@university.edu",
            "phone": "9876543233",
            "position": "Accountant",
            "department": "Finance",
            "salary": 32000,
            "hire_date": datetime(2020, 3, 10)
        }
    ]
    
    result = employees.insert_many(employee_details)
    return result.inserted_ids

def seed_fees():
    """Insert fee information for students"""
    
    fees_collection = db["fees"]
    fees_collection.delete_many({})
    
    student_usernames = [f"student{i}" for i in range(1, 16)]
    
    fees_data = []
    for student in student_usernames:
        fees_data.extend([
            {
                "student_id": student,
                "fee_type": "Tuition Fee",
                "amount": 50000,
                "due_date": datetime(2026, 3, 31),
                "status": "Pending",
                "semester": "Spring 2026"
            },
            {
                "student_id": student,
                "fee_type": "Library Fee",
                "amount": 5000,
                "due_date": datetime(2026, 3, 31),
                "status": "Pending",
                "semester": "Spring 2026"
            },
            {
                "student_id": student,
                "fee_type": "Lab Fee",
                "amount": 10000,
                "due_date": datetime(2026, 3, 31),
                "status": "Pending",
                "semester": "Spring 2026"
            },
            {
                "student_id": student,
                "fee_type": "Activity Fee",
                "amount": 3000,
                "due_date": datetime(2026, 3, 31),
                "status": "Paid",
                "paid_date": datetime(2026, 2, 10),
                "semester": "Spring 2026"
            }
        ])
    
    result = fees_collection.insert_many(fees_data)
    return result.inserted_ids

def seed_attendance():
    """Insert sample attendance records"""
    attendance = db["attendance"]
    attendance.delete_many({})

    records = []
    for i in range(1, 6):
        for d in range(1, 4):
            records.append({
                "student_username": f"student{i}",
                "date": datetime(2026, 3, d),
                "status": "Present" if d % 2 == 1 else "Absent",
                "marked_by": "lecturer1"
            })

    result = attendance.insert_many(records)
    return result.inserted_ids


def seed_assignments():
    """Insert sample assignments"""
    assignments_col = db["assignments"]
    assignments_col.delete_many({})

    assignments = [
        {
            "assignment_id": "A1",
            "title": "Intro to Algorithms",
            "description": "Solve exercise set 1",
            "course": "Computer Science",
            "posted_by": "lecturer5",
            "due_date": datetime(2026, 3, 20)
        },
        {
            "assignment_id": "A2",
            "title": "Physics Lab Report",
            "description": "Submit lab observations",
            "course": "Physics",
            "posted_by": "lecturer2",
            "due_date": datetime(2026, 3, 22)
        }
    ]

    result = assignments_col.insert_many(assignments)
    return result.inserted_ids


def seed_events():
    """Insert sample events"""
    events_col = db["events"]
    events_col.delete_many({})

    events = [
        {
            "title": "Orientation Day",
            "date": datetime(2026, 4, 1),
            "location": "Auditorium",
            "description": "Welcome new students"
        },
        {
            "title": "Tech Talk: AI",
            "date": datetime(2026, 4, 15),
            "location": "Lab 3",
            "description": "Guest lecture on AI trends"
        }
    ]

    result = events_col.insert_many(events)
    return result.inserted_ids


def seed_marks():
    """Insert sample marks for students"""
    marks_col = db["marks"]
    marks_col.delete_many({})

    marks = []
    for i in range(1, 11):
        marks.append({
            "student_username": f"student{i}",
            "subject": "Mathematics",
            "marks_obtained": 60 + (i % 40),
            "max_marks": 100,
            "exam_date": datetime(2026, 2, 20)
        })

    result = marks_col.insert_many(marks)
    return result.inserted_ids


def seed_payslips():
    """Insert sample payslips for employees"""
    payslips_col = db["payslips"]
    payslips_col.delete_many({})

    payslips = [
        {
            "employee_email": "rajesh@university.edu",
            "month": "February",
            "year": 2026,
            "gross": 35000,
            "net": 32000
        },
        {
            "employee_email": "harsh@university.edu",
            "month": "February",
            "year": 2026,
            "gross": 40000,
            "net": 36500
        }
    ]

    result = payslips_col.insert_many(payslips)
    return result.inserted_ids


def seed_punch_records():
    """Insert sample punch records for attendance machine"""
    punch_col = db["punch_records"]
    punch_col.delete_many({})

    punches = []
    for i in range(1, 5):
        punches.append({
            "employee": f"employee{i}",
            "date": datetime(2026, 3, 1),
            "in_time": datetime(2026, 3, 1, 9, 0),
            "out_time": datetime(2026, 3, 1, 17, 0)
        })

    result = punch_col.insert_many(punches)
    return result.inserted_ids


def seed_marked_attendance():
    """Insert sample marked attendance (manual adjustments)"""
    marked_col = db["marked_attendance"]
    marked_col.delete_many({})

    marked = [
        {"student_username": "student1", "date": datetime(2026, 3, 2), "status": "Excused", "reason": "Medical"},
        {"student_username": "student2", "date": datetime(2026, 3, 2), "status": "Late", "reason": "Transport"}
    ]

    result = marked_col.insert_many(marked)
    return result.inserted_ids


def seed_quizzes_and_submissions():
    """Insert quizzes and quiz submissions"""
    quizzes_col = db["quizzes"]
    subs_col = db["quiz_submissions"]
    quizzes_col.delete_many({})
    subs_col.delete_many({})

    quizzes = [
        {"quiz_id": "Q1", "title": "Week1 Quiz", "course": "Computer Science", "total_marks": 20, "date": datetime(2026, 3, 5)},
        {"quiz_id": "Q2", "title": "Week2 Quiz", "course": "Mathematics", "total_marks": 25, "date": datetime(2026, 3, 12)}
    ]

    quiz_ids = quizzes_col.insert_many(quizzes).inserted_ids

    submissions = [
        {"quiz_id": "Q1", "student_username": "student1", "marks_obtained": 18, "submitted_at": datetime(2026, 3, 5, 10, 0)},
        {"quiz_id": "Q1", "student_username": "student2", "marks_obtained": 15, "submitted_at": datetime(2026, 3, 5, 10, 5)},
    ]

    result = subs_col.insert_many(submissions)
    return list(quiz_ids) + list(result.inserted_ids)

def main():
    """Run all seeding functions"""
    print("🗄️  Starting Database Seeding...\n")
    
    try:
        print("📝 Seeding Users...")
        user_ids = seed_users()
        print(f"✓ {len(user_ids)} users created\n")
        
        print("👥 Seeding Students...")
        student_ids = seed_students()
        print(f"✓ {len(student_ids)} students created\n")
        
        print("👨‍🏫 Seeding Lecturers...")
        lecturer_ids = seed_lecturers()
        print(f"✓ {len(lecturer_ids)} lecturers created\n")
        
        print("🏢 Seeding Employees...")
        employee_ids = seed_employees()
        print(f"✓ {len(employee_ids)} employees created\n")
        
        print("💳 Seeding Fees...")
        fee_ids = seed_fees()
        print(f"✓ {len(fee_ids)} fee records created\n")

        print("📋 Seeding Attendance...")
        att_ids = seed_attendance()
        print(f"✓ {len(att_ids)} attendance records created\n")

        print("✏️  Seeding Assignments...")
        assign_ids = seed_assignments()
        print(f"✓ {len(assign_ids)} assignments created\n")

        print("🎫 Seeding Events...")
        event_ids = seed_events()
        print(f"✓ {len(event_ids)} events created\n")

        print("📊 Seeding Marks...")
        marks_ids = seed_marks()
        print(f"✓ {len(marks_ids)} marks records created\n")

        print("🏷️  Seeding Payslips...")
        payslip_ids = seed_payslips()
        print(f"✓ {len(payslip_ids)} payslips created\n")

        print("🕘 Seeding Punch Records...")
        punch_ids = seed_punch_records()
        print(f"✓ {len(punch_ids)} punch records created\n")

        print("🛠️  Seeding Marked Attendance...")
        marked_ids = seed_marked_attendance()
        print(f"✓ {len(marked_ids)} marked attendance records created\n")

        print("🧾 Seeding Quizzes & Submissions...")
        quiz_and_sub_ids = seed_quizzes_and_submissions()
        print(f"✓ {len(quiz_and_sub_ids)} quiz + submission records created\n")

        print("=" * 60)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n🔐 LOGIN CREDENTIALS:")
        print("  Student: student1 / pass")
        print("  Lecturer: lecturer1 / pass")
        print("  Admin: admin1 / pass")
        print("\n")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")

if __name__ == "__main__":
    main()
