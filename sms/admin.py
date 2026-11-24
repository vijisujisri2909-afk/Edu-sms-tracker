from django.contrib import admin
from .models import Attendance, Batch, Student

admin.site.register(Batch)
admin.site.register(Student)
admin.site.register(Attendance)
