from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse

from .models import Event, Registration, Feedback
from .forms import EventForm, RegistrationForm, FeedbackForm
import uuid
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import qrcode
from io import BytesIO
from django.core.files import File
from django.core.mail import send_mail
from django.conf import settings
import pandas as pd
from django.contrib.auth.models import User
from .forms import CSVUploadForm

from django.core.mail import EmailMessage
import csv
from io import TextIOWrapper
from .utils import generate_certificate

@login_required
def download_certificate(request, certificate_id):
    registration = get_object_or_404(
        Registration,
        certificate_id=certificate_id
    )

    # ✅ FIX 3: Only allow the owner to download their certificate
    if registration.student != request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to download this certificate.")
        return redirect("student_dashboard")

    # ✅ FIX 4: Only issue certificate if attendance was marked
    if not registration.attendance:
        messages.error(request, "Certificate is only available after your attendance is marked.")
        return redirect("student_dashboard")

    return generate_certificate(registration)



@login_required
def bulk_upload(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            messages.error(request, "Please select a CSV file")
            return redirect("bulk_upload", event_id=event.id)

        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        count = 0

        for row in reader:
            if not Registration.objects.filter(
                event=event,
                college_id=row["college_id"]
            ).exists():

                Registration.objects.create(
                    event=event,
                    student=request.user,
                    full_name=row["full_name"],
                    college_id=row["college_id"],
                    email=row["email"],
                    transaction_id=str(uuid.uuid4())[:12],
                    attendance=False
                )

                count += 1

        messages.success(
            request,
            f"{count} participants uploaded successfully"
        )

        messages.success(request, "CSV uploaded successfully")
        return redirect("event_detail", event.id)

    return render(
        request,
        "bulk_upload.html",
        {"event": event}
    )


@login_required
def delete_registration(request, reg_id):
    registration = get_object_or_404(
        Registration,
        id=reg_id
    )

    event_id = registration.event.id

    registration.delete()

    messages.success(
        request,
        "Registration deleted successfully."
    )

    return redirect(
        "event_detail",
        event_id=event_id
    )

@login_required
def student_delete_registration(request, reg_id):
    registration = get_object_or_404(
        Registration,
        id=reg_id,
        student=request.user
    )

    registration.delete()

    messages.success(
        request,
        "Registration cancelled successfully."
    )

    return redirect("student_dashboard")

# =========================
# HOME
# =========================
def home(request):
    return redirect('login')


# =========================
# LOGIN
# =========================
def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.is_staff:
                return redirect('dashboard')
            return redirect('student_dashboard')

    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


# =========================
# SIGNUP
# =========================
def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        User.objects.create_user(
            username=username,
            password=password
        )

        messages.success(request, "Account created successfully")
        return redirect("login")

    return render(request, "signup.html")


# =========================
# EVENT LIST
# =========================
@login_required
def event_list(request):
    events = Event.objects.all()

    registered_event_ids = Registration.objects.filter(
        student=request.user
    ).values_list("event_id", flat=True)

    return render(request, "events.html", {
        "events": events,
        "registered_event_ids": registered_event_ids
    })


# =========================
# REGISTER EVENT
# =========================
from django.core.mail import EmailMessage
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File


# =========================
# REGISTER EVENT
# =========================
@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # =====================================
    # PREVENT DUPLICATE REGISTRATION
    # =====================================
    if Registration.objects.filter(
        student=request.user,
        event=event
    ).exists():
        messages.warning(
            request,
            "You have already registered for this event."
        )
        return redirect("student_dashboard")

    # =====================================
    # FORM SUBMISSION
    # =====================================
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            reg = form.save(commit=False)

            reg.student = request.user
            reg.event = event

            # SAVE FIRST
            reg.transaction_verified = False
            reg.save()

            # =====================================
            # QR CODE GENERATION (KEEP YOUR FORMAT)
            # =====================================
            qr_data = f"""
Registration ID: {reg.id}
Name: {reg.full_name}
College USN: {reg.college_id}
Email: {reg.email}
Event: {event.title}
Date: {event.date}
Venue: {event.venue}
Certificate ID: {reg.certificate_id}
SJB Institute of Technology
Campus Events Portal
"""

            qr = qrcode.make(qr_data)

            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)

            file_name = f"{reg.id}.png"

            reg.qr_code.save(
                file_name,
                File(buffer),
                save=True
            )

            # =====================================
            # EMAIL WITH QR ATTACHMENT (FIXED)
            # =====================================
            email = EmailMessage(
                subject="Event Registration Successful 🎉",
                body=f"""
Hello {reg.full_name},

You have successfully registered for:

Event: {event.title}
Date: {event.date}
Venue: {event.venue}
College USN: {reg.college_id}

Registration ID: {reg.id}
We will be reaching back to you once the Payment is verified

Thank you,
SJB Institute of Technology
Campus Events Portal
""",
                from_email=settings.EMAIL_HOST_USER,
                to=[reg.email],
            )
            email.send()


            # =====================================
            # SUCCESS MESSAGE
            # =====================================
            messages.success(
                request,
                "Registration successful! QR sent to email."
            )

            return redirect("student_dashboard")

    else:
        form = RegistrationForm()

    # =====================================
    # RENDER PAGE
    # =====================================
    return render(request, "register_event.html", {
        "form": form,
        "event": event
    })

