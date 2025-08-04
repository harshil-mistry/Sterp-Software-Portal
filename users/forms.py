from django import forms
from django.contrib.auth.forms import UserCreationForm
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
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        default_password = 'default123'  # You might want to move this to settings.py
        employee.set_password(default_password)
        employee.is_active = True
        if commit:
            employee.save()
        return employee
        if commit:
            employee.save()
        return employee
