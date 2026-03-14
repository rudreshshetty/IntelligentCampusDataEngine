from flask import Flask, render_template, request, redirect, session, send_file, jsonify, url_for
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.secret_key = "secret_key_rk_world"

# MongoDB Connection with timeout and graceful failure handling
from typing import cast
from pymongo.collection import Collection
from pymongo.database import Database

# Flag whether DB connection succeeded
db_connected = False
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")

# Pre-declare collection variables with a concrete type so static analyzers
# (Pylance) know these are MongoDB Collection objects even when we assign
# `None` at runtime in the error branch. We use `cast(Collection, None)` in
# the except branch to keep runtime behavior (None) while satisfying the
# type checker.
users: Collection
students: Collection
lecturers: Collection
attendance: Collection
assignments: Collection
events: Collection
fees: Collection
marks: Collection
employees: Collection
payslips: Collection
announcements: Collection
punch_records: Collection
marked_attendance: Collection
quizzes: Collection
quiz_submissions: Collection
db: Database

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Force a server selection to verify connection
    client.server_info()
    db = client["rk_world"]
    users = db["users"]
    students = db["students"]
    lecturers = db["lecturers"]
    attendance = db["attendance"]
    assignments = db["assignments"]
    events = db["events"]
    fees = db["fees"]
    marks = db["marks"]
    employees = db["employees"]
    payslips = db["payslips"]
    announcements = db["announcements"]
    punch_records = db["punch_records"]
    marked_attendance = db["marked_attendance"]
    quizzes = db["quizzes"]
    quiz_submissions = db["quiz_submissions"]
    db_connected = True
except ServerSelectionTimeoutError:
    # MongoDB not reachable; leave db variables as None and handle later.
    # Use `cast` so static type checkers treat these as Collection objects
    # (avoids warnings like "'find_one' is not a known attribute of 'None'").
    client = None
    db = cast(Database, None)
    users = cast(Collection, None)
    students = cast(Collection, None)
    lecturers = cast(Collection, None)
    attendance = cast(Collection, None)
    assignments = cast(Collection, None)
    events = cast(Collection, None)
    fees = cast(Collection, None)
    marks = cast(Collection, None)
    employees = cast(Collection, None)
    payslips = cast(Collection, None)
    announcements = cast(Collection, None)
    punch_records = cast(Collection, None)
    marked_attendance = cast(Collection, None)
    quizzes = cast(Collection, None)
    quiz_submissions = cast(Collection, None)


# ==================== SMS NOTIFICATION FUNCTION ====================
def send_sms_to_parent(parent_contact, student_name, subject, date, formatted_date):
    """
    Send SMS notification to parent about student absence.
    Currently logs the SMS; can be extended with Twilio or other providers.
    """
    try:
        # Format phone number (remove spaces/dashes if present)
        phone = str(parent_contact).strip()
        
        # SMS message content
        message = f"Hi, This is to inform that {student_name} was absent from the {subject} class on {formatted_date}. Please contact Sapthagiri NPS University if you need more information. Reply STOP to unsubscribe."
        
        # Store SMS record in database for audit trail
        if "sms_logs" not in db.list_collection_names():
            db.create_collection("sms_logs")
        
        sms_record = {
            "phone": phone,
            "student_name": student_name,
            "subject": subject,
            "date": date,
            "message": message,
            "status": "sent",
            "sent_timestamp": datetime.now(),
            "message_preview": message[:50] + "..."
        }
        
        db["sms_logs"].insert_one(sms_record)
        
        # Try Twilio if credentials exist
        try:
            from twilio.rest import Client
            import re
            
            account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
            twilio_from = os.environ.get("TWILIO_PHONE_NUMBER")
            
            if not all([account_sid, auth_token, twilio_from]):
                print("Missing Twilio credentials")
                return False
            
            # Clean phone number (remove spaces, dashes, etc.)
            phone_clean = re.sub(r"[^\d+]", "", str(phone))
            
            # Safe formatting
            if phone_clean.startswith("+"):
                formatted_phone = phone_clean
            elif phone_clean.startswith("91"):
                formatted_phone = f"+{phone_clean}"
            else:
                formatted_phone = f"+91{phone_clean.lstrip('0')}"
            
            client = Client(account_sid, auth_token)
            
            msg = client.messages.create(
                body=message,
                from_=twilio_from,
                to=formatted_phone
            )
            
            # Update DB safely
            try:
                if sms_record and "_id" in sms_record:
                    db["sms_logs"].update_one(
                        {"_id": sms_record["_id"]},
                        {"$set": {
                            "twilio_sid": msg.sid,
                            "status": "sent"
                        }}
                    )
            except Exception as db_error:
                print(f"DB update failed: {str(db_error)}")
            
            print(f"SMS sent to {formatted_phone}: {msg.sid}")
            return True

        except ImportError:
            print("Twilio not installed.")
            return False

        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
        
        # Update DB as failed (optional but safe)
        try:
            if sms_record and "_id" in sms_record:
                db["sms_logs"].update_one(
                    {"_id": sms_record["_id"]},
                    {"$set": {
                        "status": "failed",
                        "error": str(e)
                    }}
                )
        except:
            pass
        
        return False

    except Exception as e:
        print(f"Error in send_sms_to_parent: {str(e)}")
        return False

@app.route('/db_status')
def db_status():
    if db_connected and client:
        try:
            info = client.server_info()
            return jsonify({
                "connected": True,
                "version": info.get("version"),
                "host": mongodb_uri
            })
        except Exception as e:
            return jsonify({"connected": False, "error": str(e)}), 500
    return jsonify({"connected": False, "error": f"Cannot reach MongoDB at {mongodb_uri}"}), 503

