from django.urls import path

from django.contrib.auth import views as auth_views
# from admin_app.views import load_states  # Ensure correct function import
from .views import *
urlpatterns=[
path('adminbase/',mainbase_view,name='adminbase'),
path('admin_index/',admin_index,name='admin_index'),
path('index/',index),
path('admin_logout/',admin_logout,name='admin_logout'),
path('add_employee/',add_employee,name='add_employee'),
path('add_holidays/', add_holidays, name='add_holidays'),
path('export-employees/', export_employees_to_excel, name='export_employees'),
path('get-states/', get_states, name='get_states'),
path('list_employees/',list_employees,name='employee_list'),
# path('employee_update/<pk>', EmployeeUpdateView.as_view(), name='employee_update'),
path('employee_delete/<pk>',EmployeeDeleteView.as_view(),name='employee_delete'),
path('restore_employee/<int:pk>/', restore_employee, name='restore_employee'),
path('deleted_employees/', DeletedEmployeeListView.as_view(), name='deleted_employees'),
path('leaverequestdisplay/',admin_leave_requests,name='leave_request_display'),
path('accept_leave_request/<int:leave_request_id>/', accept_leave_request, name='accept_leave_request'),
path('reject_leave_request/<int:leave_request_id>/', reject_leave_request, name='reject_leave_request'),
path('delete-leave/<int:leave_id>/', delete_leave_request, name='delete_leave_request'),
# path('employee/update/<int:pk>/', EmployeeUpdateView.as_view(), name='employee_update'),
path('employee/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee_edit'),
path('ajax/load-states/', load_states, name='load_states'),  # This is for AJAX dynamic state loading


#     path('register/', register_admin, name='register_admin'),  # URL for admin registration
#     path('login/', login_admin, name='login_admin'),  # URL for admin login
#     path('dashboard/', admin_dashboard, name='admin_dashboard'),  # Admin dashboard URL
# path('logout/', logout_admin, name='logout_admin'),

path('admin_login/', admin_login, name='admin_login'),

# Admin Dashboard (After successful login)
path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
# path('create_admin/', create_admin_user, name='create_admin_user'),  # Add this line
path('change_password/', change_password, name='admin_change_password'),
# Forgot Password - Enter Email


path('admin_password_reset/', auth_views.PasswordResetView.as_view(
    template_name='admin_password_reset.html',
    email_template_name='admin_password_reset_email.txt',       # plain text version
    html_email_template_name='admin_password_reset_email.html', # HTML version
    subject_template_name='admin_password_reset_subject.txt',
), name='admin_password_reset'),
# Password Reset Email Sent Confirmation
path('admin_password_reset_done/',
         auth_views.PasswordResetDoneView.as_view(template_name='admin_password_reset_done.html'),
         name='admin_password_reset_done'),
# Link Clicked - Enter New Password
path('admin_password_reset_confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='admin_password_reset_confirm.html'),
         name='admin_password_reset_confirm'),

# Password Successfully Changed
path('admin_password_reset_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='admin_password_reset_complete.html'),
         name='admin_password_reset_complete'),

# path("leave-requests/", admin_leave_requests, name="admin_leave_requests"),
path("filter-leave-requests/", filter_leave_requests, name="filter_leave_requests"),

path('generate-emp-id/', generate_emp_id, name='generate_emp_id'),
path('filter-holidays/<int:year>/', filter_holidays_by_year, name='filter_holidays_by_year'),
path('delete-file/', delete_file, name='delete_file'),
path('employees/upload/', EmployeeExcelCreateView.as_view(), name='employee_excel_create'),
]




