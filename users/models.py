from django.contrib.auth.models import AbstractUser
from django.db import models

class Employee(AbstractUser):
    DEPARTMENT_CHOICES = [
        ('IT', 'Information Technology'),
        ('HR', 'Human Resources'),
        ('FIN', 'Finance'),
        ('MKT', 'Marketing'),
        ('OPS', 'Operations'),
        ('SALES', 'Sales'),
    ]
    
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    joining_date = models.DateField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)
    
    def generate_employee_id(self):
        """Generate the next employee ID in sequence"""
        # Get the last employee ID
        last_employee = Employee.objects.filter(
            employee_id__startswith='STERPEMP'
        ).order_by('employee_id').last()
        
        if last_employee and last_employee.employee_id:
            # Extract the numeric part and increment
            try:
                last_number = int(last_employee.employee_id.replace('STERPEMP', ''))
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1
        
        return f'STERPEMP{next_number:03d}'
    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"
