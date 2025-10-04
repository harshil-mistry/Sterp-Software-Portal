# 🚀 Leave Management - Quick Start Guide

## ✅ Pre-Flight Checklist

Before testing the leave management system, ensure:

1. **All migrations are applied:**
   ```powershell
   python manage.py migrate
   ```
   Expected output:
   ```
   Applying users.0009_leavetype_leavebalance_leaveapplication... OK
   Applying users.0010_initialize_leave_data... OK
   ```

2. **Leave types exist (check via Django admin or shell):**
   ```powershell
   python manage.py shell
   ```
   ```python
   from users.models import LeaveType
   LeaveType.objects.all()
   # Should show: Casual Leave (7), Sick Leave (11), Paid Leave (5)
   ```

3. **Existing employees have balances:**
   ```python
   from users.models import LeaveBalance
   LeaveBalance.objects.filter(year=2025).count()
   # Should be: number_of_employees * 3
   ```

---

## 🎯 Quick Test Scenarios

### Scenario 1: Employee Applies for Leave (2 minutes)

**Step 1:** Login as Employee
```
URL: /login/
Username: (any non-admin employee)
Password: (employee password)
```

**Step 2:** Navigate to Leave Dashboard
```
Click: Profile dropdown → "My Leaves"
OR
Direct URL: /leaves/
```

**Expected:**
- See 4 stat cards (Total: 23, Available: 23, Used: 0, Pending: 0)
- See 3 balance cards (Casual: 7, Sick: 11, Paid: 5)
- "Apply for Leave" button visible

**Step 3:** Apply for Leave
```
Click: "Apply for Leave" button
Fill in:
  - Leave Type: Casual Leave
  - Start Date: Tomorrow's date
  - End Date: 3 days from tomorrow
  - Reason: "Family function"
Click: "Submit Application"
```

**Expected:**
- Success message: "Leave application submitted successfully! 3 day(s) of Casual Leave requested..."
- Redirected to dashboard
- Pending count changes to 1
- Application visible in recent applications table with "Pending" status

---

### Scenario 2: Admin Approves Leave (2 minutes)

**Step 1:** Login as Admin
```
Logout from employee account
Login with admin credentials
```

**Step 2:** Navigate to Leave Requests
```
Click: Profile dropdown → "Leave Requests"
OR
Direct URL: /admin/leaves/
```

**Expected:**
- Pending Requests stat shows 1
- Table shows the application submitted by employee

**Step 3:** Review Application
```
Click: "Review" button on the pending application
```

**Expected:**
- Left panel: Employee info with photo, department
- Balance card shows: Casual Leave - 7 total, 0 used, 7 remaining
- Right panel: Application details
- "Approve" and "Reject" buttons visible

**Step 4:** Approve the Leave
```
Click: "Approve" button
Modal opens:
  - Add remarks (optional): "Approved. Enjoy!"
Click: "Approve" button in modal
```

**Expected:**
- Success message: "Leave application approved! 3 day(s) of Casual Leave deducted..."
- Redirected to leave requests list
- Pending count decreases to 0
- Approved count increases to 1

**Step 5:** Verify Balance Deduction
```
Click: "Review" on the same application again
Check the balance card
```

**Expected:**
- Casual Leave balance now shows:
  - Total: 7
  - Used: 3
  - Remaining: 4

---

### Scenario 3: Employee Checks Updated Balance (1 minute)

**Step 1:** Login as Employee Again
```
Logout from admin
Login as the employee who applied
```

**Step 2:** View Dashboard
```
Navigate to: /leaves/
```

**Expected:**
- Stats updated:
  - Total: 23
  - Available: 20 (23 - 3)
  - Used: 3
  - Pending: 0
- Casual Leave card shows: 4 remaining (was 7)
- Application in table shows "Approved" status with green badge

**Step 3:** View Application Detail
```
Click: "View" on the approved application
```

**Expected:**
- Status banner is green
- Shows "Approved by [Admin Name]"
- Review information section visible with admin remarks
- "Cancel Application" button NOT visible (already approved)

---

### Scenario 4: Insufficient Balance Test (1 minute)

**Still as Employee:**

**Step 1:** Try to Apply for More Than Available
```
Click: "Apply for Leave"
Fill in:
  - Leave Type: Casual Leave
  - Start Date: Next week
  - End Date: 10 days later (total 10 days)
  - Reason: "Long vacation"
Click: "Submit Application"
```

**Expected:**
- Form validation error
- Error message: "You only have 4 Casual Leave day(s) remaining, but requested 10 day(s)"
- Form does NOT submit
- Balance unchanged

---

### Scenario 5: Admin Rejects Leave (2 minutes)

**Step 1:** As Employee, Apply Again
```
Leave Type: Sick Leave
Start Date: Next Monday
End Date: Next Tuesday (2 days)
Reason: "Not feeling well"
Submit
```

**Step 2:** Login as Admin
```
Navigate to: /admin/leaves/
```

**Expected:**
- Pending count: 1

