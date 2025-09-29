"""
Google Calendar Integration - Example Usage

This file demonstrates how to use the Google Calendar integration
in the Django Employee Management System.
"""

from users.models import Employee, Project
from users.google_calendar_utils import GoogleCalendarService
from datetime import datetime, date


def example_create_project_events():
    """
    Example: Create calendar events for all employees assigned to a project
    """
    # Get a project
    project = Project.objects.first()
    if not project:
        print("No projects found. Create a project first.")
        return
    
    # Get all collaborators on the project
    collaborators = project.collaborators.all()
    
    for collaborator in collaborators:
        employee = collaborator.employee
        
        # Check if employee has Google Calendar connected
        if hasattr(employee, 'google_calendar_credentials'):
            # Create project start event
            success, message = GoogleCalendarService.create_project_start_event(employee, project)
            print(f"Project start event for {employee.get_full_name()}: {message}")
            
            # Create project deadline event
            success, message = GoogleCalendarService.create_project_deadline_event(employee, project)
            print(f"Project deadline event for {employee.get_full_name()}: {message}")
        else:
            print(f"{employee.get_full_name()} has not connected Google Calendar")


def example_create_custom_event():
    """
    Example: Create a custom calendar event for an employee
    """
    # Get an employee
    employee = Employee.objects.first()
    if not employee:
        print("No employees found.")
        return
    
    # Check if employee has Google Calendar connected
    if not hasattr(employee, 'google_calendar_credentials'):
        print(f"{employee.get_full_name()} has not connected Google Calendar")
        return
    
    # Create a custom event
    event_data = {
        'summary': 'Team Meeting - Weekly Sync',
        'description': 'Weekly team synchronization meeting\n\nAgenda:\n- Project updates\n- Blockers discussion\n- Next week planning',
        'location': 'Conference Room A, STERP Softwares',
        'start': {
            'dateTime': '2024-02-15T10:00:00',
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': '2024-02-15T11:30:00',
            'timeZone': 'Asia/Kolkata',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 60},    # 1 hour before
                {'method': 'popup', 'minutes': 15},    # 15 minutes before
            ],
        },
        'attendees': [
            {'email': employee.email},
            {'email': 'manager@sterpsoftwares.com'},
        ],
    }
    
    success, message = GoogleCalendarService.create_event(employee, event_data)
    print(f"Custom event creation: {message}")


def example_create_recurring_meeting():
    """
    Example: Create a recurring weekly meeting
    """
    employee = Employee.objects.first()
    if not employee or not hasattr(employee, 'google_calendar_credentials'):
        print("Employee not found or Google Calendar not connected")
        return
    
    event_data = {
        'summary': 'Weekly Team Stand-up',
        'description': 'Daily stand-up meeting for the development team',
        'start': {
            'dateTime': '2024-02-12T09:00:00',
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': '2024-02-12T09:30:00',
            'timeZone': 'Asia/Kolkata',
        },
        'recurrence': [
            'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR'  # Every weekday
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    
    success, message = GoogleCalendarService.create_event(employee, event_data)
    print(f"Recurring meeting creation: {message}")


def example_bulk_calendar_events():
    """
    Example: Create calendar events for all employees
    """
    # Get all employees
    employees = Employee.objects.filter(is_superuser=False)
    
    for employee in employees:
        if hasattr(employee, 'google_calendar_credentials'):
            # Create a company-wide event
            event_data = {
                'summary': 'All Hands Meeting',
                'description': 'Monthly all-hands company meeting',
                'start': {
                    'dateTime': '2024-02-20T14:00:00',
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': '2024-02-20T15:00:00',
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
            }
            
            success, message = GoogleCalendarService.create_event(employee, event_data)
            print(f"All hands event for {employee.get_full_name()}: {'✓' if success else '✗'}")


# Usage in Django views or management commands:
"""
# In a Django view
def create_project_calendar_events(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Create events for all collaborators
    for collaborator in project.collaborators.all():
        employee = collaborator.employee
        if hasattr(employee, 'google_calendar_credentials'):
            GoogleCalendarService.create_project_deadline_event(employee, project)
    
    messages.success(request, "Calendar events created for all connected employees!")
    return redirect('project_detail', pk=project_id)

# In a Django management command (create management/commands/create_calendar_events.py)
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create calendar events for upcoming project deadlines'
    
    def handle(self, *args, **options):
        # Find projects with deadlines in the next 7 days
        from datetime import timedelta
        upcoming_deadline = date.today() + timedelta(days=7)
        
        projects = Project.objects.filter(
            end_date__lte=upcoming_deadline,
            end_date__gte=date.today()
        )
        
        for project in projects:
            for collaborator in project.collaborators.all():
                employee = collaborator.employee
                if hasattr(employee, 'google_calendar_credentials'):
                    success, message = GoogleCalendarService.create_project_deadline_event(employee, project)
                    self.stdout.write(f"{employee.get_full_name()}: {message}")

# Run with: python manage.py create_calendar_events
"""


if __name__ == "__main__":
    print("Google Calendar Integration Examples")
    print("====================================")
    print("This file contains example usage of the Google Calendar integration.")
    print("Import these functions in Django views or management commands to use them.")