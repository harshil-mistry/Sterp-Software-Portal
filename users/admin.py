from django.contrib import admin
from .models import Employee, GoogleCalendarCredentials, LeaveType, LeaveBalance, LeaveApplication, Attendance
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
    
@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_days', 'created_at')
    search_fields = ('name',)


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('remaining_days',)


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'applied_at')
    list_filter = ('status', 'leave_type', 'applied_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    readonly_fields = ('applied_at', 'updated_at', 'reviewed_at')
    fieldsets = (
        ('Leave Details', {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_remarks')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in_time', 'check_out_time', 'work_hours', 'status', 'marked_by_admin')
    list_filter = ('status', 'date', 'marked_by_admin')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('created_at', 'updated_at', 'work_hours')
    date_hierarchy = 'date'
    fieldsets = (
        ('Employee & Date', {
            'fields': ('employee', 'date')
        }),
        ('Check In/Out Times', {
            'fields': ('check_in_time', 'check_out_time', 'work_hours')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'marked_by_admin')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )