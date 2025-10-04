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
        """Generate a sequential employee ID in format STERPEMPxxx"""
        # Get the last employee ID
        last_employee = Employee.objects.filter(
            employee_id__startswith='STERPEMP'
        ).order_by('employee_id').last()
        
        if last_employee and last_employee.employee_id:
            # Extract the number part and increment it
            last_number = int(last_employee.employee_id[8:])  # Remove 'STERPEMP' prefix
            new_number = last_number + 1
        else:
            # First employee
            new_number = 1
        
        # Format with leading zeros (001, 002, etc.)
        return f'STERPEMP{new_number:03d}'

    
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
    
    def get_completion_percentage(self):
        """Calculate project completion based on task completion"""
        # Get all tasks related to this project
        project_tasks = self.project_tasks.all()
        total_tasks = project_tasks.count()
        
        if total_tasks == 0:
            return 0
        
        # Calculate based on completed tasks
        completed_tasks = project_tasks.filter(status='COMPLETED').count()
        return round((completed_tasks / total_tasks) * 100, 1)
    
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


class GoogleCalendarCredentials(models.Model):
    """Store Google Calendar OAuth2 credentials for employees"""
    employee = models.OneToOneField(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='google_calendar_credentials'
    )
    token = models.TextField(help_text="OAuth2 access token")
    refresh_token = models.TextField(help_text="OAuth2 refresh token")
    token_uri = models.TextField(help_text="Token URI for OAuth2")
    client_id = models.TextField(help_text="Google OAuth2 client ID")
    client_secret = models.TextField(help_text="Google OAuth2 client secret")
    scopes = models.TextField(help_text="OAuth2 scopes (JSON array)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Calendar Credential"
        verbose_name_plural = "Google Calendar Credentials"
    
    def __str__(self):
        return f"Google Calendar - {self.employee.get_full_name()}"


class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    name = models.CharField(max_length=200, help_text="Task title/name")
    description = models.TextField(help_text="Detailed description of the task")
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='assigned_tasks',
        help_text="Employee assigned to this task"
    )
    project = models.ForeignKey(
        'Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_tasks',
        help_text="Optional: Project this task is associated with"
    )
    date = models.DateField(help_text="Date when the task should be completed")
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='MEDIUM',
        help_text="Task priority level"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="Current status of the task"
    )
    created_by = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        help_text="Admin who created this task"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the task was created")
    completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="When the task was marked as completed"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Last time the task was updated")
    
    # Additional tracking fields
    completion_notes = models.TextField(
        blank=True, 
        help_text="Notes added by employee when completing the task"
    )
    actual_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Actual hours spent on this task"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['status', 'date']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['project']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.employee.get_full_name()} ({self.get_status_display()})"
    
    def is_overdue(self):
        """Check if the task is overdue"""
        from django.utils import timezone
        if self.status == 'PENDING' and self.date < timezone.now().date():
            return True
        return False
    
    def days_until_due(self):
        """Calculate days until the task is due"""
        from django.utils import timezone
        if self.status == 'COMPLETED':
            return None
        delta = self.date - timezone.now().date()
        return delta.days
    
    def time_to_complete(self):
        """Calculate time taken to complete the task"""
        if self.status == 'COMPLETED' and self.completed_at:
            return self.completed_at - self.created_at
        return None
    
    def mark_completed(self, completion_notes='', actual_hours=None):
        """Mark the task as completed"""
        from django.utils import timezone
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        if completion_notes:
            self.completion_notes = completion_notes
        if actual_hours:
            self.actual_hours = actual_hours
        self.save()


# Leave Management Models
class LeaveType(models.Model):
    """Types of leaves available"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    default_days = models.IntegerField(default=0, help_text="Default number of days allocated per year")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.default_days} days)"
    
    class Meta:
        ordering = ['name']


class LeaveBalance(models.Model):
    """Track leave balance for each employee"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year = models.IntegerField(help_text="Year for which this balance applies")
    total_days = models.DecimalField(max_digits=5, decimal_places=1, help_text="Total days allocated")
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0, help_text="Days already used")
    remaining_days = models.DecimalField(max_digits=5, decimal_places=1, help_text="Days remaining")
    
    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['employee', 'leave_type']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.year})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate remaining days
        self.remaining_days = self.total_days - self.used_days
        super().save(*args, **kwargs)


class LeaveApplication(models.Model):
    """Leave application/request"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='applications')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=1, help_text="Total days requested")
    reason = models.TextField(help_text="Reason for leave")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Admin action fields
    reviewed_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_leaves',
        help_text="Admin who reviewed this application"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True, help_text="Admin's remarks on approval/rejection")
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['status', 'applied_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.start_date} to {self.end_date})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        # Validate dates
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date cannot be before start date")
            
            # Calculate total days (including weekends)
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1  # +1 to include both start and end dates
            
            # Check if employee has sufficient balance
            if self.employee and self.leave_type:
                try:
                    balance = LeaveBalance.objects.get(
                        employee=self.employee,
                        leave_type=self.leave_type,
                        year=self.start_date.year
                    )
                    if self.total_days > balance.remaining_days:
                        raise ValidationError(
                            f"Insufficient leave balance. You have {balance.remaining_days} days remaining."
                        )
                except LeaveBalance.DoesNotExist:
                    raise ValidationError("Leave balance not found for this year.")
    
    def save(self, *args, **kwargs):
        # Calculate total days before saving
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1
        super().save(*args, **kwargs)
    
    def approve(self, admin, remarks=''):
        """Approve the leave application"""
        from django.utils import timezone
        
        if self.status != 'PENDING':
            raise ValueError("Only pending applications can be approved")
        
        self.status = 'APPROVED'
        self.reviewed_by = admin
        self.reviewed_at = timezone.now()
        self.admin_remarks = remarks
        self.save()
        
        # Deduct from leave balance
        balance = LeaveBalance.objects.get(
            employee=self.employee,
            leave_type=self.leave_type,
            year=self.start_date.year
        )
        balance.used_days += self.total_days
        balance.save()
    
    def reject(self, admin, remarks=''):
        """Reject the leave application"""
        from django.utils import timezone
        
        if self.status != 'PENDING':
            raise ValueError("Only pending applications can be rejected")
        
        self.status = 'REJECTED'
        self.reviewed_by = admin
        self.reviewed_at = timezone.now()
        self.admin_remarks = remarks
        self.save()
