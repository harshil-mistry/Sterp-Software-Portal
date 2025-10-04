# Leave Management System - Testing Guide

## 🧪 Complete Testing Checklist

### Prerequisites
1. Ensure all migrations are applied:
   ```powershell
   python manage.py migrate
   ```

2. Verify leave types are created (should exist from migration 0010):
   - Casual Leave (7 days)
   - Sick Leave (11 days)
   - Paid Leave (5 days)

3. Existing employees should have leave balances for current year (2025)

---

## Employee Tests

### 1. Access Leave Dashboard
- **URL**: `/leaves/`
- **Login as**: Any non-admin employee
- **Expected**:
  - See 4 statistics cards (Total, Available, Used, Pending)
  - See 3 leave balance cards (Casual, Sick, Paid)
  - Each balance shows total, used, remaining
  - Progress bars show utilization
  - Recent applications table (may be empty initially)
  - "Apply for Leave" button visible

### 2. Apply for Leave
- **URL**: `/leaves/apply/`
- **Steps**:
  1. Click "Apply for Leave" from dashboard
  2. Select leave type (e.g., Casual Leave)
  3. Choose start date (e.g., today or future date)
  4. Choose end date (same or later than start date)
  5. Enter reason (e.g., "Personal work")
  6. Click "Submit Application"
- **Expected**:
  - Form validates dates (end date >= start date)
  - Form checks balance availability
  - Success message shown
  - Redirects to dashboard
  - Application appears in recent applications with "Pending" status

### 3. View Leave Application Details
- **URL**: `/leaves/<application_id>/`
- **Steps**:
  1. Click "View" on any application from dashboard
- **Expected**:
  - See all application details (type, dates, duration, reason)
  - See status banner (yellow for pending)
  - "Cancel Application" button visible if status is PENDING

### 4. Cancel Pending Application
- **Steps**:
  1. Open a pending application detail
  2. Click "Cancel Application"
  3. Confirm in popup
- **Expected**:
  - Success message shown
  - Status changes to "Cancelled"
  - "Cancel" button disappears

### 5. Insufficient Balance Test
- **Steps**:
  1. Try to apply for more days than available
  2. Example: If you have 7 casual leaves, try to apply for 10 days
- **Expected**:
  - Form validation error
  - Message: "Insufficient leave balance"

### 6. Invalid Date Test
- **Steps**:
  1. Try to set end date before start date
- **Expected**:
  - Form validation error
  - Message about date validation

---

## Admin Tests

### 7. View All Leave Requests
- **URL**: `/admin/leaves/`
- **Login as**: Admin/Superuser
- **Expected**:
  - See 3 statistics cards (Pending, Approved, Rejected)
  - See table of all leave applications
  - Each row shows employee name, department, leave type, dates, status
  - Filter dropdowns available (Status, Employee, Leave Type)

### 8. Filter Leave Requests
- **Steps**:
  1. Select "Pending" from Status dropdown
  2. Click "Apply Filters"
- **Expected**:
  - Table shows only pending applications
  - URL updates with query parameters

### 9. View Leave Request Detail (Admin)
- **URL**: `/admin/leaves/<application_id>/`
- **Steps**:
  1. Click "Review" on any pending application
- **Expected**:
  - Left sidebar: Employee info with avatar, department, email
  - Leave balance card showing current balance for that leave type
  - Right side: Application details (dates, reason, etc.)
  - If pending: "Approve" and "Reject" buttons visible
  - If already reviewed: Shows reviewer name and date

### 10. Approve Leave Application
- **Steps**:
  1. Open a pending application detail
  2. Click "Approve" button
  3. Add optional remarks in modal
  4. Click "Approve" in modal
- **Expected**:
  - Success message: "Leave application approved! X days deducted..."
  - Redirects to leave requests list
  - Application status changes to "Approved"
  - Employee's leave balance is automatically reduced
  - reviewed_by and reviewed_at fields populated

### 11. Reject Leave Application
- **Steps**:
  1. Open a pending application detail
  2. Click "Reject" button
  3. Add REQUIRED remarks in modal (e.g., "Already too many people on leave")
  4. Click "Reject" in modal
- **Expected**:
  - Success message: "Leave application rejected..."
  - Application status changes to "Rejected"
  - Leave balance NOT deducted
  - Remarks saved and visible to employee

### 12. View Employee Leave Summary
- **URL**: `/admin/employee/<employee_id>/leaves/`
- **Steps**:
  1. From leave detail page, click "View Leave Summary"
  2. Or navigate directly
- **Expected**:
  - Employee info banner with stats
  - Current year balances (all 3 types)
  - 4 statistics cards (total apps, approved, pending, days used)
  - Complete application history table
  - Links back to individual applications

### 13. Reject Without Remarks (Validation Test)
- **Steps**:
  1. Click "Reject" on pending application
  2. Leave remarks field empty
  3. Click "Reject" in modal
- **Expected**:
  - Browser validation: "Please fill out this field"
  - OR error message: "Please provide a reason for rejection"

