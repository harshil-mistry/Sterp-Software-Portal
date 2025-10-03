"""
Google Calendar integration utilities
"""

import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .models import GoogleCalendarCredentials


class GoogleCalendarService:
    """Service class to handle Google Calendar integration"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    @classmethod
    def _check_availability(cls):
        
        if not hasattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID') or not hasattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET'):
            return False, "Google OAuth2 credentials not configured in settings."
        
        return True, ""
    
    @classmethod
    def get_authorization_url(cls, request, employee):
        """Generate Google OAuth2 authorization URL"""
        available, error = cls._check_availability()
        if not available:
            raise Exception(error)
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [request.build_absolute_uri('/google-calendar/callback/')]
                }
            },
            scopes=cls.SCOPES
        )
        flow.redirect_uri = request.build_absolute_uri('/google-calendar/callback/')
        
        # Store employee ID in session for callback
        request.session['google_auth_employee_id'] = employee.id
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session for security
        request.session['google_auth_state'] = state
        
        return authorization_url
    
    @classmethod
    def handle_callback(cls, request):
        """Handle OAuth2 callback and store credentials"""
        available, error = cls._check_availability()
        if not available:
            return False, error
        
        state = request.session.get('google_auth_state')
        employee_id = request.session.get('google_auth_employee_id')
        
        if not state or not employee_id:
            return False, "Invalid session data"
        
        try:
            from .models import Employee
            employee = Employee.objects.get(id=employee_id)
            
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [request.build_absolute_uri('/google-calendar/callback/')]
                    }
                },
                scopes=cls.SCOPES,
                state=state
            )
            flow.redirect_uri = request.build_absolute_uri('/google-calendar/callback/')
            
            # Get the authorization response
            authorization_response = request.build_absolute_uri()
            flow.fetch_token(authorization_response=authorization_response)
            
            credentials = flow.credentials
            
            # Store credentials in database
            calendar_creds, created = GoogleCalendarCredentials.objects.get_or_create(
                employee=employee,
                defaults={
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': json.dumps(credentials.scopes),
                }
            )
            
            if not created:
                # Update existing credentials
                calendar_creds.token = credentials.token
                calendar_creds.refresh_token = credentials.refresh_token
                calendar_creds.token_uri = credentials.token_uri
                calendar_creds.client_id = credentials.client_id
                calendar_creds.client_secret = credentials.client_secret
                calendar_creds.scopes = json.dumps(credentials.scopes)
                calendar_creds.save()
            
            # Clear session data
            del request.session['google_auth_state']
            del request.session['google_auth_employee_id']
            
            return True, "Google Calendar connected successfully!"
            
        except Exception as e:
            return False, f"Error connecting to Google Calendar: {str(e)}"
    
    @classmethod
    def get_calendar_service(cls, employee):
        """Get Google Calendar service object for an employee"""
        available, error = cls._check_availability()
        if not available:
            return None
        
        try:
            calendar_creds = GoogleCalendarCredentials.objects.get(employee=employee)
            
            credentials = Credentials(
                token=calendar_creds.token,
                refresh_token=calendar_creds.refresh_token,
                token_uri=calendar_creds.token_uri,
                client_id=calendar_creds.client_id,
                client_secret=calendar_creds.client_secret,
                scopes=json.loads(calendar_creds.scopes)
            )
            
            # Refresh token if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update stored token
                calendar_creds.token = credentials.token
                calendar_creds.save()
            
            service = build('calendar', 'v3', credentials=credentials)
            return service
            
        except GoogleCalendarCredentials.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error creating calendar service: {e}")
            return None
    
    @classmethod
    def revoke_credentials(cls, employee):
        """Revoke and delete Google Calendar credentials for an employee"""
        try:
            calendar_creds = GoogleCalendarCredentials.objects.get(employee=employee)
            
            # Try to revoke the token
            credentials = Credentials(
                token=calendar_creds.token,
                refresh_token=calendar_creds.refresh_token,
                token_uri=calendar_creds.token_uri,
                client_id=calendar_creds.client_id,
                client_secret=calendar_creds.client_secret,
                scopes=json.loads(calendar_creds.scopes)
            )
                
            # Revoke credentials with Google
            try:
                credentials.revoke(Request())
            except Exception as revoke_error:
                print(f"Error revoking token with Google: {revoke_error}")
            
            # Delete from database
            calendar_creds.delete()
            
            return True, "Google Calendar disconnected successfully!"
            
        except GoogleCalendarCredentials.DoesNotExist:
            return False, "No Google Calendar connection found"
        except Exception as e:
            return False, f"Error disconnecting Google Calendar: {str(e)}"
    
    @classmethod
    def create_event(cls, employee, event_data):
        """Create an event in employee's Google Calendar"""
        service = cls.get_calendar_service(employee)
        if not service:
            return False, "Google Calendar not connected"
        
        try:
            event = service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            return True, f"Event created: {event.get('htmlLink')}"
            
        except Exception as e:
            return False, f"Error creating event: {str(e)}"
    
    @classmethod
    def create_project_deadline_event(cls, employee, project):
        """Create a project deadline event in employee's calendar"""
        available, error = cls._check_availability()
        if not available:
            return False, error
            
        from datetime import datetime, timedelta
        
        event_data = {
            'summary': f'Project Deadline: {project.name}',
            'description': f'Project: {project.name}\nDescription: {project.description}\nPriority: {project.get_priority_display()}',
            'start': {
                'date': project.end_date.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'date': project.end_date.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},       # 1 hour before
                ],
            },
        }
        
        return cls.create_event(employee, event_data)
    
    @classmethod
    def create_project_start_event(cls, employee, project):
        """Create a project start event in employee's calendar"""
        available, error = cls._check_availability()
        if not available:
            return False, error
            
        event_data = {
            'summary': f'Project Start: {project.name}',
            'description': f'Project: {project.name}\nDescription: {project.description}\nPriority: {project.get_priority_display()}',
            'start': {
                'date': project.start_date.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'date': project.start_date.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 60},      # 1 hour before
                    {'method': 'popup', 'minutes': 15},      # 15 minutes before
                ],
            },
        }
        
        return cls.create_event(employee, event_data)
    
    @classmethod
    def create_task_deadline_event(cls, employee, task):
        """Create a task deadline event in employee's calendar"""
        available, error = cls._check_availability()
        if not available:
            return False, error
        
        # Build description with project info if linked
        description = (
            f'Task: {task.name}\n'
            f'Description: {task.description}\n'
            f'Priority: {task.get_priority_display()}\n'
            f'Assigned by: {task.created_by.get_full_name()}'
        )
        
        if task.project:
            description += f'\nProject: {task.project.name}'
            
        event_data = {
            'summary': f'Task Due: {task.name}',
            'description': description,
            'start': {
                'date': task.date.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'date': task.date.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},       # 1 hour before
                ],
            },
            'colorId': '11',  # Red color for tasks to make them stand out
        }
        
        return cls.create_event(employee, event_data)
    
    @classmethod
    def delete_project_events(cls, employee, project):
        """Delete project-related events from employee's calendar"""
        available, error = cls._check_availability()
        if not available:
            return False, error
            
        service = cls.get_calendar_service(employee)
        if not service:
            return False, "Google Calendar not connected"
        
        try:
            # Search for events related to this project
            events_result = service.events().list(
                calendarId='primary',
                q=f'Project: {project.name}',
                maxResults=50
            ).execute()
            
            events = events_result.get('items', [])
            deleted_count = 0
            
            for event in events:
                # Check if this is a project-related event by looking at the summary or description
                summary = event.get('summary', '')
                description = event.get('description', '')
                
                if (f'Project: {project.name}' in description or 
                    f'Project Start: {project.name}' in summary or 
                    f'Project Deadline: {project.name}' in summary):
                    
                    try:
                        service.events().delete(
                            calendarId='primary',
                            eventId=event['id']
                        ).execute()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete event {event['id']}: {str(e)}")
            
            if deleted_count > 0:
                return True, f"Deleted {deleted_count} project-related events"
            else:
                return True, "No project events found to delete"
                
        except Exception as e:
            return False, f"Error deleting project events: {str(e)}"