
from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
path('login/', employee_login, name='login'),
path('set_password/', set_password, name='set_password'),
path('emp_index/',emp_index,name='index'),

path('request_leave/', request_leave, name='request_leave'),
path('my_leave_history/', my_leave_history, name='my_leave_history'),
path('profile/',employee_dashboard, name='profile'),
# path('get_states/', get_states, name='get_states'),
path('update_employee_passwords/', update_employee_passwords, name='update_employee_passwords'),
path('edit_employee/',edit_employee_profile,name='edit_employee'),
# path('delete_employee/',delete_employee_profile,name='delete_employee')
path('password_reset/', auth_views.PasswordResetView.as_view(
template_name='password_reset_form.html'
), name='password_reset'),
path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
template_name='admin_password_reset_done.html'
), name='password_reset_done'),
path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
template_name='admin_password_reset_confirm.html'
), name='password_reset_confirm'),
path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
template_name='admin_password_reset_complete.html'
), name='password_reset_complete'),
path('logout/', employee_logout, name='logout'),
path('change_password/', change_password, name='change_password'),
path('total_leaves/', total_leaves_view, name='total_leaves'),
path('holiday_list/',holiday_list,name='holiday_list'),
path('manager/leave-requests/', manager_leave_requests, name='manager_leave_requests'),
path('manager/leave-requests/<int:leave_request_id>/', manage_leave_request, name='manage_leave_request'),
# path('leave_summary/', employee_leave_summary, name='employee_leave_summary'),
# path('test/',test,name='test'),
path('calendar/',calendar_view),
path('manager/subordinates/', view_subordinates, name='view_subordinates'),
path('allocate-leave/<int:employee_id>/', allocate_leave, name='allocate_leave'),

path('filter-manager-leave-requests/', filter_manager_leave_requests, name='filter_manager_leave_requests'),
path('navbar/',navbar,name='navbar'),
path('leftbar/',sidebar,name='leftbar'),
path('base/',base,name='base')

]