@login_required
def scan_qr(request):
    if request.method == "POST":
        qr_image = request.FILES.get("qr_image")

        if qr_image:
            # TEMP DEMO LOGIC:
            # Mark latest registration attendance as Present

            latest_registration = Registration.objects.order_by("-id").first()

            if latest_registration:
                latest_registration.attendance = True
                latest_registration.save()

                messages.success(
                    request,
                    f"Attendance marked for {latest_registration.full_name}"
                )
            else:
                messages.error(
                    request,
                    "No registration found."
                )

        return redirect("scan_qr")

    return render(request, "scan_qr.html")


# =========================
# STUDENT DASHBOARD
# =========================
@login_required
def student_dashboard(request):
    events = Event.objects.all()

    registrations = Registration.objects.filter(
        student=request.user
    )

    registered_event_ids = registrations.values_list(
        "event_id",
        flat=True
    )

    return render(request, "student_dashboard.html", {
        "events": events,
        "registrations": registrations,
        "registered_event_ids": registered_event_ids
    })


# =========================
# FEEDBACK
# =========================
@login_required
def feedback_view(request, reg_id):
    registration = get_object_or_404(
        Registration,
        id=reg_id,
        student=request.user
    )

    if request.method == "POST":
        form = FeedbackForm(request.POST)

        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.registration = registration
            feedback.save()

            registration.feedback_submitted = True
            registration.save()

            return redirect("student_dashboard")

    else:
        form = FeedbackForm()

    return render(request, "feedback.html", {
        "form": form,
        "registration": registration
    })


# =========================
# CERTIFICATE
# =========================
from .utils import generate_certificate


# =========================
# ADMIN DASHBOARD
# =========================
@login_required
def dashboard(request):
    scheduled = Event.objects.filter(status="scheduled")
    ongoing = Event.objects.filter(status="ongoing")
    completed = Event.objects.filter(status="completed")

    return render(request, "dashboard.html", {
        "scheduled": scheduled,
        "ongoing": ongoing,
        "completed": completed
    })


# =========================
# ADD EVENT
# =========================
@login_required
def add_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect("dashboard")

    else:
        form = EventForm()

    return render(request, "add_event.html", {
        "form": form
    })


# =========================
# EVENT DETAIL
# =========================
@login_required
def event_detail(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    # =====================================
    # UPDATE EVENT STATUS
    # =====================================

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status:
            event.status = new_status
            event.save()

            messages.success(
                request,
                "Event status updated successfully."
            )

            return redirect(
                "event_detail",
                event_id=event.id
            )

    # =====================================
    # PARTICIPANTS
    # =====================================

    participants = Registration.objects.filter(
        event=event
    )

    # =====================================
    # FEEDBACKS
    # =====================================

    feedbacks = Feedback.objects.filter(
        registration__event=event
    )

    # =====================================
    # RENDER PAGE
    # =====================================

    return render(
        request,
        "event_detail.html",
        {
            "event": event,
            "registrations": participants,
            "feedbacks": feedbacks,
            "total": participants.count(),
            "attended": participants.filter(
                attendance=True
            ).count(),
            "feedback_count": feedbacks.count()
        }
    )


# =========================
# TOGGLE ATTENDANCE (FIXED)
# =========================
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
import json


@login_required
def toggle_attendance(request, reg_id):
    print("ATTENDANCE TOGGLE CALLED")

    if request.method == "POST":
        try:
            registration = get_object_or_404(Registration, id=reg_id)

            # 🔥 handle empty body safely
            if request.body:
                data = json.loads(request.body)
                attendance_value = data.get("attendance", False)
            else:
                attendance_value = not registration.attendance

            registration.attendance = attendance_value
            registration.save()

            total_attendance = Registration.objects.filter(
                event=registration.event,
                attendance=True
            ).count()

            return JsonResponse({
                "success": True,
                "attendance": registration.attendance,
                "total_attendance": total_attendance
            })

        except Exception as e:
            print("ERROR:", e)
            return JsonResponse({"success": False})

    return JsonResponse({"success": False})
# =========================
# VERIFY TRANSACTION
# =========================
@login_required
def verify_transaction(request, reg_id):
    if request.method == "POST":
        reg = get_object_or_404(
            Registration,
            id=reg_id
        )

        reg.transaction_verified = True
        reg.save()

        return JsonResponse({
            "success": True
        })

    return JsonResponse({
        "success": False
    })

    # =========================
    # GENERATE QR NOW
    # =========================
    qr_data = f"""
Registration ID: {reg.id}
Name: {reg.full_name}
Email: {reg.email}
Event: {reg.event.title}
"""

    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    reg.qr_code.save(
        f"{reg.id}.png",
        File(buffer),
        save=True
    )

    # =========================
    # SEND EMAIL WITH QR
    # =========================
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags
    import base64

    reg.qr_code.open()
    qr_bytes = reg.qr_code.read()
    reg.qr_code.close()

    qr_base64 = base64.b64encode(qr_bytes).decode()

    html_content = f"""
    <html>
    <body>
        <h2>✅ Payment Verified</h2>

        <p>Hello {reg.full_name},</p>

        <p>Your payment has been verified.</p>

        <p><b>Event:</b> {reg.event.title}</p>

        <p>Here is your QR code:</p>

        <img src="data:image/png;base64,{qr_base64}" width="200"/>

        <p>Show this at the event for attendance.</p>
    </body>
    </html>
    """

    plain_text = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject="Payment Verified - QR Code Generated",
        body=plain_text,
        from_email=settings.EMAIL_HOST_USER,
        to=[reg.email],
    )

    email.attach_alternative(html_content, "text/html")

    email.attach(
        f"qr_{reg.id}.png",
        qr_bytes,
        "image/png"
    )

    email.send()

    return JsonResponse({
        "verified": True
    })

