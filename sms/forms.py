from django import forms
from .models import Attendance, Batch, Student


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'batch',
        ]


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status']
