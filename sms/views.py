from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import AttendanceForm, StudentForm
from .models import Attendance, Batch, Student


def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()

    return render(request, 'sms/register_student.html', {'form': form})


def student_list(request):
    students = (
        Student.objects.select_related('batch')
        .order_by('last_name', 'first_name')
    )
    return render(request, 'sms/student_list.html', {'students': students})


def batch_list(request):
    batches = Batch.objects.order_by('name')
    return render(request, 'sms/batch_list.html', {'batches': batches})


def take_attendance(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    students = list(
        Student.objects.filter(batch=batch).order_by('last_name', 'first_name')
    )
    today = timezone.localdate()
    attendance_exists = Attendance.objects.filter(
        student__batch=batch,
        date=today,
    ).exists()

    if request.method == 'POST':
        if attendance_exists:
            messages.error(
                request,
                'Attendance for this batch has already been recorded today.',
            )
            return redirect('take_attendance', batch_id=batch.pk)
        if not students:
            messages.error(request, 'This batch has no students to mark.')
            return redirect('batch_list')

        student_forms = [
            (student, AttendanceForm(request.POST, prefix=f'student-{student.pk}'))
            for student in students
        ]
        forms_valid = [form.is_valid() for _, form in student_forms]
        if all(forms_valid):
            try:
                with transaction.atomic():
                    for student, form in student_forms:
                        attendance = form.save(commit=False)
                        attendance.student = student
                        attendance.date = today
                        attendance.save()
            except IntegrityError:
                messages.error(
                    request,
                    'Attendance for this batch has already been recorded today.',
                )
                return redirect('take_attendance', batch_id=batch.pk)

            messages.success(request, 'Attendance recorded successfully.')
            return redirect('batch_list')
    else:
        student_forms = [
            (student, AttendanceForm(prefix=f'student-{student.pk}'))
            for student in students
        ]

    return render(
        request,
        'sms/take_attendance.html',
        {
            'batch': batch,
            'student_forms': student_forms,
            'attendance_exists': attendance_exists,
        },
    )


def attendance_report(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    attendance_summary = {
        student.pk: {
            'student': student,
            'present_days': 0,
            'absent_days': 0,
            'late_days': 0,
        }
        for student in Student.objects.filter(batch=batch).order_by(
            'last_name', 'first_name'
        )
    }
    status_counts = {
        Attendance.Status.PRESENT: 'present_days',
        Attendance.Status.ABSENT: 'absent_days',
        Attendance.Status.LATE: 'late_days',
    }
    records = Attendance.objects.filter(
        student__batch=batch,
    ).select_related('student')
    for record in records:
        count_field = status_counts.get(record.status)
        if count_field:
            attendance_summary[record.student_id][count_field] += 1

    return render(
        request,
        'sms/attendance_report.html',
        {
            'batch': batch,
            'attendance_summary': attendance_summary,
        },
    )


def student_attendance_report(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related('batch'),
        pk=student_id,
    )
    attendance_records = student.attendance_records.order_by('date', 'pk')
    return render(
        request,
        'sms/student_attendance_report.html',
        {
            'student': student,
            'attendance_records': attendance_records,
        },
    )


