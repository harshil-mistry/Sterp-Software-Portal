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
    path('admin/add-calendar-event/<int:employee_id>/', views.admin_add_calendar_event, name='admin_add_calendar_event'),
]
