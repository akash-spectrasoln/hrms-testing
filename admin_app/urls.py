from django.urls import path
from timesheet_app import views as ts_views
from django.contrib.auth import views as auth_views
# from admin_app.views import load_states  # Ensure correct function import
from .views import *
urlpatterns=[

path('admin_index/',admin_index,name='admin_index'),
path('index/',index),
path('admin_logout/',admin_logout,name='admin_logout'),
path('add_employee/',add_employee,name='add_employee'),
path('add_holidays/', add_holidays, name='add_holidays'),
path('export-employees/', export_employees_to_excel, name='export_employees'),
path('get-states/', get_states, name='get_states'),
path('list_employees/',list_employees,name='employee_list'),

path('employee_delete/<pk>',EmployeeDeleteView.as_view(),name='employee_delete'),
path('restore_employee/<int:pk>/', restore_employee, name='restore_employee'),
path('deleted_employees/', DeletedEmployeeListView.as_view(), name='deleted_employees'),
path('leaverequestdisplay/',admin_leave_requests,name='leave_request_display'),
path('accept_leave_request/<int:leave_request_id>/', accept_leave_request, name='accept_leave_request'),
path('reject_leave_request/<int:leave_request_id>/', reject_leave_request, name='reject_leave_request'),
path('delete-leave/<int:leave_id>/', delete_leave_request, name='delete_leave_request'),

path('employee/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee_edit'),
path('ajax/load-states/', load_states, name='load_states'),  # This is for AJAX dynamic state loading
path('login/', admin_login, name='admin_login'),

# Admin Dashboard (After successful login)
path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
# path('create_admin/', create_admin_user, name='create_admin_user'),  # Add this line
path('change_password/', change_password, name='admin_change_password'),
# Forgot Password - Enter Email

path('admin_password_reset/',
     auth_views.PasswordResetView.as_view(
         template_name='admin_password_reset.html',
         email_template_name='admin_password_reset_email.txt',
         html_email_template_name='admin_password_reset_email.html',
         subject_template_name='admin_password_reset_subject.txt',
         success_url=reverse_lazy('admin_password_reset_done')    # <-- Add this!
     ), name='admin_password_reset'),

path('admin_password_reset_done/',
     auth_views.PasswordResetDoneView.as_view(
         template_name='admin_password_reset_done.html',
         extra_context={'login_url': reverse_lazy('admin_login')}
     ),
     name='admin_password_reset_done'),

path('admin_password_reset_confirm/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(
         template_name='admin_password_reset_confirm.html',
         success_url=reverse_lazy('admin_password_reset_complete')  # <-- Add this!
     ),
     name='admin_password_reset_confirm'),

path('admin_password_reset_complete/',
     auth_views.PasswordResetCompleteView.as_view(
         template_name='admin_password_reset_complete.html',
         extra_context={'login_url': reverse_lazy('admin_login')}
     ),
     name='admin_password_reset_complete'),

path("filter-leave-requests/", filter_leave_requests, name="filter_leave_requests"),

path('generate-emp-id/', generate_emp_id, name='generate_emp_id'),
path('filter-holidays/<int:year>/', filter_holidays_by_year, name='filter_holidays_by_year'),
path('delete-file/', delete_file, name='delete_file'),
path('employees/upload/', EmployeeExcelCreateView.as_view(), name='employee_excel_create'),
path('holiday/upload/',HolidayExcelCreateView.as_view(),name='holiday_excel_create'),
path('employee_leaves',list_emp_leave_details,name="employee_leaves"),
path('export-employees-leaves/',export_employees_leaves, name='export_employees_leaves'),
path('employee-bank/',employeeBankDetails,name='employee-bank'),
path('export-emp-bank/',export_employee_bank_details,name='export_employee_bank_details'),
path('setup/', setup_list_create_view, name='setup_list'),
path('setup/edit/<int:pk>/', setup_edit_view, name='setup_edit'),
path('setup/delete/<int:pk>/', setup_delete_view, name='setup_delete'),

path('clients/', ts_views.client_list, name='client_list'),
path('clients/add/', ts_views.client_create, name='client_create'),
path('clients/<int:pk>/edit/', ts_views.client_update, name='client_update'),
path('clients/<int:pk>/delete/', ts_views.client_delete, name='client_delete'),
path('projects/', ts_views.project_list, name='project_list'),
path('projects/add/', ts_views.project_create, name='project_create'),
path('projects/edit/<int:pk>/', ts_views.project_update, name='project_update'),
path('projects/delete/<int:pk>/', ts_views.project_delete_view, name='project_delete'),
path('assignments/',ts_views.AssignProjectListView.as_view(),name='assign-project-list'), # Create a new assignment
path('assignments/create/',ts_views.AssignProjectCreateView.as_view(),name='assignproject_create'),
path('ajax/client-search/', ts_views.client_search, name='client_search'),
path('ajax/load-projects/', ts_views.load_projects, name='ajax_load_projects'),
path('ajax/get-projects/<int:client_id>/', ts_views.get_projects_for_client, name='ajax_get_projects'),
path('assignments/<int:pk>/update/', ts_views.AssignProjectUpdateView.as_view(), name='assign-project-update'),
path('assignments/<int:pk>/delete/', ts_views.AssignProjectDeleteView.as_view(), name='assign-project-delete'),
path('costcenters/', ts_views.CostCenterListView.as_view(), name='costcenter_list'),
path('costcenters/create/', ts_views.CostCenterCreateView.as_view(), name='costcenter_create'),
path('costcenters/<str:pk>/edit/', ts_views.CostCenterUpdateView.as_view(), name='costcenter_update'),

]