**Step 3:** Review and Reject
```
Click: "Review" on the sick leave application
Click: "Reject" button
Modal opens:
  - Remarks (REQUIRED): "Please provide medical certificate"
Click: "Reject" button in modal
```

**Expected:**
- Success message: "Leave application rejected..."
- Application status: Rejected (red badge)
- Balance unchanged (still 11 sick leaves)

**Step 4:** Verify Balance NOT Deducted
```
Check balance card or view dashboard as employee
```

**Expected:**
- Sick Leave balance: 11 remaining (unchanged)

---

### Scenario 6: New Employee Auto-Assignment (2 minutes)

**Step 1:** Create New Employee
```
Login as admin
Navigate to: /create-employee/
Fill in all required fields:
  - Username: test_employee_2
  - Email: test2@example.com
  - First Name: Test
  - Last Name: Employee2
  - Department: IT
  - etc.
Submit
```

**Expected:**
- Employee created successfully
- Email sent notification

**Step 2:** Verify Auto-Assigned Balances
```
Method 1 - Django Shell:
python manage.py shell

from users.models import Employee, LeaveBalance
emp = Employee.objects.get(username='test_employee_2')
balances = LeaveBalance.objects.filter(employee=emp)
for b in balances:
    print(f"{b.leave_type.name}: {b.remaining_days}")

Expected output:
Casual Leave: 7
Sick Leave: 11
Paid Leave: 5

Method 2 - Admin Panel:
Navigate to: /admin/employee/<new_employee_id>/leaves/
```

**Expected:**
- Employee leave summary page loads
- Shows 3 balance cards with full balances
- Total applications: 0
- Year: 2025

---

## 🎨 Visual Verification

### Dashboard Should Look Like:
```
┌─────────────────────────────────────────────────┐
│  Leave Management                    [Apply]    │
├─────────────────────────────────────────────────┤
│  [Total: 23]  [Available: 20]  [Used: 3]  [0]  │
├─────────────────────────────────────────────────┤
│  Leave Balances 2025                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Casual   │  │ Sick     │  │ Paid     │     │
│  │ 4 left   │  │ 11 left  │  │ 5 left   │     │
│  │ [=====>] │  │ [======] │  │ [======] │     │
│  │ 3/7 used │  │ 0/11     │  │ 0/5      │     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│  Recent Applications                            │
│  ┌───────────────────────────────────────────┐ │
│  │ Casual | 3 days | Jan 10-12 | Approved   │ │
│  │ Sick   | 2 days | Jan 15-16 | Rejected   │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Status Colors:
- 🟢 Green = Approved
- 🟡 Yellow = Pending
- 🔴 Red = Rejected
- ⚫ Gray = Cancelled

---

## 🔍 Troubleshooting

### Issue: No balances showing
**Check:**
```python
from users.models import LeaveBalance
LeaveBalance.objects.filter(employee__username='your_username')
```
**Fix:** Run migration 0010 or create manually

### Issue: Signal not creating balances for new employee
**Check:**
```python
# In users/apps.py
def ready(self):
    import users.signals  # Should be present
```
**Fix:** Ensure apps.py has ready() method

### Issue: Balance not deducting on approval
**Check:**
```python
# In users/models.py LeaveApplication
def approve(self, admin, remarks=""):
    # Should call balance.save()
```
**Fix:** Verify approve() method implementation

### Issue: Form validation not working
**Check:**
```python
# In users/forms.py LeaveApplicationForm
def __init__(self, *args, employee=None, **kwargs):
    self.employee = employee  # Must be set
```
**Fix:** Ensure employee parameter passed when creating form

---

## 📝 Quick Commands

### Reset Leave Balances (Careful!)
```python
from users.models import LeaveBalance
LeaveBalance.objects.all().delete()
# Then run migration 0010 again
python manage.py migrate users 0009
python manage.py migrate users 0010
```

### Check All Pending Applications
```python
from users.models import LeaveApplication
LeaveApplication.objects.filter(status='PENDING').count()
```

### Manually Approve Application
```python
from users.models import LeaveApplication, Employee
app = LeaveApplication.objects.get(id=1)
admin = Employee.objects.filter(is_superuser=True).first()
app.approve(admin=admin, remarks="Manual approval")
```

---

## ✅ Success Indicators

After completing all scenarios, you should have:
- ✅ Submitted at least 2 leave applications
- ✅ 1 approved application with balance deducted
- ✅ 1 rejected application with balance unchanged
- ✅ Verified insufficient balance validation
- ✅ Created new employee with auto-assigned balances
- ✅ Seen all 6 template pages working

---

## 🎓 Next Steps

1. Test with multiple employees
2. Test edge cases (same dates, past dates, etc.)
3. Review admin leave summary page
4. Test all filter combinations
5. Check responsiveness on mobile
6. Verify navigation links work from all pages

---

## 📞 Need Help?

Check the detailed guides:
- `TESTING_GUIDE.md` - Comprehensive testing checklist
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `LEAVE_MANAGEMENT_PROGRESS.md` - Implementation progress

Happy testing! 🚀
