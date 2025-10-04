from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import random
import string
from .models import Employee, Project, ProjectCollaborator, Task, LeaveType, LeaveBalance, LeaveApplication

class EmployeeCreationForm(UserCreationForm):
    password1 = forms.CharField(widget=forms.HiddenInput(), required=False)
    password2 = forms.CharField(widget=forms.HiddenInput(), required=False)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        })
    )
    
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 
                 'date_of_birth', 'phone_number', 'address', 'department', 'position', 'monthly_salary']
        widgets = {
            'department': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'}),
            'position': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'}),
            'monthly_salary': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2', 'step': '0.01'})
        }
    
    def generate_random_password(self):
        """Generate a random 8-character password"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))
    
    def send_password_email(self, employee, password):
        """Send password email to the new employee"""
        subject = 'Welcome to STERP Softwares - Your Account Details'
        
        # Render email template
        try:
            html_message = render_to_string('users/emails/welcome_email.html', {
                'employee': employee,
                'password': password,
                'company_name': 'STERP Softwares'
            })
        except Exception as template_error:
            print(f"Template error: {template_error}")
            html_message = None
        
        plain_message = f"""
Welcome to STERP Softwares!

Your account has been created successfully.

Login Details:
Employee ID/Username: {employee.username}
Password: {password}

Please log in and change your password after first login.

Portal URL: http://your-domain.com/login/

