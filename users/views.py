from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import EmployeeCreationForm, ProjectCreationForm, ProjectUpdateForm, TaskCreationForm, TaskUpdateForm, TaskCompletionForm, LeaveApplicationForm
from .models import Employee, Project, ProjectCollaborator, GoogleCalendarCredentials, Task, LeaveType, LeaveBalance, LeaveApplication
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Sum
from datetime import date
import time
import logging

from .google_calendar_utils import GoogleCalendarService

logger = logging.getLogger(__name__)

def add_project_calendar_events(project, collaborators_list=None):
    """
    Add calendar events for project start and deadline for all collaborators
    who have Google Calendar connected
    """
    if collaborators_list is None:
        # Get all collaborators for the project
        collaborators = ProjectCollaborator.objects.filter(project=project).select_related('employee')
        collaborators_list = [collab.employee for collab in collaborators]
    
    events_added = []
    events_failed = []
    
    for employee in collaborators_list:
        # Check if employee has Google Calendar connected
        try:
            calendar_creds = GoogleCalendarCredentials.objects.get(employee=employee)
            
            # Add project start event
            start_success, start_message = GoogleCalendarService.create_project_start_event(employee, project)
            if start_success:
                events_added.append(f"{employee.get_full_name()} - Project Start")
                logger.info(f"Added start event for {employee.get_full_name()} in project {project.name}")
            else:
                events_failed.append(f"{employee.get_full_name()} - Project Start: {start_message}")
                logger.error(f"Failed to add start event for {employee.get_full_name()}: {start_message}")
            
            # Add project deadline event
            deadline_success, deadline_message = GoogleCalendarService.create_project_deadline_event(employee, project)
            if deadline_success:
                events_added.append(f"{employee.get_full_name()} - Project Deadline")
                logger.info(f"Added deadline event for {employee.get_full_name()} in project {project.name}")
            else:
                events_failed.append(f"{employee.get_full_name()} - Project Deadline: {deadline_message}")
                logger.error(f"Failed to add deadline event for {employee.get_full_name()}: {deadline_message}")
                
        except GoogleCalendarCredentials.DoesNotExist:
            logger.info(f"No Google Calendar connected for {employee.get_full_name()}")
            continue
        except Exception as e:
            logger.error(f"Error adding calendar events for {employee.get_full_name()}: {str(e)}")
            events_failed.append(f"{employee.get_full_name()} - Error: {str(e)}")
    
    return events_added, events_failed
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
@user_passes_test(is_admin)
def employee_detail(request, pk):
    """Admin view to see detailed employee information and task contributions"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Get all projects where employee is a collaborator
    project_collaborations = ProjectCollaborator.objects.filter(employee=employee).select_related('project')
    projects = [collab.project for collab in project_collaborations]
    
    # Get all tasks assigned to this employee
    tasks = Task.objects.filter(employee=employee).select_related('project').order_by('-date')
    
    # Calculate task statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='COMPLETED').count()
    pending_tasks = tasks.filter(status='PENDING').count()
    in_progress_tasks = tasks.filter(status='IN_PROGRESS').count()
    overdue_tasks = tasks.filter(status__in=['PENDING', 'IN_PROGRESS'], date__lt=date.today()).count()
    
    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Group tasks by project
    tasks_by_project = {}
    for project in projects:
        project_tasks = tasks.filter(project=project)
        if project_tasks.exists():
            tasks_by_project[project] = {
                'total': project_tasks.count(),
                'completed': project_tasks.filter(status='COMPLETED').count(),
                'pending': project_tasks.filter(status='PENDING').count(),
                'in_progress': project_tasks.filter(status='IN_PROGRESS').count(),
            }
    
    # Tasks without project
    tasks_no_project = tasks.filter(project__isnull=True)
    if tasks_no_project.exists():
        tasks_by_project[None] = {
            'total': tasks_no_project.count(),
            'completed': tasks_no_project.filter(status='COMPLETED').count(),
            'pending': tasks_no_project.filter(status='PENDING').count(),
            'in_progress': tasks_no_project.filter(status='IN_PROGRESS').count(),
        }
    
    # Calculate monthly tasks completed (last 30 days)
    from datetime import timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    monthly_completed = tasks.filter(status='COMPLETED', completed_at__gte=thirty_days_ago).count()
    
    context = {
        'employee': employee,
        'projects': projects,
        'project_collaborations': project_collaborations,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_percentage': round(completion_percentage, 1),
        'tasks_by_project': tasks_by_project,
        'monthly_completed': monthly_completed,
        'total_projects': len(projects),
    }
    
    return render(request, 'users/employee_detail.html', context)

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
    projects = Project.objects.all().prefetch_related('collaborators__employee', 'project_tasks')
    
    # Calculate completion percentage for each project
    projects_with_completion = []
    for project in projects:
        projects_with_completion.append({
            'project': project,
            'completion_percentage': project.get_completion_percentage()
        })
    
    return render(request, 'users/project_list.html', {
        'projects': projects,
        'projects_with_completion': projects_with_completion
    })

@login_required
@user_passes_test(is_admin)
def create_project(request):
    if request.method == 'POST':
        form = ProjectCreationForm(request.POST)
        if form.is_valid():
            project = form.save(created_by=request.user)
            
            # Get the collaborators that were added
            collaborators = form.cleaned_data.get('collaborators', [])
            
            # Add calendar events for collaborators
            if collaborators:
                events_added, events_failed = add_project_calendar_events(project, collaborators)
                
                # Show success message with calendar event info
                success_msg = f'Project "{project.name}" created successfully!'
                if events_added:
                    success_msg += f' Calendar events added for: {", ".join([name.split(" - ")[0] for name in events_added])}'
                if events_failed:
                    success_msg += f' Some calendar events failed to add.'
                
                messages.success(request, success_msg)
                
                # Show warning for failed events if any
                if events_failed:
                    failed_msg = "Calendar event failures: " + "; ".join(events_failed[:3])  # Limit to first 3
                    if len(events_failed) > 3:
                        failed_msg += f" and {len(events_failed) - 3} more..."
                    messages.warning(request, failed_msg)
            else:
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
    
    # Get all tasks associated with this project
    tasks = Task.objects.filter(project=project).select_related('employee').order_by('-date')
    
    # Calculate task statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='COMPLETED').count()
    pending_tasks = tasks.filter(status='PENDING').count()
    in_progress_tasks = tasks.filter(status='IN_PROGRESS').count()
    overdue_tasks = tasks.filter(status__in=['PENDING', 'IN_PROGRESS'], date__lt=date.today()).count()
    
    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Group tasks by employee for tracking
    tasks_by_employee = {}
    for collaborator in collaborators:
        employee_tasks = tasks.filter(employee=collaborator.employee)
        tasks_by_employee[collaborator.employee] = {
            'total': employee_tasks.count(),
            'completed': employee_tasks.filter(status='COMPLETED').count(),
            'pending': employee_tasks.filter(status='PENDING').count(),
            'in_progress': employee_tasks.filter(status='IN_PROGRESS').count(),
        }
    
    return render(request, 'users/project_detail.html', {
        'project': project,
        'collaborators': collaborators,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_percentage': round(completion_percentage, 1),
        'tasks_by_employee': tasks_by_employee,
    })

@login_required
@user_passes_test(is_admin)
def update_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        # Store original project data before form save
        original_start_date = project.start_date
        original_end_date = project.end_date
        current_collaborators = set(ProjectCollaborator.objects.filter(project=project).values_list('employee_id', flat=True))
        
        form = ProjectUpdateForm(request.POST, instance=project)
        if form.is_valid():
            # Get new collaborators from form
            new_collaborators_set = set(form.cleaned_data.get('collaborators', []).values_list('id', flat=True))
            
            # Check if dates have changed
            dates_changed = (
                form.cleaned_data['start_date'] != original_start_date or 
                form.cleaned_data['end_date'] != original_end_date
            )
            
            # Save the form (this will update collaborators and project data)
            form.save()
            
            # Calculate changes in collaborators
            added_collaborators_ids = new_collaborators_set - current_collaborators
            removed_collaborators_ids = current_collaborators - new_collaborators_set
            unchanged_collaborators_ids = current_collaborators & new_collaborators_set
            
            events_added = []
            events_failed = []
            events_removed = []
            events_updated = []
            
            # Handle date changes for existing collaborators
            if dates_changed and unchanged_collaborators_ids:
                unchanged_employees = Employee.objects.filter(id__in=unchanged_collaborators_ids)
                for employee in unchanged_employees:
                    try:
                        calendar_creds = GoogleCalendarCredentials.objects.get(employee=employee)
                        
                        # Delete old events with old dates
                        delete_success, delete_message = GoogleCalendarService.delete_project_events(employee, project)
                        
                        # Create new events with updated dates
                        new_events_added, new_events_failed = add_project_calendar_events(project, [employee])
                        if new_events_added:
                            events_updated.append(f"{employee.get_full_name()}")
                            logger.info(f"Updated calendar events for {employee.get_full_name()} due to date changes")
                        
                        if new_events_failed:
                            events_failed.extend(new_events_failed)
                            
                    except GoogleCalendarCredentials.DoesNotExist:
                        logger.info(f"No Google Calendar connected for {employee.get_full_name()}")
                        continue
                    except Exception as e:
                        logger.error(f"Error updating calendar events for {employee.get_full_name()}: {str(e)}")
                        events_failed.append(f"{employee.get_full_name()} - Update error: {str(e)}")
            
            # Add calendar events for new collaborators
            if added_collaborators_ids:
                added_employees = Employee.objects.filter(id__in=added_collaborators_ids)
                new_events_added, new_events_failed = add_project_calendar_events(project, added_employees)
                events_added.extend(new_events_added)
                events_failed.extend(new_events_failed)
            
            # Remove calendar events for removed collaborators
            if removed_collaborators_ids:
                removed_employees = Employee.objects.filter(id__in=removed_collaborators_ids)
                for employee in removed_employees:
                    try:
                        calendar_creds = GoogleCalendarCredentials.objects.get(employee=employee)
                        success, message = GoogleCalendarService.delete_project_events(employee, project)
                        if success:
                            events_removed.append(f"{employee.get_full_name()}")
                            logger.info(f"Removed project events for {employee.get_full_name()} from project {project.name}")
                        else:
                            events_failed.append(f"{employee.get_full_name()} - Removal failed: {message}")
                            logger.error(f"Failed to remove events for {employee.get_full_name()}: {message}")
                    except GoogleCalendarCredentials.DoesNotExist:
                        logger.info(f"No Google Calendar connected for {employee.get_full_name()}")
                        continue
                    except Exception as e:
                        logger.error(f"Error removing calendar events for {employee.get_full_name()}: {str(e)}")
                        events_failed.append(f"{employee.get_full_name()} - Error: {str(e)}")
            
            # Build success message
            success_msg = f'Project "{project.name}" updated successfully!'
            if events_added:
                success_msg += f' Calendar events added for: {", ".join([name.split(" - ")[0] for name in events_added])}'
            if events_removed:
                success_msg += f' Calendar events removed for: {", ".join(events_removed)}'
            if events_updated:
                success_msg += f' Calendar events updated for: {", ".join(events_updated)}'
            
            messages.success(request, success_msg)
            
            # Show warning for failed events if any
            if events_failed:
                failed_msg = "Calendar event issues: " + "; ".join(events_failed[:3])  # Limit to first 3
                if len(events_failed) > 3:
                    failed_msg += f" and {len(events_failed) - 3} more..."
                messages.warning(request, failed_msg)
            
            return redirect('project_detail', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectUpdateForm(instance=project)
    
    return render(request, 'users/update_project.html', {'form': form, 'project': project})

def sync_all_existing_projects_for_employee(employee):
    """
    Utility function to sync all existing projects for a newly connected employee
    This is used when someone connects their Google Calendar for the first time
    """
    try:
        # Get all projects where this employee is a collaborator
        collaborations = ProjectCollaborator.objects.filter(employee=employee).select_related('project')
        projects = [collab.project for collab in collaborations]
        
        total_events_added = 0
        synced_projects = []
        
        for project in projects:
            events_added, events_failed = add_project_calendar_events(project, [employee])
            if events_added:
                total_events_added += len(events_added)
                synced_projects.append(project.name)
        
        return total_events_added, synced_projects
        
    except Exception as e:
        logger.error(f"Error syncing all projects for {employee.get_full_name()}: {str(e)}")
        return 0, []

@login_required
@user_passes_test(is_admin)
def delete_project(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project_name = project.name
        
        # Automatically remove calendar events for all collaborators before deleting
        try:
            collaborators = ProjectCollaborator.objects.filter(project=project).select_related('employee')
            events_removed_count = 0
            
            for collab in collaborators:
                try:
                    calendar_creds = GoogleCalendarCredentials.objects.get(employee=collab.employee)
                    success, message = GoogleCalendarService.delete_project_events(collab.employee, project)
                    if success:
                        events_removed_count += 1
                        logger.info(f"Removed calendar events for {collab.employee.get_full_name()} from deleted project {project_name}")
                except GoogleCalendarCredentials.DoesNotExist:
                    logger.info(f"No calendar credentials for {collab.employee.get_full_name()}")
                    continue
                except Exception as e:
                    logger.error(f"Error removing calendar events for {collab.employee.get_full_name()}: {str(e)}")
            
            project.delete()
            
            if events_removed_count > 0:
                messages.success(request, f'Project "{project_name}" deleted successfully! Calendar events removed for {events_removed_count} team member{"s" if events_removed_count != 1 else ""}.')
            else:
                messages.success(request, f'Project "{project_name}" deleted successfully!')
                
        except Exception as e:
            logger.error(f"Error during project deletion: {str(e)}")
            project.delete()  # Still delete the project even if calendar cleanup fails
            messages.success(request, f'Project "{project_name}" deleted successfully!')
            messages.warning(request, "Some calendar events might not have been removed.")
        
        return redirect('project_list')

@login_required
def employee_projects(request):
    """View for employees to see projects they're assigned to"""
    if request.user.is_superuser:
        return redirect('project_list')  # Admins should use the main project list
    
    collaborations = ProjectCollaborator.objects.filter(
        employee=request.user
    ).select_related('project').prefetch_related('project__project_tasks').order_by('-project__created_at')
    
    projects = [collaboration.project for collaboration in collaborations]
    
    # Calculate completion percentage for each project
    projects_with_completion = []
    for project in projects:
        projects_with_completion.append({
            'project': project,
            'completion_percentage': project.get_completion_percentage()
        })
    
    return render(request, 'users/employee_projects.html', {
        'projects': projects,
        'collaborations': collaborations,
        'projects_with_completion': projects_with_completion
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
    
    # Calculate project completion percentage
    completion_percentage = project.get_completion_percentage()
    
    return render(request, 'users/employee_project_detail.html', {
        'project': project,
        'collaborators': collaborators,
        'user_role': user_role,
        'completion_percentage': completion_percentage
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


@csrf_exempt
def google_calendar_callback(request):
    """Handle Google Calendar OAuth2 callback with session validation"""
    
    logger.info(f"OAuth callback received. Session key: {request.session.session_key}")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.build_absolute_uri()}")
    
    # Ensure session is fully loaded - wait and retry if needed
    max_retries = 3
    retry_count = 0
    session_loaded = False
    
    while retry_count < max_retries and not session_loaded:
        try:
            # Force session load by accessing session data
            session_key = request.session.session_key
            logger.info(f"Attempt {retry_count + 1}: Session key: {session_key}")
            
            if session_key:
                # Try to access session data that should exist
                auth_state = request.session.get('google_auth_state')
                employee_id = request.session.get('google_auth_employee_id')
                
                logger.info(f"Session data - Auth state exists: {bool(auth_state)}, Employee ID: {employee_id}")
                
                if auth_state and employee_id:
                    session_loaded = True
                    logger.info("Session successfully loaded with OAuth data")
                else:
                    # Session exists but OAuth data missing - might be invalid
                    if retry_count == max_retries - 1:
                        logger.error("OAuth session data missing after all retries")
                        messages.error(request, "OAuth session expired. Please try connecting again.")
                        return redirect('employee_profile')
            
            if not session_loaded:
                logger.info(f"Session not ready, waiting... (attempt {retry_count + 1})")
                time.sleep(0.5)  # Wait 500ms before retry
                retry_count += 1
                
        except Exception as e:
            logger.error(f"Session loading error: {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                messages.error(request, "Session loading failed. Please try connecting again.")
                return redirect('employee_profile')
            time.sleep(0.5)
    
    # # Check if user is logged in after session is loaded
    if not request.user.is_authenticated:
        logger.warning("User not authenticated after session loading")
        messages.error(request, "You must be logged in to connect Google Calendar.")
        return redirect('login')
    
    # Process the OAuth callback
    logger.info("Processing OAuth callback with GoogleCalendarService")
    success, message = GoogleCalendarService.handle_callback(request)
    if success:
        logger.info(f"OAuth callback successful: {message}")
        
        # Automatically sync calendar events for existing projects
        try:
            total_events_added, synced_projects = sync_all_existing_projects_for_employee(request.user)
            
            if total_events_added > 0:
                if len(synced_projects) == 1:
                    sync_msg = f"Calendar events automatically created for existing project: \"{synced_projects[0]}\""
                elif len(synced_projects) <= 3:
                    project_list = ', '.join([f'"{name}"' for name in synced_projects])
                    sync_msg = f"Calendar events automatically created for existing projects: {project_list}"
                else:
                    sync_msg = f"Calendar events automatically created for {len(synced_projects)} existing projects"
                
                success_message = f"{message} {sync_msg} ({total_events_added} events added)"
            else:
                success_message = f"{message} No existing project assignments found."
                
            messages.success(request, success_message)
            
        except Exception as e:
            logger.error(f"Error auto-syncing existing projects: {str(e)}")
            messages.success(request, message)  # Show original success message
            messages.info(request, "Connected successfully, but couldn't auto-sync existing projects.")
    else:
        logger.error(f"OAuth callback failed: {message}")
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


# ============================================
# TASK MANAGEMENT VIEWS
# ============================================

@login_required
@user_passes_test(is_admin)
def task_list(request):
    """Admin view to list all tasks with filtering options"""
    tasks = Task.objects.all().select_related('employee', 'created_by')
    
    # Filter by employee
    employee_id = request.GET.get('employee')
    if employee_id:
        tasks = tasks.filter(employee_id=employee_id)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        tasks = tasks.filter(date__gte=date_from)
    if date_to:
        tasks = tasks.filter(date__lte=date_to)
    
    # Get employees for filter dropdown
    employees = Employee.objects.filter(is_superuser=False).order_by('first_name', 'last_name')
    
    # Get task statistics
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='PENDING').count()
    completed_tasks = tasks.filter(status='COMPLETED').count()
    overdue_tasks = tasks.filter(status='PENDING', date__lt=date.today()).count()
    
    context = {
        'tasks': tasks,
        'employees': employees,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'selected_employee': employee_id,
        'selected_status': status,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
    }
    
    return render(request, 'users/task_list.html', context)


@login_required
@user_passes_test(is_admin)
def create_task(request):
    """Admin view to create a new task"""
    if request.method == 'POST':
        form = TaskCreationForm(request.POST)
        if form.is_valid():
            task = form.save(created_by=request.user)
            messages.success(request, f'Task "{task.name}" assigned to {task.employee.get_full_name()} successfully!')
            
            # Sync task with Google Calendar if employee has connected their calendar
            try:
                if hasattr(task.employee, 'google_calendar_credentials'):
                    success, message = GoogleCalendarService.create_task_deadline_event(
                        task.employee, 
                        task
                    )
                    if success:
                        logger.info(f"Task '{task.name}' synced to {task.employee.get_full_name()}'s Google Calendar")
                    else:
                        logger.warning(f"Failed to sync task to calendar: {message}")
            except Exception as e:
                # Don't fail task creation if calendar sync fails
                logger.error(f"Error syncing task to Google Calendar: {str(e)}")
            
            return redirect('task_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskCreationForm()
        # Set default date to today
        form.fields['date'].widget.attrs['value'] = date.today().strftime('%Y-%m-%d')
    
    return render(request, 'users/create_task.html', {
        'form': form,
        'today': date.today().strftime('%Y-%m-%d')
    })


@login_required
@user_passes_test(is_admin)
def task_detail(request, pk):
    """Admin view to see task details"""
    task = get_object_or_404(Task, pk=pk)
    
    context = {
        'task': task,
    }
    
    return render(request, 'users/task_detail.html', context)


@login_required
@user_passes_test(is_admin)
def update_task(request, pk):
    """Admin view to update a task"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskUpdateForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.name}" updated successfully!')
            return redirect('task_detail', pk=task.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskUpdateForm(instance=task)
    
    return render(request, 'users/update_task.html', {
        'form': form,
        'task': task
    })


@login_required
@user_passes_test(is_admin)
def delete_task(request, pk):
    """Admin view to delete a task"""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        task_name = task.name
        employee_name = task.employee.get_full_name()
        task.delete()
        messages.success(request, f'Task "{task_name}" for {employee_name} deleted successfully!')
        return redirect('task_list')


@login_required
def employee_tasks(request):
    """Employee view to see their assigned tasks"""
    if request.user.is_superuser:
        return redirect('task_list')  # Admins should use the main task list
    
    # Get tasks assigned to the current employee
    tasks = Task.objects.filter(employee=request.user).order_by('-created_at')
    
    # Filter by status if requested
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    # Get task statistics for the employee
    total_tasks = Task.objects.filter(employee=request.user).count()
    pending_tasks = Task.objects.filter(employee=request.user, status='PENDING').count()
    completed_tasks = Task.objects.filter(employee=request.user, status='COMPLETED').count()
    overdue_tasks = Task.objects.filter(employee=request.user, status='PENDING', date__lt=date.today()).count()
    
    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'selected_status': status,
    }
    
    return render(request, 'users/employee_tasks.html', context)


@login_required
def employee_task_detail(request, pk):
    """Employee view to see task details and mark as completed"""
    task = get_object_or_404(Task, pk=pk, employee=request.user)
    
    if request.method == 'POST' and task.status == 'PENDING':
        form = TaskCompletionForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.name}" marked as completed!')
            return redirect('employee_tasks')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskCompletionForm(instance=task) if task.status == 'PENDING' else None
    
    context = {
        'task': task,
        'form': form,
    }
    
    return render(request, 'users/employee_task_detail.html', context)


@login_required
def mark_task_completed(request, pk):
    """Quick action to mark a task as completed without form"""
    task = get_object_or_404(Task, pk=pk, employee=request.user)
    
    if request.method == 'POST' and task.status == 'PENDING':
        task.mark_completed()
        messages.success(request, f'Task "{task.name}" marked as completed!')
    
    return redirect('employee_tasks')


@login_required
@user_passes_test(is_admin)
def get_project_employees(request, project_id):
    """AJAX endpoint to get employees for a specific project"""
    try:
        if project_id == '0' or project_id == 'None':
            # Return all non-admin employees
            employees = Employee.objects.filter(is_superuser=False).values('id', 'first_name', 'last_name', 'username')
        else:
            # Get employees who are collaborators on this project
            collaborators = ProjectCollaborator.objects.filter(project_id=project_id).select_related('employee')
            employees = [
                {
                    'id': collab.employee.id,
                    'first_name': collab.employee.first_name,
                    'last_name': collab.employee.last_name,
                    'username': collab.employee.username,
                }
                for collab in collaborators
            ]
        
        return JsonResponse({'employees': list(employees)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============================================
# LEAVE MANAGEMENT VIEWS
# ============================================

@login_required
def employee_leave_dashboard(request):
    """Employee view to see leave balances and application history"""
    if request.user.is_superuser:
        messages.info(request, "Admins should use the admin leave management interface.")
        return redirect('admin_leave_requests')
    
    current_year = date.today().year
    
    # Get leave balances for current year
    leave_balances = LeaveBalance.objects.filter(
        employee=request.user,
        year=current_year
    ).select_related('leave_type')
    
    # Get recent leave applications (last 10)
    recent_applications = LeaveApplication.objects.filter(
        employee=request.user
    ).select_related('leave_type', 'reviewed_by').order_by('-applied_at')[:10]
    
    # Get pending applications count
    pending_count = LeaveApplication.objects.filter(
        employee=request.user,
        status='PENDING'
    ).count()
    
    # Calculate total leaves stats
    total_leaves = leave_balances.aggregate(
        total=Sum('total_days'),
        used=Sum('used_days'),
        remaining=Sum('remaining_days')
    )
    
    context = {
        'leave_balances': leave_balances,
        'recent_applications': recent_applications,
        'pending_count': pending_count,
        'total_leaves': total_leaves,
        'current_year': current_year,
    }
    
    return render(request, 'users/leave_dashboard.html', context)


@login_required
def apply_leave(request):
    """Employee view to apply for leave"""
    if request.user.is_superuser:
        messages.error(request, "Admins cannot apply for leaves.")
        return redirect('admin_leave_requests')
    
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, employee=request.user)
        if form.is_valid():
            leave_application = form.save()
            messages.success(
                request,
                f'Leave application submitted successfully! '
                f'{leave_application.total_days} day(s) of {leave_application.leave_type.name} requested. '
                f'Status: Pending approval.'
            )
            return redirect('employee_leave_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LeaveApplicationForm(employee=request.user)
    
    # Get current balances for display
    current_year = date.today().year
    leave_balances = LeaveBalance.objects.filter(
        employee=request.user,
        year=current_year
    ).select_related('leave_type')
    
    context = {
        'form': form,
        'leave_balances': leave_balances,
    }
    
    return render(request, 'users/apply_leave.html', context)


@login_required
def leave_application_detail(request, pk):
    """Employee view to see their leave application details"""
    application = get_object_or_404(
        LeaveApplication,
        pk=pk,
        employee=request.user
    )
    
    context = {
        'application': application,
    }
    
    return render(request, 'users/leave_detail.html', context)


@login_required
def cancel_leave_application(request, pk):
    """Employee view to cancel a pending leave application"""
    application = get_object_or_404(
        LeaveApplication,
        pk=pk,
        employee=request.user,
        status='PENDING'
    )
    
    if request.method == 'POST':
        application.status = 'CANCELLED'
        application.save()
        messages.success(request, f'Leave application for {application.total_days} day(s) cancelled successfully!')
        return redirect('employee_leave_dashboard')
    
    return redirect('leave_application_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def admin_leave_requests(request):
    """Admin view to see all leave requests with filtering"""
    applications = LeaveApplication.objects.all().select_related(
        'employee',
        'leave_type',
        'reviewed_by'
    ).order_by('-applied_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        applications = applications.filter(status=status)
    else:
        # Default to showing pending applications first
        applications = applications.order_by(
            '-status',  # PENDING comes before others
            '-applied_at'
        )
    
    # Filter by employee
    employee_id = request.GET.get('employee')
    if employee_id:
        applications = applications.filter(employee_id=employee_id)
    
    # Filter by leave type
    leave_type_id = request.GET.get('leave_type')
    if leave_type_id:
        applications = applications.filter(leave_type_id=leave_type_id)
    
    # Get employees and leave types for filters
    employees = Employee.objects.filter(is_superuser=False).order_by('first_name', 'last_name')
    leave_types = LeaveType.objects.all()
    
    # Get statistics
    pending_count = LeaveApplication.objects.filter(status='PENDING').count()
    approved_count = LeaveApplication.objects.filter(status='APPROVED').count()
    rejected_count = LeaveApplication.objects.filter(status='REJECTED').count()
    
    context = {
        'applications': applications,
        'employees': employees,
        'leave_types': leave_types,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'selected_status': status,
        'selected_employee': employee_id,
        'selected_leave_type': leave_type_id,
    }
    
    return render(request, 'users/admin_leave_requests.html', context)


@login_required
@user_passes_test(is_admin)
def admin_leave_detail(request, pk):
    """Admin view to see leave application details"""
    application = get_object_or_404(LeaveApplication, pk=pk)
    
    # Get employee's leave balance for the application year
    leave_balance = LeaveBalance.objects.filter(
        employee=application.employee,
        leave_type=application.leave_type,
        year=application.start_date.year
    ).first()
    
    context = {
        'application': application,
        'leave_balance': leave_balance,
    }
    
    return render(request, 'users/admin_leave_detail.html', context)


@login_required
@user_passes_test(is_admin)
def approve_leave(request, pk):
    """Admin action to approve a leave application"""
    application = get_object_or_404(LeaveApplication, pk=pk, status='PENDING')
    
    if request.method == 'POST':
        remarks = request.POST.get('admin_remarks', '')
        
        try:
            # Use the model's approve method which handles balance deduction
            application.approve(admin=request.user, remarks=remarks)
            
            messages.success(
                request,
                f'Leave application approved! {application.total_days} day(s) of '
                f'{application.leave_type.name} deducted from {application.employee.get_full_name()}\'s balance.'
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('admin_leave_detail', pk=pk)
        
        return redirect('admin_leave_requests')
    
    return redirect('admin_leave_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def reject_leave(request, pk):
    """Admin action to reject a leave application"""
    application = get_object_or_404(LeaveApplication, pk=pk, status='PENDING')
    
    if request.method == 'POST':
        remarks = request.POST.get('admin_remarks', '')
        
        if not remarks:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('admin_leave_detail', pk=pk)
        
        # Use the model's reject method
        application.reject(admin=request.user, remarks=remarks)
        
        messages.success(
            request,
            f'Leave application rejected. {application.employee.get_full_name()} has been notified.'
        )
        return redirect('admin_leave_requests')
    
    return redirect('admin_leave_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def employee_leave_summary(request, employee_id):
    """Admin view to see an employee's complete leave summary"""
    employee = get_object_or_404(Employee, pk=employee_id)
    current_year = date.today().year
    
    # Get leave balances for current year
    leave_balances = LeaveBalance.objects.filter(
        employee=employee,
        year=current_year
    ).select_related('leave_type')
    
    # Get all leave applications for the employee
    applications = LeaveApplication.objects.filter(
        employee=employee
    ).select_related('leave_type', 'reviewed_by').order_by('-applied_at')
    
    # Get statistics
    total_applications = applications.count()
    pending_applications = applications.filter(status='PENDING').count()
    approved_applications = applications.filter(status='APPROVED').count()
    rejected_applications = applications.filter(status='REJECTED').count()
    
    # Calculate total leaves used this year
    approved_this_year = applications.filter(
        status='APPROVED',
        start_date__year=current_year
    ).aggregate(total=Sum('total_days'))['total'] or 0
    
    context = {
        'employee': employee,
        'leave_balances': leave_balances,
        'applications': applications,
        'current_year': current_year,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'approved_this_year': approved_this_year,
    }
    
    return render(request, 'users/employee_leave_summary.html', context)
