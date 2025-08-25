from django.contrib import admin
from .models import Employee
from django.contrib.auth.models import User

# Register your models here.
admin.site.register(Employee)
admin.site.register(User)