# Upload folder
UPLOAD_FOLDER = os.path.join("static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==================== LOGIN SYSTEM ====================

@app.route('/')
def home():
    return login_page()

@app.route('/login_page')
def login_page():
    error = request.args.get('error', None)
    return render_template("login.html", error=error)

@app.route('/login', methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    selected_role = request.form.get("selected_role", "student").lower()

    if not db_connected:
        return (f"Database connection error: cannot reach MongoDB at {mongodb_uri}. "
                "Please start MongoDB and try again."), 503

    # Find user by username and password
    user = users.find_one({"username": username, "password": password})

    if not user:
        # User not found or password incorrect
        return redirect(url_for('login_page', error='invalid_credentials'))
    
    # Check if selected role matches user's actual role
    user_role = user.get("role", "").lower()
    
    if user_role != selected_role:
        # Role mismatch - user selected wrong role
        return redirect(url_for('login_page', error='role_mismatch'))

    # Authentication successful and role matches
    session["username"] = username
    session["role"] = user_role
    session["user_id"] = str(user.get("_id"))

    if user_role == "student":
        return redirect("/student")
    elif user_role == "lecturer":
        return redirect("/lecturer")
    else:
        return redirect("/admin")


# ==================== STUDENT DASHBOARD ====================

@app.route('/student')
def student_dashboard():
    if "username" not in session or session.get("role") != "student":
        return redirect("/")
    
    username = session["username"]
    student = students.find_one({"username": username})
    
    # Fetch fees and payments
    student_fees = list(fees.find({"student_id": username}))
    payments = list(db["payments"].find({"student_id": username}).sort("payment_date", -1))
    
    return render_template("student_dashboard.html", 
                         student=student,
                         student_fees=student_fees,
                         payments=payments)

@app.route('/upload_assignment', methods=["POST"])
def upload_assignment():
    if "username" not in session or session.get("role") != "student":
        return redirect("/")
    
    if "assignment" not in request.files:
        return "No file selected"
    
    file = request.files["assignment"]
    if not file or not file.filename:
        return "No file selected"
    
    filename = secure_filename(file.filename) if file.filename else "uploaded_file"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    # Store in database
    assignments.insert_one({
        "student_id": session["username"],
        "filename": filename,
        "upload_date": datetime.now(),
        "status": "Submitted"
    })
    
    return "Assignment Uploaded Successfully"

@app.route('/view_attendance')
def view_attendance():
    if "username" not in session or session.get("role") != "student":
        return redirect("/")
    
    student_attendance = list(attendance.find({"student_id": session["username"]}))
    return render_template("student_dashboard.html", attendance=student_attendance)

# ==================== FEES PAYMENT SYSTEM ====================

@app.route('/pay_fee/<fee_id>', methods=["POST"])
def pay_fee(fee_id):
    if "username" not in session or session.get("role") != "student":
        return redirect("/")
    
    amount = request.form.get("amount", "0")
    payment_method = request.form.get("payment_method", "Unknown")
    
    try:
        # Create payment record
        payment_data = {
            "student_id": session["username"],
            "fee_id": fee_id,
            "amount": float(amount) if amount else 0.0,
            "payment_method": payment_method,
            "payment_date": datetime.now(),
            "status": "Completed",
            "transaction_id": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Insert payment record
        db["payments"].insert_one(payment_data)
        
        # Update fee status (convert to ObjectId)
        try:
            oid = ObjectId(fee_id)
        except Exception:
            oid = fee_id
        fees.update_one(
            {"_id": oid, "student_id": session["username"]},
            {"$set": {"status": "Paid", "paid_date": datetime.now()}}
        )
        
        return f"Payment Successful! Transaction ID: {payment_data['transaction_id']}"
    except Exception as e:
        return f"Payment Failed: {str(e)}"

@app.route('/pay_fee_api', methods=["POST"])
def pay_fee_api():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        fee_type = data.get("fee_type")
        amount = data.get("amount")
        payment_method = data.get("payment_method")
        transaction_id = data.get("transaction_id")
        
        # Create payment record
        payment_data = {
            "student_id": session["username"],
            "fee_type": fee_type,
            "amount": float(amount),
            "payment_method": payment_method,
            "payment_date": datetime.now(),
            "status": "Completed",
            "transaction_id": transaction_id
        }
        
        # Insert payment record
        db["payments"].insert_one(payment_data)
        
        # Update fee status in fees collection
        fees.update_one(
            {"student_id": session["username"], "fee_type": fee_type},
            {"$set": {"status": "Paid", "paid_date": datetime.now()}}
        )
        
        return jsonify({
            "status": "success", 
            "message": "Payment processed successfully",
            "transaction_id": transaction_id
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Payment failed: {str(e)}"
        }), 500

@app.route('/process_payment', methods=["POST"])
def process_payment():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        app.logger.debug(f"process_payment received data: {data}")
        fee_type = data.get("fee_type")
        amount = data.get("amount")
        payment_method = data.get("payment_method")
        transaction_id = data.get("transaction_id")
        fee_id = data.get("fee_id")
        
        # Basic validation
        if amount is None or transaction_id is None:
            return jsonify({"status": "error", "message": "Missing payment information"}), 400
        
        # Create payment record
        payment_data = {
            "student_id": session["username"],
            "fee_type": fee_type,
            "amount": float(amount),
            "payment_method": payment_method,
            "payment_date": datetime.now(),
            "status": "Completed",
            "transaction_id": transaction_id
        }
        
        # Insert payment record
        result = db["payments"].insert_one(payment_data)
        
        # Update fee status in fees collection. prefer id if available
        update_filter = {"student_id": session["username"]}
        if fee_id:
            try:
                update_filter["_id"] = ObjectId(fee_id)
            except Exception:
                update_filter["_id"] = fee_id
        elif fee_type:
            update_filter["fee_type"] = fee_type

        update_result = fees.update_one(
            update_filter,
            {"$set": {"status": "Paid", "paid_date": datetime.now()}}
        )
        if update_result.matched_count == 0:
            app.logger.warning(f"No fee record updated for filter {update_filter}")
        
        return jsonify({
            "status": "success", 
            "message": "Payment processed successfully",
            "transaction_id": transaction_id
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Payment failed: {str(e)}"
        }), 500

@app.route('/download_receipt/<transaction_id>')
def download_receipt(transaction_id):
    if "username" not in session or session.get("role") != "student":
        return redirect("/")
    
    try:
        # Fetch payment record
        payment = db["payments"].find_one({
            "transaction_id": transaction_id,
            "student_id": session["username"]
        })
        
        if not payment:
            return "Payment record not found", 404
        
        # Fetch student details
        student = students.find_one({"username": session["username"]})
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#43e97b'),
            spaceAfter=30,
            alignment=1
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Build PDF content
        elements = []
        
        # Header
        elements.append(Paragraph("PAYMENT RECEIPT", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # University Info
        elements.append(Paragraph("<b>SAPTHAGIRI NPS UNIVERSITY</b>", heading_style))
        elements.append(Paragraph("Excellence in Education", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Receipt Details
        receipt_data = [
            ["Receipt Details", ""],
            ["Receipt Number:", transaction_id],
            ["Date:", payment['payment_date'].strftime("%d-%m-%Y %H:%M:%S")],
            ["Status:", "Payment Received"],
        ]
        
        receipt_table = Table(receipt_data, colWidths=[2*inch, 3*inch])
        receipt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#43e97b')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ]))
        elements.append(receipt_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Student Details
        student_data = [
            ["Student Details", ""],
            ["Name:", student.get('name', 'N/A') if student else 'N/A'],
            ["Username:", session['username']],
            ["Enrollment No:", student.get('enrollment_no', 'N/A') if student else 'N/A'],
        ]
        
        student_table = Table(student_data, colWidths=[2*inch, 3*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#43e97b')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ]))
        elements.append(student_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment Details
        payment_data = [
            ["Payment Details", ""],
            ["Fee Type:", payment['fee_type']],
            ["Amount Paid:", f"₹{payment['amount']:,.2f}"],
            ["Payment Method:", payment['payment_method']],
            ["Payment Date:", payment['payment_date'].strftime("%d-%m-%Y")],
            ["Payment Time:", payment['payment_date'].strftime("%H:%M:%S")],
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 3*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#43e97b')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Footer
        elements.append(Paragraph("Thank you for your payment!", styles['Normal']))
        elements.append(Paragraph("For queries, contact: info@sapthagiri.edu", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("This is an electronically generated receipt. No signature required.", 
                                  ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                                                textColor=colors.grey)))
        
        # Build PDF
        doc.build(elements)
        
        # Reset buffer position
        pdf_buffer.seek(0)
        
        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Fee_Receipt_{transaction_id}.pdf'
        )
    except Exception as e:
        return f"Error generating receipt: {str(e)}", 500

@app.route('/get_fees')
def get_fees():
    if "username" not in session or session.get("role") != "student":
        return redirect("/")
    
    student_fees = list(fees.find({"student_id": session["username"]}))
    return render_template("student_dashboard.html", 
                         student_fees=student_fees,
                         total_fees=sum([f.get("amount", 0) for f in student_fees]))

# ==================== LECTURER DASHBOARD ====================

@app.route('/lecturer')
def lecturer_dashboard():
    if "username" not in session or session.get("role") != "lecturer":
        return redirect("/")
    
    lecturer = lecturers.find_one({"username": session["username"]})
    # fetch all students so the attendance table can render immediately
    all_students = list(students.find({}, {"_id": 0, "name": 1, "enrollment_no": 1,
                                           "phone": 1, "contact": 1, "parent_contact": 1}))
    # optionally sort by enrollment or name
    all_students.sort(key=lambda s: s.get("enrollment_no", ""))
    return render_template("lecturer_dashboard.html", lecturer=lecturer, all_students=all_students)

@app.route('/update_attendance', methods=["POST"])
def update_attendance():
    if "username" not in session or session.get("role") != "lecturer":
        return redirect("/")
    
    student_id = request.form.get("student_id")
    status = request.form.get("status")
    date = request.form.get("date")
    
    attendance.insert_one({
        "student_id": student_id,
        "lecturer_id": session["username"],
        "date": date,
        "status": status
    })
    
    return "Attendance Updated"

@app.route('/send_absence_notification', methods=["POST"])
def send_absence_notification():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        student_name = data.get("student_name")
        enrollment_no = data.get("enrollment_no")
        parent_contact = data.get("parent_contact")
        date = data.get("date")
        subject = data.get("subject")
        time = data.get("time")
        
        # Format the date
        from datetime import datetime as dt
        formatted_date = dt.strptime(date, "%Y-%m-%d").strftime("%d-%b-%Y")
        
        # Create absence record
        absence_record = {
            "student_name": student_name,
            "enrollment_no": enrollment_no,
            "parent_contact": parent_contact,
            "subject": subject,
            "date": date,
            "time": time,
            "lecturer_id": session["username"],
            "notification_sent": True,
            "notification_timestamp": datetime.now(),
            "message_text": f"Hi, This is to inform that {student_name} was absent from the {subject} class on {formatted_date}. Please contact the university if you need more information. - Sapthagiri NPS University"
        }
        
        # Store in a new collection for notifications
        if "notifications" not in db.list_collection_names():
            db.create_collection("notifications")
        db["notifications"].insert_one(absence_record)
        
        # Also update attendance record
        attendance.insert_one({
            "student_name": student_name,
            "enrollment_no": enrollment_no,
            "subject": subject,
            "date": date,
            "status": "Absent",
            "lecturer_id": session["username"],
            "parent_notified": True,
            "parent_contact": parent_contact,
            "notification_time": datetime.now()
        })
        
        return jsonify({
            "status": "success",
            "message": "Notification sent to parent successfully",
            "parent_contact": parent_contact,
            "notification_id": str(absence_record.get("_id", ""))
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error sending notification: {str(e)}"
        }), 500

@app.route('/save_bulk_attendance', methods=["POST"])
def save_bulk_attendance():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        attendance_records = data.get("attendance_records", [])
        date = data.get("date")
        subject = data.get("subject")
        
        if not attendance_records:
            return jsonify({"status": "error", "message": "No attendance records provided"}), 400
        
        # Format the date
        from datetime import datetime as dt
        formatted_date = dt.strptime(date, "%Y-%m-%d").strftime("%d-%b-%Y")
        
        present_count = 0
        absent_count = 0
        absent_students = []
        
        # Process each attendance record
        for record in attendance_records:
            status = record.get("status")
            student_name = record.get("student_name")
            enrollment_no = record.get("enrollment_no")
            parent_contact = record.get("parent_contact")
            
            # Save attendance record
            attendance.insert_one({
                "student_name": student_name,
                "enrollment_no": enrollment_no,
                "subject": subject,
                "date": date,
                "status": status,
                "lecturer_id": session["username"],
                "marked_time": datetime.now(),
                "parent_contact": parent_contact,
                "parent_notified": True if status == "Absent" else False
            })
            
            if status == "Present":
                present_count += 1
            elif status == "Absent":
                absent_count += 1
                absent_students.append({
                    "student_name": student_name,
                    "enrollment_no": enrollment_no,
                    "parent_contact": parent_contact
                })
                
                # Send absence notification to parent
                absence_record = {
                    "student_name": student_name,
                    "enrollment_no": enrollment_no,
                    "parent_contact": parent_contact,
                    "subject": subject,
                    "date": date,
                    "lecturer_id": session["username"],
                    "notification_sent": True,
                    "notification_timestamp": datetime.now(),
                    "message_text": f"Hi, This is to inform that {student_name} was absent from the {subject} class on {formatted_date}. Please contact the university if you need more information. - Sapthagiri NPS University"
                }
                
                # Store in notifications collection
                if "notifications" not in db.list_collection_names():
                    db.create_collection("notifications")
                db["notifications"].insert_one(absence_record)
                
                # Send SMS to parent
                send_sms_to_parent(parent_contact, student_name, subject, date, formatted_date)
        
        # Prepare success message
        message_parts = [f"Attendance for {date} ({subject}) saved successfully!"]
        message_parts.append(f"✓ Present: {present_count} students")
        
        if absent_count > 0:
            message_parts.append(f"✗ Absent: {absent_count} students")
            message_parts.append("\nParents of absent students have been notified via SMS:")
            for student in absent_students[:5]:  # Show first 5
                message_parts.append(f"  • {student['student_name']} ({student['enrollment_no']})")
            if absent_count > 5:
                message_parts.append(f"  ... and {absent_count - 5} more")
        
        return jsonify({
            "status": "success",
            "message": "\n".join(message_parts),
            "present_count": present_count,
            "absent_count": absent_count,
            "total_students": len(attendance_records)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error saving attendance: {str(e)}"
        }), 500

@app.route('/update_marks', methods=["POST"])
def update_marks():
    if "username" not in session or session.get("role") != "lecturer":
        return redirect("/")
    
    student_id = request.form.get("student_id")
    subject = request.form.get("subject")
    marks_value = request.form.get("marks", "0")
    
    marks.update_one(
        {"student_id": student_id, "subject": subject},
        {"$set": {"marks": int(marks_value) if marks_value else 0, "lecturer_id": session["username"]}},
        upsert=True
    )
    
    return "Marks Updated"


@app.route('/get_all_students')
def get_all_students():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    # include phone and parent contact as well so the front‑end can display whichever is available
    student_list = list(students.find({}, {"_id": 0, "username": 1, "name": 1, "enrollment_no": 1,
                                           "phone": 1, "contact": 1, "parent_contact": 1}))
    return jsonify({"status": "success", "students": student_list}), 200


@app.route('/assign_internals_marks', methods=["POST"])
def assign_internals_marks():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        data = request.get_json()
        subject = data.get('subject')
        records = data.get('records', [])

        if not subject or not records:
            return jsonify({"status": "error", "message": "Subject and records required"}), 400

        saved = 0
        for r in records:
            enrollment = r.get('enrollment_no')
            student_name = r.get('student_name')
            marks_value = r.get('marks')

            # Find student username by enrollment (fallback to enrollment if not found)
            stu = students.find_one({"enrollment_no": enrollment})
            student_id = stu.get('username') if stu else enrollment

            marks.update_one(
                {"student_id": student_id, "subject": subject, "marks_type": "internals"},
                {"$set": {
                    "student_name": student_name,
                    "enrollment_no": enrollment,
                    "marks": int(marks_value) if marks_value != '' and marks_value is not None else None,
                    "marks_type": "internals",
                    "approval_status": "visible",
                    "lecturer_id": session["username"],
                    "assigned_date": datetime.now()
                }},
                upsert=True
            )
            saved += 1

        return jsonify({"status": "success", "message": f"Saved internals marks for {saved} students"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_counts')
def get_counts():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    try:
        from datetime import date
        today = date.today().isoformat()

        present = marked_attendance.count_documents({"date": today, "status": "Present"})
        absent = marked_attendance.count_documents({"date": today, "status": "Absent"})
        leave = marked_attendance.count_documents({"date": today, "status": "Leave"})

        return jsonify({
            "status": "success",
            "present": present,
            "absent": absent,
            "leave": leave
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/assign_exam_marks', methods=["POST"])
def assign_exam_marks():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        data = request.get_json()
        subject = data.get('subject')
        semester = data.get('semester')
        records = data.get('records', [])

        if not subject or not records:
            return jsonify({"status": "error", "message": "Subject and records required"}), 400

        saved = 0
        for r in records:
            enrollment = r.get('enrollment_no')
            student_name = r.get('student_name')
            marks_value = r.get('marks')

            # Find student username by enrollment (fallback to enrollment if not found)
            stu = students.find_one({"enrollment_no": enrollment})
            student_id = stu.get('username') if stu else enrollment

            marks.update_one(
                {"student_id": student_id, "subject": subject, "marks_type": "exam"},
                {"$set": {
                    "student_name": student_name,
                    "enrollment_no": enrollment,
                    "marks": int(marks_value) if marks_value != '' and marks_value is not None else None,
                    "semester": semester,
                    "marks_type": "exam",
                    "approval_status": "pending",
                    "lecturer_id": session["username"],
                    "submitted_date": datetime.now()
                }},
                upsert=True
            )
            saved += 1

        return jsonify({"status": "success", "message": f"Exam marks submitted for approval. {saved} students updated."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/assign_marks_bulk', methods=["POST"])
def assign_marks_bulk():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        data = request.get_json()
        subject = data.get('subject')
        records = data.get('records', [])

        if not subject or not records:
            return jsonify({"status": "error", "message": "Subject and records required"}), 400

        saved = 0
        for r in records:
            enrollment = r.get('enrollment_no')
            student_name = r.get('student_name')
            marks_value = r.get('marks')

            # Find student username by enrollment (fallback to enrollment if not found)
            stu = students.find_one({"enrollment_no": enrollment})
            student_id = stu.get('username') if stu else enrollment

            marks.update_one(
                {"student_id": student_id, "subject": subject},
                {"$set": {
                    "student_name": student_name,
                    "enrollment_no": enrollment,
                    "marks": int(marks_value) if marks_value != '' and marks_value is not None else None,
                    "lecturer_id": session["username"],
                    "assigned_date": datetime.now()
                }},
                upsert=True
            )
            saved += 1

        return jsonify({"status": "success", "message": f"Saved marks for {saved} students"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_student_attendance')
def get_student_attendance():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    try:
        # some attendance records store username in student_id, others use enrollment_no
        query = {"$or": [{"student_id": session["username"]}]}
        # look up enrollment to match bulk-inserted entries
        student = students.find_one({"username": session["username"]})
        if student and student.get("enrollment_no"):
            query["$or"].append({"enrollment_no": student.get("enrollment_no")})

        records = list(attendance.find(query).sort("date", -1))
        # convert dates to string if present
        for rec in records:
            rec['_id'] = str(rec.get('_id'))
            if rec.get('date'):
                rec['date'] = rec['date']
        return jsonify({"status": "success", "attendance": records}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_student_assignments')
def get_student_assignments():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    try:
        records = list(assignments.find({"student_id": session["username"]}).sort("upload_date", -1))
        for rec in records:
            rec['_id'] = str(rec.get('_id'))
            if rec.get('upload_date'):
                rec['upload_date'] = rec['upload_date'].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"status": "success", "assignments": records}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_student_fees')
def get_student_fees():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    try:
        records = list(fees.find({"student_id": session["username"]}).sort("due_date", 1))
        for rec in records:
            # convert ObjectId to string so JS can use it
            rec['_id'] = str(rec.get('_id'))
            # ensure due_date is JSON serializable
            if rec.get('due_date'):
                if hasattr(rec['due_date'], 'strftime'):
                    rec['due_date'] = rec['due_date'].strftime("%Y-%m-%d")
                else:
                    rec['due_date'] = str(rec['due_date'])
        return jsonify({"status": "success", "fees": records}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_student_marks')
def get_student_marks():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        student_id = session["username"]
        marks_type = request.args.get('marks_type', 'internals')  # Default to internals
        
        # For internals marks, get all marks_type='internals'
        # For exam marks, get only marks_type='exam' with approval_status='approved'
        if marks_type == 'internals':
            student_marks = list(marks.find({"student_id": student_id, "marks_type": "internals"}, {"_id": 0}))
        else:  # exam marks
            # Students should see exam marks only after admin publishes them
            student_marks = list(marks.find({
                "student_id": student_id,
                "marks_type": "exam",
                "approval_status": "published"
            }, {"_id": 0}))
        
        return jsonify({"status": "success", "marks": student_marks}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/approve_exam_marks/<marks_id>', methods=["POST"])
def approve_exam_marks(marks_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        # marks_id will be a combination of student_id and subject
        # Format: "student_id:subject"
        parts = marks_id.split(':')
        if len(parts) != 2:
            return jsonify({"status": "error", "message": "Invalid marks ID"}), 400
        
        student_id, subject = parts
        
        # When admin uses the quick-approve endpoint we treat that as immediate publish
        result = marks.update_one(
            {"student_id": student_id, "subject": subject, "marks_type": "exam"},
            {"$set": {"approval_status": "published", "approved_by": session['username'], "approved_at": datetime.now()}}
        )
        
        if result.matched_count > 0:
            return jsonify({"status": "success", "message": "Exam marks approved"}), 200
        else:
            return jsonify({"status": "error", "message": "Marks not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_pending_exam_marks')
def get_pending_exam_marks():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        # Optional semester filter
        semester = request.args.get('semester')
        query = {"marks_type": "exam", "approval_status": "pending"}
        if semester:
            query["semester"] = semester

        pending_marks = list(marks.find(query, {"_id": 0}))
        
        return jsonify({"status": "success", "pending_marks": pending_marks}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/approve_and_schedule', methods=['POST'])
def approve_and_schedule():
    """Admin endpoint to approve a subject's exam marks and schedule publication."""
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        subject = request.form.get('subject')
        semester = request.form.get('semester')
        academic_year = request.form.get('academic_year')
        title = request.form.get('title') or f"{subject} - Exam Results"
        message = request.form.get('message') or f"Results for {subject} are scheduled to be published."
        publish_date = request.form.get('publish_date')
        publish_time = request.form.get('publish_time')

        # subject may be None for semester-level scheduling
        if not publish_date or not publish_time:
            return jsonify({"status": "error", "message": "publish_date and publish_time required"}), 400

        publish_datetime = datetime.strptime(f"{publish_date} {publish_time}", "%Y-%m-%d %H:%M")

        # Approve marks: if subject provided, approve for that subject; otherwise approve for the whole semester
        if subject:
            marks.update_many(
                {"marks_type": "exam", "subject": subject, "approval_status": "pending"},
                {"$set": {"approval_status": "approved", "approved_by": session['username'], "approved_at": datetime.now()}}
            )
        elif semester:
            marks.update_many(
                {"marks_type": "exam", "semester": semester, "approval_status": "pending"},
                {"$set": {"approval_status": "approved", "approved_by": session['username'], "approved_at": datetime.now()}}
            )
        else:
            return jsonify({"status": "error", "message": "Either subject or semester required"}), 400

        # Insert a publication record so the background worker can publish at the scheduled time
        pub_record = {
            "subject": subject,
            "semester": semester,
            "academic_year": academic_year,
            "publish_date": publish_datetime,
            "created_by": session['username'],
            "created_at": datetime.now(),
            "status": "scheduled"
        }
        pub_res = db["result_publications"].insert_one(pub_record)

        # Create announcement entry to be published at the same time (status scheduled)
        results_file = None
        if "results_file" in request.files:
            file = request.files["results_file"]
            if file and file.filename:
                filename = secure_filename(file.filename) if file.filename else "results"
                filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                results_file = filename

        ann = {
            "title": title,
            "message": message,
            "semester": semester,
            "academic_year": academic_year,
            "publish_date": publish_datetime,
            "created_by": session['username'],
            "created_at": datetime.now(),
            "results_file": results_file,
            "status": "scheduled"
        }
        announcements.insert_one(ann)

        return jsonify({"status": "success", "message": "Marks approved and scheduled for publication", "publication_id": str(pub_res.inserted_id)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def _publish_scheduled_results_worker():
    """Background worker that publishes scheduled results when publish_date arrives."""
    while True:
        try:
            current_time = datetime.now()
            pubs = list(db["result_publications"].find({"status": "scheduled", "publish_date": {"$lte": current_time}}))
            for p in pubs:
                subject = p.get('subject')
                semester = p.get('semester')

                # If subject is provided publish marks for that subject, otherwise publish for the semester
                if subject:
                    res = marks.update_many(
                        {"marks_type": "exam", "subject": subject, "approval_status": {"$in": ["approved", "pending"]}},
                        {"$set": {"approval_status": "published", "published_at": datetime.now()}}
                    )
                elif semester:
                    res = marks.update_many(
                        {"marks_type": "exam", "semester": semester, "approval_status": {"$in": ["approved", "pending"]}},
                        {"$set": {"approval_status": "published", "published_at": datetime.now()}}
                    )
                else:
                    # nothing to publish
                    res = None

                # Update publication record
                db["result_publications"].update_one({"_id": p["_id"]}, {"$set": {"status": "published", "published_at": datetime.now()}})

                # Publish corresponding announcement(s) that were scheduled at same time
                db["announcements"].update_many({"publish_date": p.get("publish_date"), "status": "scheduled"}, {"$set": {"status": "published"}})

            # Sleep for 30 seconds before next check
            time.sleep(30)
        except Exception:
            # Sleep briefly on error to avoid tight loop
            time.sleep(5)


# Start background publisher thread when the DB connection is available
if db_connected:
    try:
        publisher_thread = threading.Thread(target=_publish_scheduled_results_worker, daemon=True)
        publisher_thread.start()
    except Exception:
        pass

@app.route('/assign_assignment', methods=["POST"])
def assign_assignment():
    if "username" not in session or session.get("role") != "lecturer":
        return redirect("/")
    
    title = request.form.get("title")
    description = request.form.get("description")
    deadline = request.form.get("deadline")
    
    assignments.insert_one({
        "lecturer_id": session["username"],
        "title": title,
        "description": description,
        "deadline": deadline,
        "assigned_date": datetime.now()
    })
    
    return "Assignment Assigned"


@app.route('/get_submissions')
def get_submissions():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        subs = list(assignments.find({"student_id": {"$exists": True}, "status": "Submitted"}))
        out = []
        for s in subs:
            student = students.find_one({"username": s.get('student_id')}) if s.get('student_id') else None
            filename = s.get('filename')
            file_url = url_for('static', filename=f"uploads/{filename}") if filename else ''
            out.append({
                "student_name": student.get('name') if student else s.get('student_id'),
                "enrollment_no": student.get('enrollment_no') if student else s.get('student_id'),
                "filename": filename,
                "file_url": file_url,
                "upload_date": s.get('upload_date').isoformat() if s.get('upload_date') else '',
                "assignment_title": s.get('title', '')
            })

        return jsonify({"status": "success", "submissions": out}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/upload_event_poster', methods=["POST"])
def upload_event_poster():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        title = request.form.get('title')
        date = request.form.get('date')
        file = request.files.get('poster')

        filename = None
        if file and file.filename:
            fname = secure_filename(file.filename)
            # add timestamp to filename to avoid clashes
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            file.save(save_path)
            filename = fname

        events.insert_one({
            'title': title,
            'date': date,
            'filename': filename,
            'uploaded_by': session['username'],
            'upload_date': datetime.now()
        })

        return jsonify({"status": "success", "message": "Event posted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_events')
def get_events():
    try:
        evs = list(events.find().sort('upload_date', -1))
        out = []
        for e in evs:
            filename = e.get('filename')
            file_url = url_for('static', filename=f"uploads/{filename}") if filename else ''
            out.append({
                'title': e.get('title'),
                'date': e.get('date'),
                'filename': filename,
                'file_url': file_url,
                'uploaded_by': e.get('uploaded_by'),
                'upload_date': e.get('upload_date').isoformat() if e.get('upload_date') else ''
            })

        return jsonify({"status": "success", "events": out}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== ADMIN DASHBOARD ====================

@app.route('/admin')
def admin_dashboard():
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")
    
    total_students = students.count_documents({})
    total_lecturers = lecturers.count_documents({})
    total_employees = employees.count_documents({})
    
    return render_template("admin_dashboard.html", 
                         total_students=total_students,
                         total_lecturers=total_lecturers,
                         total_employees=total_employees)

@app.route('/add_student', methods=["POST"])
def add_student():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        username = request.form.get("username")
        password = request.form.get("password")
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        parent_contact = request.form.get("parent_contact")
        admission_date_str = request.form.get("admission_date")
        
        # Validate required fields (parent contact optional)
        if not all([username, password, name, email, phone]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400
        
        # Check if username already exists
        if users.find_one({"username": username}):
            return jsonify({"status": "error", "message": "Username already exists"}), 400
        
        # Generate enrollment number
        enrollment_no = f"STU{students.count_documents({}) + 1:03d}"
        
        # parse admission_date or default to now
        try:
            if admission_date_str:
                admission_date = datetime.strptime(admission_date_str, "%Y-%m-%d")
            else:
                admission_date = datetime.now()
        except Exception:
            admission_date = datetime.now()
        
        # Add to users collection
        user_result = users.insert_one({
            "username": username,
            "password": password,
            "role": "student",
            "created_at": datetime.now()
        })
        
        # Add to students collection
        student_result = students.insert_one({
            "username": username,
            "user_id": str(user_result.inserted_id),
            "name": name,
            "email": email,
            "phone": phone,
            "parent_contact": parent_contact,
            "enrollment_no": enrollment_no,
            "admission_date": admission_date,
            "status": "Active"
        })
        
        return jsonify({
            "status": "success",
            "message": "Student added successfully",
            "student_id": str(student_result.inserted_id),
            "enrollment_no": enrollment_no
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/add_employee', methods=["POST"])
def add_employee():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        position = request.form.get("position")
        salary = request.form.get("salary")
        
        # Validate required fields
        if not all([name, email, phone, position, salary]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400
        
        # Generate employee ID
        emp_id = f"EMP{employees.count_documents({}) + 1:03d}"
        
        # Add to employees collection
        result = employees.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "position": position,
            "salary": float(salary) if salary else 0.0,
            "employee_id": emp_id,
            "hire_date": datetime.now(),
            "status": "Active"
        })
        # Also create a user account for this employee so they can log in (username = emp_id)
        try:
            users.insert_one({
                "username": emp_id,
                "password": "changeme",
                "role": "employee",
                "created_at": datetime.now()
            })
        except Exception:
            # ignore if user creation fails
            pass

        return jsonify({
            "status": "success",
            "message": "Employee added successfully",
            "employee_id": str(result.inserted_id),
            "emp_code": emp_id,
            "username": emp_id
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate_marks_card/<student_id>')
def generate_marks_card(student_id):
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")
    
    student = students.find_one({"username": student_id})
    student_marks = list(marks.find({"student_id": student_id}))
    
    if not student:
        return "Student not found"
    
    # Generate PDF
    filename = f"marks_card_{student_id}.pdf"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    c = canvas.Canvas(filepath)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "MARKS CARD")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"Student Name: {student.get('name', 'N/A')}")
    c.drawString(100, 700, f"Username: {student_id}")
    c.drawString(100, 680, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    y_position = 650
    for mark in student_marks:
        c.drawString(100, y_position, f"{mark.get('subject')}: {mark.get('marks')}/100")
        y_position -= 20
    
    c.save()
    return send_file(filepath, as_attachment=True)

# ==================== PUBLISH RESULTS ====================

@app.route('/publish_results', methods=["POST"])
def publish_results():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        semester = request.form.get("semester")
        academic_year = request.form.get("academic_year")
        title = request.form.get("title")
        message = request.form.get("message")
        publish_date = request.form.get("publish_date")
        publish_time = request.form.get("publish_time")
        
        # Combine date and time
        publish_datetime = datetime.strptime(f"{publish_date} {publish_time}", "%Y-%m-%d %H:%M")
        
        # Handle file upload
        results_file = None
        if "results_file" in request.files:
            file = request.files["results_file"]
            if file and file.filename:
                filename = secure_filename(file.filename) if file.filename else "uploaded_file"
                filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                results_file = filename
        
        # Insert into announcements collection
        announcement = {
            "title": title,
            "message": message,
            "semester": semester,
            "academic_year": academic_year,
            "publish_date": publish_datetime,
            "created_by": session["username"],
            "created_at": datetime.now(),
            "results_file": results_file,
            "status": "scheduled" if publish_datetime > datetime.now() else "published"
        }
        
        result = announcements.insert_one(announcement)
        
        return jsonify({
            "status": "success", 
            "message": "Results published successfully",
            "announcement_id": str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_announcements')
def get_announcements():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        # Get all published announcements
        current_time = datetime.now()
        announcements_list = list(announcements.find(
            {"publish_date": {"$lte": current_time}}
        ).sort("publish_date", -1))
        
        # Convert to JSON-serializable format
        for ann in announcements_list:
            ann['_id'] = str(ann['_id'])
            ann['publish_date'] = ann['publish_date'].strftime("%Y-%m-%d %H:%M")
            ann['created_at'] = ann['created_at'].strftime("%Y-%m-%d %H:%M")
        
        return jsonify({
            "status": "success",
            "announcements": announcements_list
        }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_admin_announcements')
def get_admin_announcements():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        # Get all announcements (scheduled and published)
        announcements_list = list(announcements.find().sort("publish_date", -1))
        
        for ann in announcements_list:
            ann['_id'] = str(ann['_id'])
            ann['publish_date'] = ann['publish_date'].strftime("%Y-%m-%d %H:%M")
            ann['created_at'] = ann['created_at'].strftime("%Y-%m-%d %H:%M")
        
        return jsonify({
            "status": "success",
            "announcements": announcements_list
        }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_announcement/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        result = announcements.delete_one({"_id": ObjectId(announcement_id)})
        
        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "Announcement deleted"}), 200
        else:
            return jsonify({"status": "error", "message": "Announcement not found"}), 404
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate_payslip/<employee_id>')
def generate_payslip(employee_id):
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")
    
    employee = employees.find_one({"_id": employee_id})
    
    if not employee:
        return "Employee not found"
    
    filename = f"payslip_{employee_id}.pdf"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    c = canvas.Canvas(filepath)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "PAYSLIP")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"Employee: {employee.get('name')}")
    c.drawString(100, 700, f"Position: {employee.get('position')}")
    c.drawString(100, 680, f"Salary: ${employee.get('salary')}")
    c.drawString(100, 660, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    c.save()
    return send_file(filepath, as_attachment=True)

# ==================== EMPLOYEE ATTENDANCE SYSTEM ====================

@app.route('/get_employee_of_day')
def get_employee_of_day():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        from datetime import date
        today = date.today().isoformat()
        
        # Get attendance statistics for today
        pipeline = [
            {
                "$match": {
                    "date": today,
                    "status": {"$in": ["Present", "On Time"]}
                }
            },
            {
                "$group": {
                    "_id": "$employee_id",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 1
            }
        ]
        
        result = list(marked_attendance.aggregate(pipeline))
        
        if result:
            emp_id = result[0]["_id"]
            emp = employees.find_one({"_id": ObjectId(emp_id)})
            
            if emp:
                # Get punch in time for today
                punch = punch_records.find_one({"employee_id": emp_id, "date": today})
                
                return jsonify({
                    "status": "success",
                    "employee": {
                        "_id": str(emp.get("_id")),
                        "name": emp.get("name", "N/A"),
                        "position": emp.get("position", "N/A"),
                        "punch_in": punch.get("punch_in_time", "Not recorded") if punch else "Not recorded"
                    }
                })
        
        return jsonify({
            "status": "success",
            "employee": {
                "name": "No Data",
                "position": "N/A",
                "punch_in": "N/A"
            }
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_todays_punch_summary')
def get_todays_punch_summary():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        from datetime import date
        today = date.today().isoformat()
        
        present = marked_attendance.count_documents({"date": today, "status": "Present"})
        absent = marked_attendance.count_documents({"date": today, "status": "Absent"})
        leave = marked_attendance.count_documents({"date": today, "status": "Leave"})
        
        return jsonify({
            "status": "success",
            "present": present,
            "absent": absent,
            "leave": leave
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_recent_punch_details')
def get_recent_punch_details():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        punches = list(punch_records.find().sort("_id", -1).limit(10))
        
        result = []
        for punch in punches:
            emp = employees.find_one({"_id": ObjectId(punch.get("employee_id"))})
            
            hours_worked = "-"
            status = "Incomplete"
            
            if punch.get("punch_out_time"):
                # Calculate hours worked
                from datetime import datetime
                try:
                    punch_in = datetime.strptime(punch.get("punch_in_time"), "%H:%M")
                    punch_out = datetime.strptime(punch.get("punch_out_time"), "%H:%M")
                    diff = (punch_out - punch_in).total_seconds() / 3600
                    hours_worked = f"{diff:.1f} hrs"
                    status = "On Time" if diff >= 8 else "Short Hours"
                except:
                    pass
            else:
                status = "Active"
            
            result.append({
                "emp_id": str(punch.get("employee_id")),
                "emp_name": emp.get("name", "Unknown") if emp else "Unknown",
                "punch_in_time": punch.get("punch_in_time", "N/A"),
                "punch_out_time": punch.get("punch_out_time", "N/A"),
                "hours_worked": hours_worked,
                "status": status
            })
        
        return jsonify({"status": "success", "punches": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_employees_list')
def get_employees_list():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        emps = list(employees.find({}, {"name": 1, "position": 1}))
        result = [{"_id": str(emp.get("_id")), "name": emp.get("name", "N/A"), "position": emp.get("position", "N/A")} for emp in emps]
        return jsonify({"status": "success", "employees": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_todays_punch_records')
def get_todays_punch_records():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        from datetime import date
        today = date.today().isoformat()
        
        punches = list(punch_records.find({"date": today}))
        
        result = []
        for punch in punches:
            emp = employees.find_one({"_id": ObjectId(punch.get("employee_id"))})
            
            hours_worked = "-"
            status = "Incomplete"
            
            if punch.get("punch_out_time"):
                from datetime import datetime
                try:
                    punch_in = datetime.strptime(punch.get("punch_in_time"), "%H:%M")
                    punch_out = datetime.strptime(punch.get("punch_out_time"), "%H:%M")
                    diff = (punch_out - punch_in).total_seconds() / 3600
                    hours_worked = f"{diff:.1f} hrs"
                    status = "Completed"
                except:
                    pass
            else:
                status = "Active"
            
            result.append({
                "_id": str(punch.get("_id")),
                "emp_name": emp.get("name", "Unknown") if emp else "Unknown",
                "punch_in_time": punch.get("punch_in_time", "N/A"),
                "punch_out_time": punch.get("punch_out_time") or "-",
                "hours_worked": hours_worked,
                "status": status
            })
        
        return jsonify({"status": "success", "punches": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/punch_in', methods=["POST"])
def punch_in():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        from datetime import date
        data = request.get_json()
        employee_id = data.get("employee_id")
        punch_time = data.get("punch_time")
        notes = data.get("notes", "")
        today = date.today().isoformat()
        
        # Check if already punched in
        existing = punch_records.find_one({
            "employee_id": employee_id,
            "date": today,
            "punch_in_time": {"$exists": True}
        })
        
        if existing:
            return jsonify({"status": "error", "message": "Employee already punched in today"}), 400
        
        punch_records.insert_one({
            "employee_id": employee_id,
            "date": today,
            "punch_in_time": punch_time,
            "punch_out_time": None,
            "notes": notes,
            "created_at": datetime.now()
        })
        
        return jsonify({"status": "success", "message": "Punch in recorded"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/punch_out', methods=["POST"])
def punch_out():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        from datetime import date
        data = request.get_json()
        employee_id = data.get("employee_id")
        punch_time = data.get("punch_time")
        notes = data.get("notes", "")
        today = date.today().isoformat()
        
        punch_records.update_one(
            {"employee_id": employee_id, "date": today},
            {
                "$set": {
                    "punch_out_time": punch_time,
                    "notes": notes,
                    "updated_at": datetime.now()
                }
            }
        )
        
        return jsonify({"status": "success", "message": "Punch out recorded"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/edit_punch', methods=["POST"])
def edit_punch():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        punch_id = data.get("punch_id")
        new_time = data.get("new_time")
        
        punch_records.update_one(
            {"_id": ObjectId(punch_id)},
            {"$set": {"punch_in_time": new_time, "updated_at": datetime.now()}}
        )
        
        return jsonify({"status": "success", "message": "Punch record updated"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_attendance_records', methods=["POST"])
def get_attendance_records():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        
        query = {"date": {"$gte": from_date, "$lte": to_date}}
        if employee_id:
            query["employee_id"] = employee_id
        
        records_list = list(punch_records.find(query).sort("date", -1))
        
        result = []
        for record in records_list:
            emp = employees.find_one({"_id": ObjectId(record.get("employee_id"))})
            
            hours_worked = "-"
            status = "Incomplete"
            
            if record.get("punch_out_time"):
                from datetime import datetime
                try:
                    punch_in = datetime.strptime(record.get("punch_in_time"), "%H:%M")
                    punch_out = datetime.strptime(record.get("punch_out_time"), "%H:%M")
                    diff = (punch_out - punch_in).total_seconds() / 3600
                    hours_worked = f"{diff:.1f} hrs"
                    status = "Completed"
                except:
                    pass
            
            result.append({
                "emp_name": emp.get("name", "Unknown") if emp else "Unknown",
                "date": record.get("date"),
                "punch_in": record.get("punch_in_time", "-"),
                "punch_out": record.get("punch_out_time", "-"),
                "hours_worked": hours_worked,
                "status": status,
                "notes": record.get("notes", "")
            })
        
        return jsonify({"status": "success", "records": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mark_attendance', methods=["POST"])
def mark_attendance():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        date_val = data.get("date")
        employee_id = data.get("employee_id")
        status = data.get("status")
        reason = data.get("reason", "")
        
        # Check if already marked
        existing = marked_attendance.find_one({
            "employee_id": employee_id,
            "date": date_val
        })
        
        if existing:
            # Update existing record
            marked_attendance.update_one(
                {"employee_id": employee_id, "date": date_val},
                {
                    "$set": {
                        "status": status,
                        "reason": reason,
                        "updated_at": datetime.now()
                    }
                }
            )
        else:
            # Create new record
            marked_attendance.insert_one({
                "employee_id": employee_id,
                "date": date_val,
                "status": status,
                "reason": reason,
                "marked_at": datetime.now()
            })
        
        return jsonify({"status": "success", "message": "Attendance marked successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_marked_attendance', methods=["POST"])
def get_marked_attendance():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        date_val = data.get("date")
        
        records_list = list(marked_attendance.find({"date": date_val}))
        
        result = []
        for record in records_list:
            emp = employees.find_one({"_id": ObjectId(record.get("employee_id"))})
            
            result.append({
                "_id": str(record.get("_id")),
                "emp_name": emp.get("name", "Unknown") if emp else "Unknown",
                "status": record.get("status"),
                "reason": record.get("reason", ""),
                "marked_at": record.get("marked_at", datetime.now())
            })
        
        return jsonify({"status": "success", "records": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_marked_attendance', methods=["POST"])
def delete_marked_attendance():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        
        marked_attendance.delete_one({"_id": ObjectId(record_id)})
        
        return jsonify({"status": "success", "message": "Record deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== QUIZ SYSTEM ====================

@app.route('/create_quiz', methods=["POST"])
def create_quiz():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        
        quiz_data = {
            "title": data.get("title"),
            "subject": data.get("subject"),
            "total_marks": data.get("total_marks"),
            "deadline": data.get("deadline"),
            "time_limit": data.get("time_limit"),
            "lecturer": session["username"],
            "lecturer_id": session.get("user_id"),
            "questions": data.get("questions", []),
            "created_at": datetime.now(),
            "attempt_count": 0
        }
        
        result = quizzes.insert_one(quiz_data)
        
        return jsonify({
            "status": "success",
            "message": "Quiz created successfully",
            "quiz_id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_lecturer_quizzes')
def get_lecturer_quizzes():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        lecturer_quizzes = list(quizzes.find({"lecturer": session["username"]}))
        
        result = []
        for quiz in lecturer_quizzes:
            result.append({
                "_id": str(quiz.get("_id")),
                "title": quiz.get("title"),
                "subject": quiz.get("subject"),
                "total_marks": quiz.get("total_marks"),
                "deadline": quiz.get("deadline"),
                "time_limit": quiz.get("time_limit"),
                "questions": quiz.get("questions", []),
                "attempt_count": quiz_submissions.count_documents({"quiz_id": str(quiz.get("_id"))})
            })
        
        return jsonify({"status": "success", "quizzes": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_quiz/<quiz_id>')
def get_quiz(quiz_id):
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        quiz = quizzes.find_one({"_id": ObjectId(quiz_id)})
        
        if not quiz:
            return jsonify({"status": "error", "message": "Quiz not found"}), 404
        
        # Get lecturer name
        lecturer = users.find_one({"username": quiz.get("lecturer")})
        lecturer_name = lecturer.get("username", "Unknown") if lecturer else "Unknown"
        
        return jsonify({
            "status": "success",
            "quiz": {
                "_id": str(quiz.get("_id")),
                "title": quiz.get("title"),
                "subject": quiz.get("subject"),
                "total_marks": quiz.get("total_marks"),
                "time_limit": quiz.get("time_limit"),
                "lecturer_name": lecturer_name,
                "questions": quiz.get("questions", [])
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_pending_quizzes')
def get_pending_quizzes():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        # Get all quizzes and filter out completed ones
        all_quizzes = list(quizzes.find())
        completed_quiz_ids = set(str(sub.get("quiz_id")) for sub in quiz_submissions.find({"student": session["username"]}))
        
        pending = []
        for quiz in all_quizzes:
            if str(quiz.get("_id")) not in completed_quiz_ids:
                lecturer = users.find_one({"username": quiz.get("lecturer")})
                lecturer_name = lecturer.get("username", "Unknown") if lecturer else "Unknown"
                
                pending.append({
                    "_id": str(quiz.get("_id")),
                    "title": quiz.get("title"),
                    "subject": quiz.get("subject"),
                    "total_marks": quiz.get("total_marks"),
                    "deadline": quiz.get("deadline"),
                    "time_limit": quiz.get("time_limit"),
                    "lecturer_name": lecturer_name,
                    "questions": quiz.get("questions", [])
                })
        
        return jsonify({"status": "success", "quizzes": pending})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_completed_quizzes')
def get_completed_quizzes():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        submissions = list(quiz_submissions.find({"student": session["username"]}).sort("submitted_at", -1))
        
        results = []
        for sub in submissions:
            quiz = quizzes.find_one({"_id": ObjectId(sub.get("quiz_id"))})
            if quiz:
                lecturer = users.find_one({"username": quiz.get("lecturer")})
                lecturer_name = lecturer.get("username", "Unknown") if lecturer else "Unknown"
                
                results.append({
                    "_id": str(sub.get("_id")),
                    "quiz_title": quiz.get("title"),
                    "subject": quiz.get("subject"),
                    "total_marks": quiz.get("total_marks"),
                    "marks_obtained": sub.get("marks_obtained", 0),
                    "correct_answers": sub.get("correct_answers", 0),
                    "wrong_answers": sub.get("wrong_answers", 0),
                    "percentage": round((sub.get("marks_obtained", 0) / quiz.get("total_marks", 1)) * 100),
                    "lecturer_name": lecturer_name,
                    "submitted_at": sub.get("submitted_at")
                })
        
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_quiz', methods=["POST"])
def submit_quiz():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        
        submission = {
            "quiz_id": data.get("quiz_id"),
            "student": session["username"],
            "student_id": session.get("user_id"),
            "answers": data.get("answers", {}),
            "marks_obtained": data.get("marks_obtained", 0),
            "correct_answers": data.get("correct_answers", 0),
            "wrong_answers": data.get("wrong_answers", 0),
            "total_marks": data.get("total_marks", 0),
            "submitted_at": datetime.now()
        }
        
        result = quiz_submissions.insert_one(submission)
        
        # Update quiz attempt count
        quizzes.update_one(
            {"_id": ObjectId(data.get("quiz_id"))},
            {"$inc": {"attempt_count": 1}}
        )
        
        return jsonify({
            "status": "success",
            "message": "Quiz submitted successfully",
            "submission_id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_quiz_results', methods=["POST"])
def get_quiz_results():
    if "username" not in session or session.get("role") != "lecturer":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        quiz_id = data.get("quiz_id")
        
        submissions = list(quiz_submissions.find({"quiz_id": quiz_id}))
        
        results = []
        for sub in submissions:
            student = students.find_one({"username": sub.get("student")})
            
            results.append({
                "_id": str(sub.get("_id")),
                "student_name": student.get("name", "Unknown") if student else "Unknown",
                "enrollment_no": student.get("enrollment_no", "N/A") if student else "N/A",
                "marks_obtained": sub.get("marks_obtained", 0),
                "total_marks": sub.get("total_marks", 0),
                "percentage": round((sub.get("marks_obtained", 0) / sub.get("total_marks", 1)) * 100),
                "correct_answers": sub.get("correct_answers", 0),
                "wrong_answers": sub.get("wrong_answers", 0),
                "submitted_at": sub.get("submitted_at")
            })
        
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_students_list')
def get_students_list():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        role = session.get("role")
        students_list = list(students.find().sort("admission_date", -1))
        
        result = []
        for student in students_list:
            student_data = {
                "_id": str(student.get("_id")),
                "username": student.get("username"),
                "name": student.get("name"),
                "email": student.get("email"),
                "phone": student.get("phone"),
                "parent_contact": student.get("parent_contact"),
                "enrollment_no": student.get("enrollment_no"),
                "admission_date": student.get("admission_date"),
                "status": student.get("status", "Active")
            }
            result.append(student_data)
        
        return jsonify({"status": "success", "students": result, "count": len(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_lecturers_list')
def get_lecturers_list():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not authorized"}), 401

    try:
        lecturers_list = list(lecturers.find().sort("join_date", -1))
        result = []
        for lec in lecturers_list:
            result.append({
                "_id": str(lec.get("_id")),
                "username": lec.get("username"),
                "name": lec.get("name"),
                "email": lec.get("email"),
                "subject": lec.get("subject")
            })

        return jsonify({"status": "success", "lecturers": result, "count": len(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_employees_admin_list')
def get_employees_admin_list():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        employees_list = list(employees.find().sort("hire_date", -1))
        
        result = []
        for emp in employees_list:
            emp_data = {
                "_id": str(emp.get("_id")),
                "name": emp.get("name"),
                "email": emp.get("email"),
                "phone": emp.get("phone"),
                "position": emp.get("position"),
                "salary": emp.get("salary"),
                "employee_id": emp.get("employee_id"),
                "hire_date": emp.get("hire_date"),
                "status": emp.get("status", "Active")
            }
            result.append(emp_data)
        
        return jsonify({"status": "success", "employees": result, "count": len(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_student/<student_id>')
def get_student(student_id):
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        # Student can only view their own info
        if session.get("role") == "student":
            student = students.find_one({"username": session["username"]})
        else:
            # Admin and lecturer can view any student
            student = students.find_one({"username": student_id}) or students.find_one({"_id": ObjectId(student_id)})
        
        if not student:
            return jsonify({"status": "error", "message": "Student not found"}), 404
        
        return jsonify({
            "status": "success",
            "student": {
                "_id": str(student.get("_id")),
                "username": student.get("username"),
                "name": student.get("name"),
                "email": student.get("email"),
                "phone": student.get("phone"),
                "parent_contact": student.get("parent_contact"),
                "enrollment_no": student.get("enrollment_no"),
                "admission_date": student.get("admission_date"),
                "status": student.get("status", "Active")
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/update_student/<student_id>', methods=["POST"])
def update_student(student_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        
        update_fields = {
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "status": data.get("status", "Active"),
            "updated_at": datetime.now()
        }

        # Optional fields
        if data.get("parent_contact") is not None:
            update_fields["parent_contact"] = data.get("parent_contact")
        if data.get("notes") is not None:
            update_fields["notes"] = data.get("notes")
        if data.get("username"):
            update_fields["username"] = data.get("username")
        if data.get("admission_date"):
            try:
                admission_date = datetime.strptime(data.get("admission_date"), "%Y-%m-%d")
                update_fields["admission_date"] = admission_date
            except Exception:
                pass  # Skip if date format is invalid
        
        # Handle password update if provided
        if data.get("password"):
            student = students.find_one({"_id": ObjectId(student_id)})
            if student:
                username = student.get("username")
                users.update_one({"username": username}, {"$set": {"password": data.get("password")}})
        
        students.update_one({"_id": ObjectId(student_id)}, {"$set": update_fields})
        
        return jsonify({"status": "success", "message": "Student updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_student/<student_id>', methods=["DELETE"])
def delete_student(student_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        student = students.find_one({"_id": ObjectId(student_id)})
        if student:
            username = student.get("username")
            users.delete_one({"username": username})
            students.delete_one({"_id": ObjectId(student_id)})
        
        return jsonify({"status": "success", "message": "Student deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_employee/<employee_id>')
def get_employee(employee_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        emp = employees.find_one({"_id": ObjectId(employee_id)})
        
        if not emp:
            return jsonify({"status": "error", "message": "Employee not found"}), 404
        
        return jsonify({
            "status": "success",
            "employee": {
                "_id": str(emp.get("_id")),
                "name": emp.get("name"),
                "email": emp.get("email"),
                "phone": emp.get("phone"),
                "position": emp.get("position"),
                "salary": emp.get("salary"),
                "employee_id": emp.get("employee_id"),
                "hire_date": emp.get("hire_date"),
                "status": emp.get("status", "Active")
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/student_edit/<student_id>')
def student_edit_page(student_id):
    if "username" not in session or session.get("role") != "admin":
        return redirect(url_for('login'))
    try:
        return render_template('student_edit.html')
    except Exception as e:
        return f"Error rendering page: {e}", 500


@app.route('/get_student_notifications')
def get_student_notifications():
    if "username" not in session or session.get("role") != "student":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        student = students.find_one({"username": session["username"]})
        if not student:
            return jsonify({"status": "error", "message": "Student not found"}), 404
        
        enrollment_no = student.get("enrollment_no")
        
        # Get all absence notifications for this student
        notifications_coll = db["notifications"]
        notifications = list(notifications_coll.find({
            "enrollment_no": enrollment_no
        }).sort("notification_timestamp", -1).limit(10))
        
        result = []
        for notif in notifications:
            result.append({
                "_id": str(notif.get("_id")),
                "student_name": notif.get("student_name"),
                "subject": notif.get("subject"),
                "date": notif.get("date"),
                "message_text": notif.get("message_text"),
                "timestamp": notif.get("notification_timestamp"),
                "notification_type": "Absence Alert"
            })
        
        return jsonify({"status": "success", "notifications": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/update_employee/<employee_id>', methods=["POST"])
def update_employee(employee_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        data = request.get_json()
        
        employees.update_one(
            {"_id": ObjectId(employee_id)},
            {
                "$set": {
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "phone": data.get("phone"),
                    "position": data.get("position"),
                    "salary": float(data.get("salary", 0)),
                    "status": data.get("status", "Active"),
                    "updated_at": datetime.now()
                }
            }
        )
        
        return jsonify({"status": "success", "message": "Employee updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_employee/<employee_id>', methods=["DELETE"])
def delete_employee(employee_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Not authorized"}), 401
    
    try:
        employees.delete_one({"_id": ObjectId(employee_id)})
        return jsonify({"status": "success", "message": "Employee deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== LOGOUT ====================

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
