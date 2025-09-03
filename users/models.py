from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string

class Employee(AbstractUser):
    DEPARTMENT_CHOICES = [
        ('IT', 'Information Technology'),
        ('FIN', 'Finance'),
        ('MKT', 'Marketing'),
        ('OPS', 'Operations'),
        ('SALES', 'Sales'),
    ]
    
    employee_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    position = models.CharField(max_length=100, blank=True)  # Changed to text field
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)
    
    def generate_employee_id(self):
        """Generate a unique employee ID"""
        
        while True:
            # Generate format: EMP + 4 digits
            emp_id = 'EMP' + ''.join(random.choices(string.digits, k=4))
            if not Employee.objects.filter(employee_id=emp_id).exists():
                return emp_id

    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

class Project(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class ProjectCollaborator(models.Model):
    ROLE_CHOICES = [
        ('LEAD', 'Project Lead'),
        ('MEMBER', 'Team Member'),
        ('VIEWER', 'Viewer'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collaborators')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='project_collaborations')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['project', 'employee']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.project.name}"
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['project', 'employee']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.project.name}"
