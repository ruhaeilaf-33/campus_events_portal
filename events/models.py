from django.db import models
from django.contrib.auth.models import User
import uuid


# =========================================
# EVENT MODEL
# =========================================
class Event(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()

    date = models.DateField()
    time = models.TimeField()

    venue = models.CharField(max_length=200)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    document = models.FileField(
        upload_to='event_documents/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# =========================================
# REGISTRATION MODEL
# =========================================
class Registration(models.Model):
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )

    # changed from student_id → college_id
    college_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    full_name = models.CharField(
        max_length=200
    )

    email = models.EmailField()

    qr_code = models.ImageField(
        upload_to='qr_codes/',
        null=True,
        blank=True
    )

    attendance = models.BooleanField(default=False)
    feedback_submitted = models.BooleanField(default=False)

    transaction_id = models.CharField(
        max_length=100,
        unique=True
    )

    receipt = models.FileField(
        upload_to='receipts/'
    )

    transaction_verified = models.BooleanField(default=False)

    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['college_id', 'event']
    def __str__(self):
        return f"{self.full_name} - {self.event.title}"


# =========================================
# FEEDBACK MODEL
# =========================================
class Feedback(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField(default=5)

    comments = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback - {self.registration.full_name}"