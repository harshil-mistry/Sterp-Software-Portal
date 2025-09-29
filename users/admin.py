from django.contrib import admin
from .models import Employee, GoogleCalendarCredentials
from django.contrib.auth.models import User

# Register your models here.
admin.site.register(Employee)
admin.site.register(User)


@admin.register(GoogleCalendarCredentials)
class GoogleCalendarCredentialsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__email')
    readonly_fields = ('created_at', 'updated_at')
    
    # Don't show sensitive fields in the list view
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('token', 'refresh_token', 'client_secret')
        return self.readonly_fields