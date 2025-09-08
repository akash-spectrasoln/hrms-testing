
from django.urls import path
from .views import *
from timesheet_app import views as ts_views
from django.contrib.auth import views as auth_views
urlpatterns = [
path('login/', employee_login, name='login'),
path('set_password/', set_password, name='set_password'),
path('emp_dashboard/',dashboard_view, name='emp_dashboard'),
path('emp_index/',emp_index,name='index'),
path('emp_logout/',emp_logout,name='emp_logout'),
path('profile/<int:employee_id>/', employee_profile, name='profile'),
path('set-from-timesheet/<int:employee_id>/',set_from_timesheet, name='set_from_timesheet'),
path('request_leave/', request_leave, name='request_leave'),
path('my_leave_history/', my_leave_history, name='my_leave_history'),
path('update_employee_passwords/', update_employee_passwords, name='update_employee_passwords'),
path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset_form.html',                           # form for entering email
            email_template_name='employee_password_reset_email.txt',            # plain text email fallback
            html_email_template_name='password_reset_email.html',      # your beautiful HTML email
            subject_template_name='employee_password_reset_subject.txt',        # subject template
        ),
        name='password_reset'
    ),
path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
template_name='password_reset_done.html'
), name='password_reset_done'),
path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
template_name='password_reset_confirm.html'
), name='password_reset_confirm'),
path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
template_name='password_reset_complete.html'
), name='password_reset_complete'),
path('logout/', employee_logout, name='logout'),
path('change_password/', change_password, name='change_password'),
path('holiday_list/',holiday_list,name='holiday_list'),
path('manager/leave-requests/', manager_leave_requests, name='manager_leave_requests'),
path('manager/leave-requests/<int:leave_request_id>/', manage_leave_request, name='manage_leave_request'),
path('manager/subordinates/', view_subordinates, name='view_subordinates'),
path('filter-manager-leave-requests/', filter_manager_leave_requests, name='filter_manager_leave_requests'),
path('allocate-leave/<int:employee_id>/',allocate_leave, name='allocate_leave'),
path('check-floating-holidays/', check_floating_holidays, name='check_floating_holidays'),
path('check-leave-conflicts/', check_leave_conflicts, name='check_leave_conflicts'),
path('delete-leave/<int:leave_id>/', delete_leave, name='delete_leave'),

path('tsheet_index/',ts_views.tsheet_index,name='tsheet_index'),
path('timesheet/', ts_views.timesheet_calendar, name='timesheet_calendar'),
path('submit-timesheet/', ts_views.submit_timesheet, name='submit_timesheet'),
path('ajax/get-timesheet-day-data/', ts_views.get_timesheet_day_data, name='get_timesheet_day_data'),
path('ajax/delete-timesheet-entry/<int:entry_id>/', ts_views.delete_timesheet_entry,name='delete_timesheet_entry'),
path('copy-entries/', ts_views.copy_timesheet_entries, name='copy_timesheet_entries'),
path('timesheet-approvals/', ts_views.timesheet_approval_list, name='timesheet_approval_list'),
path('timesheet/unapprove/<int:tsheet_id>/', ts_views.timesheet_unapprove, name='timesheet_unapprove'),
path('timesheets/approve/', ts_views.approve_timesheet, name='approve_timesheet'),
path('timesheets/approve-selected/', ts_views.approve_selected_timesheets, name='approve_selected_timesheets'),
path("timesheet-week-details/", ts_views.timesheet_week_details, name="timesheet_week_details"),
path('nextyearcount/',get_next_year_leave_counts, name= 'get_next_year_leave_counts'),
path('leave-reports/',leave_report,name="leave-report"),
]



