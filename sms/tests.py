from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Attendance, Batch, Student


class StudentViewsTests(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(
            name='Morning class',
            start_date='2026-01-05',
        )

    def test_registration_form_saves_student_and_redirects(self):
        response = self.client.post(
            reverse('register_student'),
            {
                'first_name': 'Avery',
                'last_name': 'Nguyen',
                'email': 'avery@example.com',
                'phone_number': '5551234567',
                'batch': self.batch.pk,
            },
        )

        self.assertRedirects(response, reverse('student_list'))
        self.assertTrue(
            Student.objects.filter(
                first_name='Avery',
                last_name='Nguyen',
                batch=self.batch,
            ).exists()
        )

    def test_student_list_shows_student_and_batch(self):
        student = Student.objects.create(
            first_name='Avery',
            last_name='Nguyen',
            email='avery@example.com',
            phone_number='5551234567',
            batch=self.batch,
        )

        response = self.client.get(reverse('student_list'))

        self.assertContains(response, 'Avery Nguyen')
        self.assertContains(response, 'avery@example.com')
        self.assertContains(response, 'Morning class')
        self.assertContains(
            response,
            reverse('student_attendance_report', args=[student.pk]),
        )

    def test_invalid_registration_renders_form_errors(self):
        response = self.client.post(
            reverse('register_student'),
            {
                'first_name': '',
                'last_name': 'Nguyen',
                'email': 'not-an-email',
                'phone_number': '5551234567',
                'batch': self.batch.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.exists())
        self.assertContains(response, 'Enter a valid email address.')


class AttendanceViewsTests(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(
            name='Morning class',
            start_date='2026-01-05',
        )
        self.student = Student.objects.create(
            first_name='Avery',
            last_name='Nguyen',
            email='avery@example.com',
            phone_number='5551234567',
            batch=self.batch,
        )
        self.url = reverse('take_attendance', args=[self.batch.pk])

    def test_get_displays_attendance_choice_for_each_student(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avery Nguyen')
        self.assertContains(response, 'Present')
        self.assertContains(response, 'Absent')
        self.assertContains(response, 'Late')

    def test_post_creates_attendance_for_each_student_today(self):
        another_student = Student.objects.create(
            first_name='Jordan',
            last_name='Lee',
            email='jordan@example.com',
            phone_number='5559876543',
            batch=self.batch,
        )
        response = self.client.post(
            self.url,
            {
                f'student-{self.student.pk}-status': Attendance.Status.PRESENT,
                f'student-{another_student.pk}-status': Attendance.Status.LATE,
            },
        )

        self.assertRedirects(response, reverse('batch_list'))
        attendance = Attendance.objects.get(student=self.student)
        self.assertEqual(attendance.date, timezone.localdate())
        self.assertEqual(attendance.status, Attendance.Status.PRESENT)
        another_attendance = Attendance.objects.get(student=another_student)
        self.assertEqual(another_attendance.date, timezone.localdate())
        self.assertEqual(another_attendance.status, Attendance.Status.LATE)

    def test_second_submission_for_same_batch_and_date_is_rejected(self):
        self.client.post(
            self.url,
            {f'student-{self.student.pk}-status': Attendance.Status.PRESENT},
        )

        response = self.client.post(
            self.url,
            {f'student-{self.student.pk}-status': Attendance.Status.ABSENT},
            follow=True,
        )

        self.assertContains(response, 'already been recorded today')
        self.assertEqual(Attendance.objects.count(), 1)
        self.assertEqual(
            Attendance.objects.get(student=self.student).status,
            Attendance.Status.PRESENT,
        )

    def test_batch_list_links_to_attendance_page(self):
        response = self.client.get(reverse('batch_list'))

        self.assertContains(
            response,
            reverse('take_attendance', args=[self.batch.pk]),
        )


class AttendanceReportTests(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(
            name='Morning class',
            start_date='2026-01-05',
        )
        self.student = Student.objects.create(
            first_name='Avery',
            last_name='Nguyen',
            email='avery@example.com',
            phone_number='5551234567',
            batch=self.batch,
        )
        self.report_url = reverse('attendance_report', args=[self.batch.pk])
        self.student_report_url = reverse(
            'student_attendance_report',
            args=[self.student.pk],
        )

    def test_batch_report_counts_each_status_and_includes_zero_counts(self):
        Attendance.objects.create(
            student=self.student,
            date='2026-01-06',
            status=Attendance.Status.PRESENT,
        )
        Attendance.objects.create(
            student=self.student,
            date='2026-01-07',
            status=Attendance.Status.PRESENT,
        )
        Attendance.objects.create(
            student=self.student,
            date='2026-01-08',
            status=Attendance.Status.ABSENT,
        )
        Attendance.objects.create(
            student=self.student,
            date='2026-01-09',
            status=Attendance.Status.LATE,
        )
        no_records_student = Student.objects.create(
            first_name='Jordan',
            last_name='Lee',
            email='jordan@example.com',
            phone_number='5559876543',
            batch=self.batch,
        )

        response = self.client.get(self.report_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['attendance_summary'][self.student.pk],
            {
                'student': self.student,
                'present_days': 2,
                'absent_days': 1,
                'late_days': 1,
            },
        )
        self.assertEqual(
            response.context['attendance_summary'][no_records_student.pk][
                'present_days'
            ],
            0,
        )
        self.assertContains(response, 'Avery Nguyen')

    def test_student_report_shows_attendance_in_date_order(self):
        Attendance.objects.create(
            student=self.student,
            date='2026-01-08',
            status=Attendance.Status.LATE,
        )
        Attendance.objects.create(
            student=self.student,
            date='2026-01-06',
            status=Attendance.Status.PRESENT,
        )
        Attendance.objects.create(
            student=self.student,
            date='2026-01-07',
            status=Attendance.Status.ABSENT,
        )

        response = self.client.get(self.student_report_url)

        self.assertEqual(response.status_code, 200)
        records = list(response.context['attendance_records'])
        self.assertEqual(
            [record.date.isoformat() for record in records],
            ['2026-01-06', '2026-01-07', '2026-01-08'],
        )
        self.assertContains(response, 'Present')
        self.assertContains(response, 'Absent')
        self.assertContains(response, 'Late')
