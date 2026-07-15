from django import forms
from .models import Event, Registration, Feedback


# =========================================
# FILE VALIDATION FUNCTION
# =========================================
def validate_receipt(file):
    allowed_types = ['pdf', 'png', 'jpg', 'jpeg']

    extension = file.name.split('.')[-1].lower()

    if extension not in allowed_types:
        raise forms.ValidationError(
            "Only PDF, PNG, JPG, JPEG files are allowed."
        )

    # Max size = 2MB
    if file.size > 2 * 1024 * 1024:
        raise forms.ValidationError(
            "File size must be less than 2MB."
        )


# =========================================
# EVENT FORM (ADMIN)
# =========================================
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'date',
            'time',
            'venue',
            'status',
            'document'
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter event title'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter event description'
            }),

            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),

            'venue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter venue'
            }),

            'status': forms.Select(attrs={
                'class': 'form-control'
            }),

            'document': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File"
    )
# =========================================
# REGISTRATION FORM (STUDENT)
# =========================================
class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = [
            'college_id',
            'full_name',
            'email',
            'transaction_id',
            'receipt'
        ]

        widgets = {
            'college_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter College ID'
            }),

            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Full Name'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email'
            }),

            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Transaction ID'
            }),

            'receipt': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    # =====================================
    # DUPLICATE TRANSACTION CHECK
    # =====================================
    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get('transaction_id')

        if Registration.objects.filter(
            transaction_id=transaction_id
        ).exists():
            raise forms.ValidationError(
                "Transaction ID already exists."
            )

        return transaction_id

    # =====================================
    # RECEIPT VALIDATION
    # =====================================
    def clean_receipt(self):
        receipt = self.cleaned_data.get('receipt')

        if receipt:
            validate_receipt(receipt)

        return receipt


# =========================================
# FEEDBACK FORM
# =========================================
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'rating',
            'comments'
        ]

        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'form-control',
                'placeholder': 'Rate from 1 to 5'
            }),

            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your feedback here...'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')

        if rating < 1 or rating > 5:
            raise forms.ValidationError(
                "Rating must be between 1 and 5."
            )

        return rating