# =========================
# OLD REGISTRATION LIST
# =========================
@login_required
def registration_list(request):
    regs = Registration.objects.all()

    return render(request, "registrations.html", {
        "regs": regs
    })

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Registration
@csrf_exempt
def mark_attendance(request):
    if request.method == "POST":
        data = json.loads(request.body)
        qr_data = data.get("qr_data")

        print("QR RECEIVED:", qr_data)

        try:
            import re

            # extract email from QR
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', qr_data)

            if not email_match:
                return JsonResponse({"success": False})

            email = email_match.group()

            id_match = re.search(r'\d+', qr_data)

            if not id_match:
                return JsonResponse({"success": False})

            reg_id = int(id_match.group())

            reg = Registration.objects.get(id=reg_id)

            if not reg:
                return JsonResponse({"success": False})

            # ✅ ALREADY MARKED
            if reg.attendance:
                return JsonResponse({
                    "success": True,
                    "already_marked": True,
                    "reg_id": reg.id,
                    "name": reg.full_name
                })

            # 🔥 THIS IS THE LINE YOU ASKED ABOUT
            reg.attendance = True
            reg.save()

            print("ATTENDANCE SAVED:", reg.id)

            return JsonResponse({
                "success": True,
                "already_marked": False,
                "reg_id": reg.id,
                "name": reg.full_name
            })

        except Exception as e:
            print("ERROR:", e)
            return JsonResponse({"success": False})

    return JsonResponse({"success": False})
import csv
from django.http import HttpResponse

@login_required
def download_attendance_csv(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    registrations = Registration.objects.filter(event=event)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.title}_attendance.csv"'

    writer = csv.writer(response)

    # HEADER
    writer.writerow([
        "Full Name",
        "Email",
        "College ID",
        "Attendance",
        "Payment Verified"
    ])

    # DATA
    for reg in registrations:
        writer.writerow([
            reg.full_name,
            reg.email,
            reg.college_id,
            "Present" if reg.attendance else "Absent",
            "Yes" if reg.transaction_verified else "No"
        ])

    return response
import csv
from io import TextIOWrapper
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Event, Registration


@login_required
def upload_csv(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, "No file selected")
            return redirect('event_detail', event_id=event.id)

        try:
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)

            count = 0

            for row in reader:
                print("ROW:", row)  # debug

                # prevent duplicate using email
                Registration.objects.get_or_create(
                    event=event,
                    email=row.get('Email'),
                    defaults={
                        "full_name": row.get('Full Name'),
                        "college_id": row.get('College ID'),
                        "attendance": False,
                        "transaction_verified": True
                    }
                )

                count += 1

            print("TOTAL ADDED:", count)

            messages.success(request, f"{count} students uploaded successfully!")

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, f"Upload failed: {str(e)}")

        return redirect('event_detail', event_id=event.id)

    return redirect('event_detail', event_id=event.id)