# Google Calendar Integration Settings

## Configuration Instructions

To enable Google Calendar integration in your Django Employee Management System:

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Web application" as the application type

### 2. Configure OAuth 2.0 Settings
In your OAuth 2.0 client configuration, add these redirect URIs:
- `http://localhost:8000/google-calendar/callback/`
- `https://yourdomain.com/google-calendar/callback/` (for production)

### 3. Add to Django Settings
Add the following to your `settings.py` file:

```python
# Google Calendar Integration
GOOGLE_OAUTH2_CLIENT_ID = 'your-google-oauth2-client-id'
GOOGLE_OAUTH2_CLIENT_SECRET = 'your-google-oauth2-client-secret'
```

### 4. Install Required Packages
Run the following command to install the Google API packages:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Note: You may need to use older versions if you encounter compatibility issues:
```bash
pip install google-auth==1.35.0 google-auth-oauthlib==0.4.6 google-auth-httplib2==0.1.0 google-api-python-client==2.70.0
```

### 5. Environment Variables (Recommended)
Instead of hardcoding credentials, use environment variables:

```python
import os

# Google Calendar Integration
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')
```

### 6. Database Migration
The Google Calendar credentials table has been created. The integration will automatically:
- Store OAuth2 tokens securely in the database
- Handle token refresh automatically
- Link credentials to specific employees

### 7. Using the Integration

#### For Employees:
- Go to Profile → Google Calendar Integration
- Click "Connect Google Calendar" 
- Authenticate with Google
- Calendar events will be automatically created for project deadlines

#### For Developers:
```python
from users.google_calendar_utils import GoogleCalendarService

# Create a project deadline event
employee = Employee.objects.get(id=1)
project = Project.objects.get(id=1)
success, message = GoogleCalendarService.create_project_deadline_event(employee, project)

# Create a custom event
event_data = {
    'summary': 'Team Meeting',
    'description': 'Weekly team sync',
    'start': {
        'dateTime': '2024-01-15T10:00:00',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2024-01-15T11:00:00',
        'timeZone': 'Asia/Kolkata',
    }
}
success, message = GoogleCalendarService.create_event(employee, event_data)
```

### Security Notes:
- OAuth tokens are stored encrypted in the database
- Refresh tokens are used to automatically renew expired access tokens
- Users can revoke access at any time
- All credentials are deleted when an employee account is removed

### Troubleshooting:
1. **Import Errors**: Make sure all Google API packages are installed
2. **Authentication Errors**: Check your OAuth 2.0 client ID and secret
3. **Redirect URI Errors**: Ensure the redirect URIs match exactly in Google Cloud Console
4. **Permission Errors**: Make sure the Google Calendar API is enabled in your project