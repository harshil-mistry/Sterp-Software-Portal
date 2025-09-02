from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import random
import string
from .models import Employee

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
        fields = ['employee_id', 'username', 'first_name', 'last_name', 'email', 
                 'date_of_birth', 'phone_number', 'address', 'department']
        widgets = {
            'department': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'})
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
Username: {employee.username}
Password: {password}
Employee ID: {employee.employee_id}

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
            print(f"Detailed email error: {str(e)}")
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
