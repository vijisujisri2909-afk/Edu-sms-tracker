from django import forms
from .models import Attendance, Student


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
