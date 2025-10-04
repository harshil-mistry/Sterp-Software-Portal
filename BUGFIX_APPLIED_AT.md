# Bug Fix: FieldError 'created_at' → 'applied_at'

## Issue
```
FieldError at /admin-leaves/
Cannot resolve keyword 'created_at' into field. 
Choices are: admin_remarks, applied_at, employee, employee_id, end_date, id, 
leave_type, leave_type_id, reason, reviewed_at, reviewed_by, reviewed_by_id, 
start_date, status, total_days, updated_at
```

## Root Cause
The `LeaveApplication` model uses `applied_at` for the timestamp field, but the views and templates were using `created_at`.

## Files Fixed

### Views (users/views.py)
Fixed 4 occurrences:
1. Line ~972: `employee_leave_dashboard` - Order by `-applied_at`
2. Line ~1079: `admin_leave_requests` - Order by `-applied_at`
3. Line ~1089: `admin_leave_requests` - Default ordering `-applied_at`
4. Line ~1215: `employee_leave_summary` - Order by `-applied_at`

### Templates
Fixed 5 template files:
1. **leave_dashboard.html** - Display applied date
2. **leave_detail.html** - Display applied date with time
3. **admin_leave_requests.html** - Display applied date in table
4. **admin_leave_detail.html** - Display applied date with time
5. **employee_leave_summary.html** - Display applied date in history table

## Changes Made
- Replaced all `created_at` → `applied_at` in leave-related queries
- Updated all template references from `{{ application.created_at }}` → `{{ application.applied_at }}`

## Status
✅ Fixed - The leave management system should now work correctly!

## Testing
Run the server and test:
```powershell
python manage.py runserver
```

Then navigate to:
- Employee: `/leaves/` - Should load without error
- Admin: `/admin/leaves/` - Should load without error
