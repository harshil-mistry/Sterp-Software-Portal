from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import EmployeeCreationForm, ProjectCreationForm, ProjectUpdateForm
from .models import Employee, Project, ProjectCollaborator, GoogleCalendarCredentials
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from datetime import date

from .google_calendar_utils import GoogleCalendarService
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
        employee_name = employee.get_full_name()
        employee.delete()
        messages.success(request, f'Employee "{employee_name}" deleted successfully!')
        return redirect('admin_dashboard')

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
    
    return render(request, 'users/create_project.html', {
        'form': form,
        'today': date.today().strftime('%Y-%m-%d')
    })

@login_required
@user_passes_test(is_admin)
def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    collaborators = ProjectCollaborator.objects.filter(project=project).select_related('employee')
    return render(request, 'users/project_detail.html', {
        'project': project,
        'collaborators': collaborators
    })

@login_required
@user_passes_test(is_admin)
def update_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectUpdateForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('project_detail', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectUpdateForm(instance=project)
    return render(request, 'users/update_project.html', {'form': form, 'project': project})

@login_required
@user_passes_test(is_admin)
def delete_project(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully!')
        return redirect('project_list')

@login_required
def employee_projects(request):
    """View for employees to see projects they're assigned to"""
    if request.user.is_superuser:
        return redirect('project_list')  # Admins should use the main project list
    
    collaborations = ProjectCollaborator.objects.filter(
        employee=request.user
    ).select_related('project').order_by('-project__created_at')
    
    projects = [collaboration.project for collaboration in collaborations]
    
    return render(request, 'users/employee_projects.html', {
        'projects': projects,
        'collaborations': collaborations
    })

@login_required
def employee_project_detail(request, pk):
    """View for employees to see project details they're assigned to"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check if employee is part of this project (or is admin)
    if not request.user.is_superuser:
        collaboration = ProjectCollaborator.objects.filter(
            project=project, 
            employee=request.user
        ).first()
        if not collaboration:
            messages.error(request, "You don't have access to this project.")
            return redirect('employee_projects')
    
    collaborators = ProjectCollaborator.objects.filter(project=project).select_related('employee')
    user_role = None
    
    if not request.user.is_superuser:
        user_collaboration = ProjectCollaborator.objects.filter(
            project=project, 
            employee=request.user
        ).first()
        user_role = user_collaboration.role if user_collaboration else None
    
    return render(request, 'users/employee_project_detail.html', {
        'project': project,
        'collaborators': collaborators,
        'user_role': user_role
    })


# Google Calendar Integration Views
@login_required
def google_calendar_connect(request):
    """Initiate Google Calendar OAuth2 flow"""
    
    try:
        authorization_url = GoogleCalendarService.get_authorization_url(request, request.user)
        return redirect(authorization_url)
    except Exception as e:
        messages.error(request, f"Error connecting to Google Calendar: {str(e)}")
        return redirect('employee_profile')


@login_required
def google_calendar_callback(request):
    """Handle Google Calendar OAuth2 callback"""
    
    success, message = GoogleCalendarService.handle_callback(request)
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect('employee_profile')


@login_required
def google_calendar_disconnect(request):
    """Disconnect Google Calendar integration"""
    if request.method == 'POST':
        success, message = GoogleCalendarService.revoke_credentials(request.user)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    return redirect('employee_profile')


@login_required
@user_passes_test(is_admin)
def admin_add_calendar_event(request, employee_id):
    """Admin view to add events to employee's Google Calendar for testing"""
    from datetime import datetime, timedelta
    
    employee = get_object_or_404(Employee, pk=employee_id)
    
    # Check if employee has Google Calendar connected
    try:
        credentials = GoogleCalendarCredentials.objects.get(employee=employee)
    except GoogleCalendarCredentials.DoesNotExist:
        messages.error(request, f'{employee.get_full_name()} has not connected their Google Calendar.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        duration = int(request.POST.get('duration', 60))  # duration in minutes
        
        try:
            # Create datetime objects
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)
            
            # Create event using Google Calendar Service
            event_data = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 60},   # 1 hour before
                        {'method': 'popup', 'minutes': 15},   # 15 minutes before
                    ],
                },
            }
            
            success, result = GoogleCalendarService.create_event(employee, event_data)
            
            if success:
                messages.success(request, f'Event "{title}" added to {employee.get_full_name()}\'s calendar successfully!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, f'Failed to add event: {result}')
                
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
    
    return render(request, 'users/admin_add_calendar_event.html', {
        'employee': employee
    })
