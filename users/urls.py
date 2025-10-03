from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create-employee/', views.create_employee, name='create_employee'),
    path('profile/', views.employee_profile, name='employee_profile'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login', template_name='users/logout.html'), name='logout'),
    path('delete-employee/<int:pk>/', views.delete_employee, name='delete_employee'),
    path('change-password/', views.CustomPasswordChangeView.as_view(), name='change_password'),
    path('projects/', views.project_list, name='project_list'),
    path('create-project/', views.create_project, name='create_project'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/edit/', views.update_project, name='update_project'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('my-projects/', views.employee_projects, name='employee_projects'),
    path('my-projects/<int:pk>/', views.employee_project_detail, name='employee_project_detail'),
    # Google Calendar Integration
    path('google-calendar/connect/', views.google_calendar_connect, name='google_calendar_connect'),
    path('google-calendar/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('google-calendar/disconnect/', views.google_calendar_disconnect, name='google_calendar_disconnect'),
    path('add-calendar-event/<int:employee_id>/', views.admin_add_calendar_event, name='admin_add_calendar_event'),
    # Task Management URLs
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.update_task, name='update_task'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('my-tasks/', views.employee_tasks, name='employee_tasks'),
    path('my-tasks/<int:pk>/', views.employee_task_detail, name='employee_task_detail'),
    path('my-tasks/<int:pk>/complete/', views.mark_task_completed, name='mark_task_completed'),
    # AJAX endpoint for getting project employees
    path('api/project/<str:project_id>/employees/', views.get_project_employees, name='get_project_employees'),
]
