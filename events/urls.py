from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('login/', views.custom_login, name='login'),
    path('signup/', views.signup, name='signup'),

    # ✅ Logout
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='login'),
        name='logout'
    ),

    # Student
    path('events/', views.event_list, name='events'),
    path(
        'register/<int:event_id>/',
        views.register_event,
        name='register_event'
    ),

    path(
        'student-dashboard/',
        views.student_dashboard,
        name='student_dashboard'
    ),

    path(
        'feedback/<int:reg_id>/',
        views.feedback_view,
        name='feedback'
    ),

    path(
        'certificate/<uuid:certificate_id>/',
        views.download_certificate,
        name='certificate'
    ),

    # Admin
    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'add-event/',
        views.add_event,
        name='add_event'
    ),

    path(
        'event/<int:event_id>/',
        views.event_detail,
        name='event_detail'
    ),

    path(
        'toggle-attendance/<int:reg_id>/',
        views.toggle_attendance,
        name='toggle_attendance'
    ),

    path(
        'verify-transaction/<int:reg_id>/',
        views.verify_transaction,
        name='verify_transaction'
    ),

    # Old registration page (optional)
    path(
        'registrations/',
        views.registration_list,
        name='registrations'
    ),
    path(
    'bulk-upload/<int:event_id>/',
    views.bulk_upload,
    name='bulk_upload'
    ),
    path(
    'delete-registration/<int:reg_id>/',
    views.delete_registration,
    name='delete_registration'
    ),
    path(
    'student-delete-registration/<int:reg_id>/',
    views.student_delete_registration,
    name='student_delete_registration'
    ),
    path(
    'scan-qr/',
    views.scan_qr,
    name='scan_qr'
    ),
    path(
    'verify-transaction/<int:reg_id>/',
    views.verify_transaction,
    name='verify_transaction'
    ),
    path(
    'mark-attendance/',
    views.mark_attendance,
    name='mark_attendance'
),
    path(
    'download-attendance/<int:event_id>/',
    views.download_attendance_csv,
    name='download_attendance_csv'
),
    path(
    'upload-csv/<int:event_id>/',
    views.upload_csv,
    name='upload_csv'
),
path(
    "certificate/<uuid:certificate_id>/",
    views.download_certificate,
    name="download_certificate"
),
]