---

## Automatic Leave Balance Assignment Test

### 14. Create New Employee
- **URL**: `/create-employee/`
- **Steps**:
  1. Login as admin
  2. Navigate to "Create Employee"
  3. Fill in all employee details
  4. Submit form
- **Expected**:
  - Employee created successfully
  - Check database or employee leave summary
  - Employee should automatically have 3 LeaveBalance records:
    - Casual: 7 days (0 used, 7 remaining)
    - Sick: 11 days (0 used, 11 remaining)
    - Paid: 5 days (0 used, 5 remaining)
  - All for current year (2025)

---

## Navigation Tests

### 15. Employee Navigation
- **Login as**: Employee
- **Expected Links**:
  - Top nav profile dropdown: "My Leaves"
  - Employee profile page: "My Leaves" quick navigation card
  - All links redirect to `/leaves/`

### 16. Admin Navigation
- **Login as**: Admin
- **Expected Links**:
  - Top nav profile dropdown: "Leave Requests"
  - Link redirects to `/admin/leaves/`

---

## Edge Cases & Validation Tests

### 17. Apply for Same Dates Twice
- **Steps**:
  1. Apply for leave from Jan 10-15
  2. Try to apply again for overlapping dates
- **Expected**:
  - System allows (no overlap validation implemented)
  - Both applications independent

### 18. Approve with Insufficient Balance
- **Note**: This shouldn't happen due to form validation, but:
- **Steps**:
  1. Have employee with 5 casual leaves remaining
  2. Apply for 5 days (pending)
  3. Admin approves (balance becomes 0)
  4. Try to approve another 5-day application
- **Expected**:
  - Error message: "Insufficient leave balance to approve"
  - Application remains pending

### 19. Cancelled Application Review Attempt
- **Steps**:
  1. Employee cancels an application
  2. Admin tries to view/review cancelled application
- **Expected**:
  - Detail page loads
  - Status shows "Cancelled"
  - No approve/reject buttons (status not PENDING)

---

## UI/UX Tests

### 20. Responsive Design
- **Steps**:
  1. Resize browser window
  2. Test on mobile viewport
- **Expected**:
  - Cards stack vertically on small screens
  - Tables become scrollable
  - Modals remain centered
  - All text readable

### 21. Dark Theme Consistency
- **Check**:
  - All pages use slate-800/900 backgrounds
  - Text is white/gray for readability
  - Cards have blur and border effects
  - Status badges color-coded (green=approved, red=rejected, yellow=pending)

---

## Database Tests

### 22. Verify Leave Balance Calculation
- **Steps**:
  1. Check employee balance before approval
  2. Note: Total=7, Used=0, Remaining=7
  3. Approve a 3-day leave
  4. Check balance again
- **Expected**:
  - Total=7 (unchanged)
  - Used=3
  - Remaining=4
  - Calculation: remaining_days = total_days - used_days

### 23. Check Review Tracking
- **Steps**:
  1. Approve/reject an application
  2. Check database or view detail page
- **Expected**:
  - reviewed_by: Admin user object
  - reviewed_at: Current timestamp
  - admin_remarks: Text entered during review

---

## Performance Tests

### 24. Load Test with Many Applications
- **Steps**:
  1. Create 50+ leave applications
  2. Load admin leave requests page
- **Expected**:
  - Page loads in reasonable time (<2 seconds)
  - Table rendering works
  - Filters work efficiently

---

## Quick Test Script

```python
# Django shell test
python manage.py shell

from users.models import Employee, LeaveType, LeaveBalance, LeaveApplication
from datetime import date, timedelta

# Get a test employee
emp = Employee.objects.filter(is_superuser=False).first()

# Check balances
balances = LeaveBalance.objects.filter(employee=emp, year=2025)
for b in balances:
    print(f"{b.leave_type.name}: {b.remaining_days}/{b.total_days}")

# Create test application
casual = LeaveType.objects.get(name="Casual Leave")
app = LeaveApplication.objects.create(
    employee=emp,
    leave_type=casual,
    start_date=date.today() + timedelta(days=5),
    end_date=date.today() + timedelta(days=7),
    total_days=3,
    reason="Test application",
    status='PENDING'
)
print(f"Created application #{app.id}")

# Simulate approval
admin = Employee.objects.filter(is_superuser=True).first()
app.approve(admin=admin, remarks="Approved for testing")
print(f"Approved! New balance: {balances.get(leave_type=casual).remaining_days}")
```

---

## Success Criteria

✅ All employee features work correctly
✅ All admin features work correctly
✅ Balances auto-deduct on approval
✅ Form validations prevent errors
✅ Navigation links functional
✅ New employees get auto-assigned balances
✅ UI matches existing dark theme
✅ No console errors
✅ Database integrity maintained

---

## Known Issues / False Positives

- Template lint errors for `widthratio` in style attributes (Django template syntax, can be ignored)
- No email notifications (feature not implemented)
- No leave overlap detection (optional feature)
