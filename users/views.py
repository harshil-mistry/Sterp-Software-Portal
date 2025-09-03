from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import EmployeeCreationForm, ProjectCreationForm
from .models import Employee, Project, ProjectCollaborator
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    employees = Employee.objects.all()
    return render(request, 'users/admin_dashboard.html', {'employees': employees})

@login_required
@user_passes_test(is_admin)
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Employee {employee.get_full_name()} created successfully! Login credentials have been sent to {employee.email}.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmployeeCreationForm()
    return render(request, 'users/create_employee.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_employee(request, pk):
    if request.method == 'POST':
        employee = Employee.objects.get(pk=pk)
        employee

@login_required
def employee_profile(request):
    return render(request, 'users/employee_profile.html')

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        if self.request.user.is_superuser:
            return '/admin-dashboard/'
        return '/profile/'

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'users/change_password.html'
    success_url = reverse_lazy('employee_profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully!')
        return super().form_valid(form)

def home(request):
    return render(request, 'users/home.html')

@login_required
@user_passes_test(is_admin)
def project_list(request):
    projects = Project.objects.all().prefetch_related('collaborators__employee')
    return render(request, 'users/project_list.html', {'projects': projects})

@login_required
@user_passes_test(is_admin)
def create_project(request):
    if request.method == 'POST':
        form = ProjectCreationForm(request.POST)
        if form.is_valid():
            project = form.save(created_by=request.user)
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('project_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectCreationForm()
    return render(request, 'users/create_project.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    collaborators = ProjectCollaborator.objects.filter(project=project).select_related('employee')
    return render(request, 'users/project_detail.html', {
        'project': project,
        'collaborators': collaborators
    })
