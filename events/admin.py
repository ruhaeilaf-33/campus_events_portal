from django.contrib import admin
from .models import Event, Registration, Feedback


# =========================================
# EVENT ADMIN
# =========================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'date',
        'time',
        'venue',
        'status',
        'created_at'
    )

    list_filter = (
        'status',
        'date'
    )

    search_fields = (
        'title',
        'venue'
    )

    ordering = (
        '-date',
        '-created_at'
    )


# =========================================
# REGISTRATION ADMIN
# =========================================
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'student_id',
        'email',
        'event',
        'attendance',
        'feedback_submitted',
        'transaction_verified',
        'registered_at'
    )

    list_filter = (
        'attendance',
        'feedback_submitted',
        'transaction_verified',
        'event'
    )

    search_fields = (
        'full_name',
        'student_id',
        'email',
        'transaction_id'
    )

    ordering = (
        '-registered_at',
    )

    readonly_fields = (
        'certificate_id',
        'registered_at'
    )


# =========================================
# FEEDBACK ADMIN
# =========================================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'registration',
        'rating',
        'submitted_at'
    )

    list_filter = (
        'rating',
        'submitted_at'
    )

    search_fields = (
        'registration__full_name',
        'registration__event__title'
    )

    ordering = (
        '-submitted_at',
    )