Best regards,
STERP Softwares Team
        """
        
        try:
            print(f"Attempting to send email to: {employee.email}")
            print(f"From email: {settings.DEFAULT_FROM_EMAIL}")
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                fail_silently=False,
            )
            print("Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"Error type: {type(e)}")
            
            # Try with basic authentication
            try:
                print("Retrying with simpler configuration...")
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[employee.email],
                    fail_silently=False,
                    auth_user=settings.EMAIL_HOST_USER,
                    auth_password=settings.EMAIL_HOST_PASSWORD,
                )
                print("Email sent on retry!")
                return True
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")
                return False
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        # Generate Employee ID and set as username
        if not employee.employee_id:
            employee.employee_id = employee.generate_employee_id()
        employee.username = employee.employee_id
        
        # Generate random password
        random_password = self.generate_random_password()
        employee.set_password(random_password)
        employee.is_active = True
        
        if commit:
            employee.save()
            # Send welcome email with password
            if self.send_password_email(employee, random_password):
                print("Email sent")
            else:
                print("Email not sent")
        
        return employee

class ProjectCreationForm(forms.ModelForm):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_superuser=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select employees to collaborate on this project"
    )
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'priority', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def save(self, commit=True, created_by=None):
        project = super().save(commit=False)
        if created_by:
            project.created_by = created_by
        
        if commit:
            project.save()
            
            # Add collaborators
            collaborators = self.cleaned_data.get('collaborators')
            if collaborators:
                for employee in collaborators:
                    ProjectCollaborator.objects.create(
                        project=project,
                        employee=employee,
                        role='MEMBER'
                    )
        
        return project

class ProjectUpdateForm(forms.ModelForm):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_superuser=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select employees to collaborate on this project"
    )
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'priority', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Pre-select current collaborators
            self.fields['collaborators'].initial = self.instance.collaborators.values_list('employee_id', flat=True)
    
    def save(self, commit=True):
        project = super().save(commit)
        
        if commit:
            # Clear existing collaborators
            ProjectCollaborator.objects.filter(project=project).delete()
            
            # Add new collaborators
            collaborators = self.cleaned_data.get('collaborators')
            if collaborators:
                for employee in collaborators:
                    ProjectCollaborator.objects.create(
                        project=project,
                        employee=employee,
                        role='MEMBER'
                    )
        
        return project


class TaskCreationForm(forms.ModelForm):
    """Form for creating new tasks"""
    
    class Meta:
        model = Task
        fields = ['name', 'description', 'project', 'employee', 'date', 'priority']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'rows': 4,
                'placeholder': 'Describe the task in detail...'
            }),
            'project': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'onchange': 'updateEmployeeOptions()'
            }),
            'employee': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'id': 'id_employee'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            }),
            'priority': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up project field
        self.fields['project'].queryset = Project.objects.all()
        self.fields['project'].required = False
        self.fields['project'].empty_label = "Not linked to any project"
        
        # Only show non-admin employees in the dropdown
        self.fields['employee'].queryset = Employee.objects.filter(is_superuser=False)
        self.fields['employee'].empty_label = "Select an employee"
    
    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        employee = cleaned_data.get('employee')
        
        # If project is selected, validate that employee is part of that project
        if project and employee:
            project_collaborators = ProjectCollaborator.objects.filter(
                project=project,
                employee=employee
            ).exists()
            
            if not project_collaborators:
                raise forms.ValidationError(
                    f"{employee.get_full_name()} is not a collaborator on the selected project. "
                    "Please select an employee who is part of this project or choose 'Not linked to any project'."
                )
        
        return cleaned_data
    
    def save(self, commit=True, created_by=None):
        task = super().save(commit=False)
        if created_by:
            task.created_by = created_by
        
        if commit:
            task.save()
        
        return task


class TaskUpdateForm(forms.ModelForm):
    """Form for updating existing tasks"""
    
    class Meta:
        model = Task
        fields = ['name', 'description', 'project', 'employee', 'date', 'priority', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'rows': 4
            }),
            'project': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'onchange': 'updateEmployeeOptions()'
            }),
            'employee': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'id': 'id_employee'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            }),
            'priority': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            }),
            'status': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.all()
        self.fields['project'].required = False
        self.fields['project'].empty_label = "Not linked to any project"
        self.fields['employee'].queryset = Employee.objects.filter(is_superuser=False)
    
    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        employee = cleaned_data.get('employee')
        
        # If project is selected, validate that employee is part of that project
        if project and employee:
            project_collaborators = ProjectCollaborator.objects.filter(
                project=project,
                employee=employee
            ).exists()
            
            if not project_collaborators:
                raise forms.ValidationError(
                    f"{employee.get_full_name()} is not a collaborator on the selected project. "
                    "Please select an employee who is part of this project or choose 'Not linked to any project'."
                )
        
        return cleaned_data


class TaskCompletionForm(forms.ModelForm):
    """Form for employees to mark tasks as completed"""
    
    class Meta:
        model = Task
        fields = ['completion_notes', 'actual_hours']
        widgets = {
            'completion_notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'rows': 4,
                'placeholder': 'Add any notes about the completed task (optional)...'
            }),
            'actual_hours': forms.NumberInput(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'step': '0.5',
                'min': '0',
                'placeholder': 'e.g., 3.0'
            })
        }
    
    def save(self, commit=True):
        task = super().save(commit=False)
        task.mark_completed(
            completion_notes=self.cleaned_data.get('completion_notes', ''),
            actual_hours=self.cleaned_data.get('actual_hours')
        )
        
        if commit:
            task.save()
        
        return task


class LeaveApplicationForm(forms.ModelForm):
    """Form for employees to apply for leave"""
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
        })
    )
    
    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl bg-slate-700/50 border-slate-600/50 text-white placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-3',
                'rows': 4,
                'placeholder': 'Please provide reason for leave...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        # If we have an employee and no instance, create a partial instance
        # This ensures employee is set before any validation
        if self.employee and not self.instance.pk:
            self.instance.employee = self.employee
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')
        
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be before start date")
            
            # Calculate days
            delta = end_date - start_date
            total_days = delta.days + 1
            
            # Check leave balance
            if self.employee and leave_type:
                from datetime import date
                try:
                    balance = LeaveBalance.objects.get(
                        employee=self.employee,
                        leave_type=leave_type,
                        year=start_date.year
                    )
                    if total_days > balance.remaining_days:
                        raise forms.ValidationError(
                            f"Insufficient leave balance. You have {balance.remaining_days} days remaining for {leave_type.name}."
                        )
                except LeaveBalance.DoesNotExist:
                    raise forms.ValidationError("Leave balance not found for this year.")
        
        return cleaned_data
    
    def save(self, commit=True):
        # Employee is already set in __init__, so we can just save normally
        leave_app = super().save(commit=False)
        
        # Double-check employee is set (defensive programming)
        if not leave_app.employee:
            if self.employee:
                leave_app.employee = self.employee
            else:
                raise ValueError("Employee must be provided to save leave application")
        
        if commit:
            leave_app.save()
        
        return leave_app
