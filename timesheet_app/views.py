from django.shortcuts import render, get_object_or_404, redirect
from admin_app.models import Client, Project,AssignProject,Employees,Country,CostCenter,TimesheetHdr,TimesheetItem,LeaveRequest,Holiday,StateHoliday
from .forms import ClientForm, ProjectForm,AssignProjectCreateForm,AssignProjectUpdateForm,CostCenterForm
from django import forms
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib import messages
from datetime import datetime, timedelta
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from admin_app.models import Holiday, StateHoliday, LeaveRequest, Activity, WrkLocation
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.db.models import Sum, Case, When, IntegerField
from django.utils import timezone
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from django.utils.timezone import now
from django.views.generic import ListView,UpdateView,CreateView
from django.utils.decorators import method_decorator
from functools import wraps

# 🔹 Use the employee app decorator
def employee_signin_required(view_func):
    from employee_app import views as employee_views   # local import avoids circular import
    return employee_views.signin_required(view_func)

def admin_signin_required(view_func):
    from admin_app import views as admin_views
    return admin_views.signin_required(view_func)

# index view to seperate timesheet app 
def tsheet_index(request):
    try:
        employee = Employees.objects.get(company_email=request.user.username)
    except Employees.DoesNotExist:
        return render(request, 'error.html', {'message': 'Employee not found.'})

    # Check if the employee is a manager (has subordinates)
    if employee.employees_managed.exists():  # If there are employees managed by this employee
        is_manager = True
    else:
        is_manager = False

    return render(request, 'timesheet/tsheet_index.html', {
        'employee': employee,
        'is_manager': is_manager , # Pass whether the employee is a manager or not
        'emp_designation': employee.role.role_name,  # Employee designation
        'emp_id': employee.employee_id,  # Employee ID
        'emp_fname' : employee.first_name, #employee firstname
        'emp_lname' : employee.last_name, #employee lastname
    })
# --- ADMIN APP FEATURED VIEWS ---



@admin_signin_required
def client_list(request):
    """List all clients with search, filter, sorting, and status."""
    search = request.GET.get('search', '').strip()
    alias = request.GET.get('alias', '')
    country = request.GET.get('country', '')
    status = request.GET.get('status', 'active')  # Default active
    sort = request.GET.get('sort', 'client_name')

    allowed_sorts = [
        'client_name', '-client_name',
        'client_alias', '-client_alias',
        'client_addr', '-client_addr',
        'country__country_name', '-country__country_name'
    ]
    sort = sort if sort in allowed_sorts else 'client_name'

    # Base queryset
    clients = Client.objects.select_related('country').all()

    # Status filter
    if status == 'active':
        clients = clients.filter(is_active=True)
    elif status == 'inactive':
        clients = clients.filter(is_active=False)
    # else '' → show all

    # Other filters
    if search:
        clients = clients.filter(
            Q(client_name__icontains=search) |
            Q(client_alias__icontains=search) |
            Q(client_addr__icontains=search)
        )
    if alias:
        clients = clients.filter(client_alias=alias)
    if country:
        clients = clients.filter(country_id=country)

    # Sorting
    clients = clients.order_by(sort)

    context = {
        'clients': clients,
        'search_query': search,
        'alias_filter': alias,
        'country_filter': country,
        'status_filter': status,  # Pass to template
        'sort_field': sort,
        'sort_options': [
            ('client_name', 'Name (A-Z)'),
            ('-client_name', 'Name (Z-A)'),
            ('client_alias', 'Abbreviation (A-Z)'),
            ('-client_alias', 'Abbreviation (Z-A)'),
            ('country__country_name', 'Country (A-Z)'),
            ('-country__country_name', 'Country (Z-A)'),
        ],
        'abbreviations': Client.objects.values_list('client_alias', flat=True).distinct(),
        'countries': Country.objects.all(),
        "querystring": request.GET.urlencode(),  # 🔑 preserve filters
    }

    return render(request, 'timesheet/client_list.html', context)


@admin_signin_required
def client_create(request):
    query_params = request.GET.copy()
    next_url = query_params.get('next', reverse('client_list'))

    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)

        if hasattr(request.user, "employee_profile"):
            client.created_by = request.user.employee_profile

        client.save()
        return redirect(next_url)  #  go back with filters

    return render(request, 'timesheet/client_form.html', {
        'form': form,
        'next': next_url,
    })
@admin_signin_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)

    query_params = request.GET.copy()
    next_url = query_params.get("next") or reverse("client_list")

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            if hasattr(request.user, "employee_profile"):
                client.updated_by = request.user.employee_profile
            if 'is_active' in form.cleaned_data:
                client.is_active = form.cleaned_data['is_active']
            client.save()
            messages.success(request, "Client updated successfully!")
            return redirect(next_url)
    else:
        form = ClientForm(instance=client)

    return render(request, 'timesheet/client_form.html', {
        'form': form,
        'next': next_url,
    })
@admin_signin_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)

    query_params = request.GET.copy()
    next_url = query_params.get("next") or reverse("client_list")

    if request.method == 'POST':
        client.is_active = False
        client.save(update_fields=['is_active'])
        return redirect(next_url)  # 🔑 preserve filters

    return render(request, 'timesheet/client_confirm_delete.html', {
        'client': client,
        'next': next_url,
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_GET



@admin_signin_required
def project_list(request):
    """
    List and filter projects with:
      - Status filter (current / expired / future / all)
      - Search by project or client name
      - Client filter
      - Sorting

    Notes:
      - Template uses `is_active` for Active column
      - Status filter is implemented with DB queries for efficiency
    """

    today = now().date()
    projects = Project.objects.select_related('client')

    # ------------------------------
    # Status filter (default = current)
    # ------------------------------
    status_filter = request.GET.get('status', 'current').strip().lower()

    if status_filter == 'current':
        projects = projects.filter(valid_from__lte=today, valid_to__gte=today)
    elif status_filter == 'expired':
        projects = projects.filter(Q(valid_to__lt=today) | Q(is_deleted=True))

    elif status_filter == 'future':
        projects = projects.filter(valid_from__gt=today)
    elif status_filter == 'all':
        pass  # no filter
    else:
        status_filter = 'current'
        projects = projects.filter(valid_from__lte=today, valid_to__gte=today)

    # ------------------------------
    # Search filter
    # ------------------------------
    search_query = request.GET.get('search', '').strip()
    if search_query:
        projects = projects.filter(
            Q(project_name__icontains=search_query) |
            Q(client__client_name__icontains=search_query)
        )

    # ------------------------------
    # Client filter
    # ------------------------------
    client_filter = request.GET.get('client', '').strip()
    if client_filter.isdigit():
        projects = projects.filter(client_id=int(client_filter))

    # ------------------------------
    # Sorting
    # ------------------------------
    sort_field = request.GET.get('sort', '-valid_from')
    allowed_sorts = [
        'project_name', '-project_name',
        'client__client_name', '-client__client_name',
        'valid_from', '-valid_from',
        'valid_to', '-valid_to',
    ]
    if sort_field not in allowed_sorts:
        sort_field = '-valid_from'
    projects = projects.order_by(sort_field)

    # ------------------------------
    # Dropdown options
    # ------------------------------
    all_clients = Client.objects.only('client_id', 'client_name').order_by('client_name')
    sort_options = [
        ('project_name', 'Project (A-Z)'),
        ('-project_name', 'Project (Z-A)'),
        ('client__client_name', 'Client (A-Z)'),
        ('-client__client_name', 'Client (Z-A)'),
        ('valid_from', 'Valid From (Oldest)'),
        ('-valid_from', 'Valid From (Newest)'),
        ('valid_to', 'Valid To (Oldest)'),
        ('-valid_to', 'Valid To (Newest)'),
    ]
    status_options = [
        ('current', 'Current'),
        ('expired', 'Expired'),
        ('future', 'Future'),
        ('all', 'All'),
    ]

    # ------------------------------
    # Context for template
    # ------------------------------
    context = {
        'projects': projects,
        'search_query': search_query,
        'client_filter': client_filter,
        'sort_field': request.GET.get('sort', '-valid_from'),
        'all_clients': all_clients,
        'sort_options': sort_options,
        'status': status_filter,
        'status_options': status_options,
    }

    return render(request, 'timesheet/project_list.html', context)
@admin_signin_required
def project_create(request):
    form = ProjectForm(request.POST or None)

    # Get the 'next' URL, or default to the base list view
    next_url = request.GET.get('next', reverse('project_list'))

    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)

        if hasattr(request.user, "employee_profile"):
            project.created_by = request.user.employee_profile

        project.save()
        
        # Redirect to the 'next' URL, preserving filters
        return redirect(next_url)

    # Pass the 'next' URL to the template for the cancel/back button
    context = {
        'form': form,
        'next': next_url,
    }
    return render(request, 'timesheet/project_form.html', context)

from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse

from urllib.parse import urlencode
@admin_signin_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Get the 'next' URL, or default to the base list view
    next_url = request.GET.get('next', reverse('project_list'))
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            if hasattr(request.user, "employee_profile"):
                project.updated_by = request.user.employee_profile
            project.save()
            # Redirect to the 'next' URL, preserving filters
            return redirect(next_url)
    else:
        form = ProjectForm(instance=project)

    # Pass the 'next' URL to the template for the cancel/back button
    context = {
        'form': form,
        'project': project,
        'next': next_url,
    }
    return render(request, 'timesheet/project_form.html', context)

@admin_signin_required
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Get the 'next' URL, or default to the base list view
    next_url = request.GET.get('next', reverse('project_list'))

    if request.method == 'POST':
        project.soft_delete()
        messages.success(request, "Project deactivated (soft-deleted) successfully!")
        
        # Redirect to the 'next' URL, preserving filters
        return redirect(next_url)

    # Pass the 'next' URL and project to the template
    context = {
        'project': project,
        'next': next_url,
    }
    return render(request, 'timesheet/project_confirm_delete.html', context)


@require_GET
def client_search(request):
    """
    Autocomplete client names (AJAX).
    """
    term = request.GET.get('term', '').strip()
    clients = (
        Client.objects.filter(client_name__icontains=term)
        if term else Client.objects.all()[:50]
    )

    results = [{'id': c.client_id, 'text': c.client_name} for c in clients]
    return JsonResponse({'results': results})


def employee_search(request):
    term = request.GET.get("term", "")
    
    # Only show employed employees with active users
    qs = Employees.objects.filter(
        is_deleted=False,
        user__isnull=False,            # ensure user relationship exists
        user__is_active=True,          # exclude inactive users
        employee_status='employed'     # only show employed employees
    ).select_related('user').order_by('employee_id','first_name','last_name')

    if term:
        qs = qs.filter(
            Q(employee_id__icontains=term) |
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term)
        ).order_by('employee_id','first_name','last_name')

    # Additional safety check - filter out any employees with inactive users
    active_employees = []
    for emp in qs:
        if emp.user and emp.user.is_active:
            active_employees.append(emp)

    results = [
        {"id": e.pk, "text": f"{e.employee_id} - {e.first_name} {e.last_name}"}
        for e in active_employees
    ]
    return JsonResponse({"results": results})

@require_GET
def get_projects_for_client(request, client_id):
    """
    Get active & valid projects for a client (used in form/project dropdowns).
    Includes previously assigned project if specified.
    """
    assigned_project_id = request.GET.get('assigned_project')
    from django.utils.timezone import now

    qs = Project.objects.filter(
        client_id=client_id,
        is_active=True
    ).filter(Q(valid_to__gte=now()) | Q(valid_to__isnull=True))

    if assigned_project_id:
        qs = qs | Project.objects.filter(pk=assigned_project_id)

    projects = qs.distinct().order_by('project_name').values(
        'project_id', 'project_name', 'valid_from', 'valid_to'
    )
    return JsonResponse({'projects': list(projects)})



# views.py
from django.views.generic import CreateView, UpdateView, ListView, View
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .forms import AssignProjectCreateForm, AssignProjectUpdateForm
import logging

logger = logging.getLogger(__name__)

class AssignProjectCreateView(CreateView):
    model = AssignProject
    form_class = AssignProjectCreateForm
    template_name = 'timesheet/assignproject_form.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('assign-project-list')

    def form_valid(self, form):
        assign_project = form.save(commit=False)
        if hasattr(self.request.user, "employee_profile"):
            assign_project.created_by = self.request.user.employee_profile
        assign_project.save()
        messages.success(self.request, "Project assigned successfully!")
        return super().form_valid(form)

from django.urls import reverse
from django.utils.http import urlencode

class AssignProjectUpdateView(UpdateView):
    model = AssignProject
    form_class = AssignProjectUpdateForm
    template_name = 'timesheet/assignproject_form.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('assign-project-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the 'next' URL directly to the template
        context['next'] = self.request.GET.get('next', reverse('assign-project-list'))
        return context

    def form_valid(self, form):
        assign_project = form.save(commit=False)
        if hasattr(self.request.user, "employee_profile"):
            assign_project.updated_by = self.request.user.employee_profile
        assign_project.save()
        messages.success(self.request, "Assignment updated successfully!")
        return super().form_valid(form)
    
def load_projects(request):
    """
    AJAX view to load project list for a given client
    """
    client_id = request.GET.get('client_id')
    if not client_id or not client_id.isdigit():
        return JsonResponse({'projects': []})

    projects = Project.objects.filter(
        client_id=client_id, is_active=True
    ).values('project_id', 'project_name', 'valid_from', 'valid_to').order_by('project_name')

    return JsonResponse({'projects': [
        {
            'project_id': p['project_id'],
            'project_name': p['project_name'],
            'valid_from': str(p['valid_from']),
            'valid_to': str(p['valid_to']),
        } for p in projects
    ]})




class AssignProjectListView(ListView):
    model = AssignProject
    template_name = 'timesheet/assignproject_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        today = now().date()

        qs = super().get_queryset().select_related(
            'employee', 'project', 'project__client'
        )

        # ------------------------------
        # Status filter (default = current)
        # ------------------------------
        status_filter = self.request.GET.get('status', 'current').strip().lower()

        if status_filter == 'current':
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
        elif status_filter == 'expired':
    # Include assignments that are either expired OR deleted
            qs = qs.filter(Q(end_date__lt=today) | Q(is_deleted=True))

        elif status_filter == 'future':
            qs = qs.filter(start_date__gt=today)
        elif status_filter == 'all':
            pass  # no filter
        else:
            # fallback to current
            status_filter = 'current'
            qs = qs.filter(start_date__lte=today, end_date__gte=today)

        # ------------------------------
        # Existing filters
        # ------------------------------
        search = self.request.GET.get('search', '').strip()
        client_filter = self.request.GET.get('client', '').strip()
        project_filter = self.request.GET.get('project', '').strip()

        if search:
            qs = qs.filter(
                Q(employee__employee_id__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(project__project_name__icontains=search) |
                Q(project__client__client_name__icontains=search)
            )

        if client_filter.isdigit():
            qs = qs.filter(project__client_id=client_filter)

        if project_filter.isdigit():
            qs = qs.filter(project_id=project_filter)

        return qs.order_by('employee_id','-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', '').strip(),
            'client_filter': self.request.GET.get('client', '').strip(),
            'project_filter': self.request.GET.get('project', '').strip(),
            'status': self.request.GET.get('status', 'current').strip().lower(),
            'all_clients': Client.objects.only('client_id', 'client_name').order_by('client_name'),
            'all_projects': Project.objects.select_related('client').only('project_id', 'project_name', 'client__client_alias') .order_by('client__client_alias', 'project_name'),
            'status_options': [
                ('current', 'Current'),
                ('expired', 'Expired'),
                ('future', 'Future'),
                ('all', 'All'),
            ],
        })
        return context



class AssignProjectDeleteView(View):
    def get(self, request, pk):
        assignment = get_object_or_404(AssignProject, pk=pk)
        next_url = request.GET.get('next', reverse('assign-project-list'))
        context = {
            'assignment': assignment,
            'next': next_url,
        }
        return render(request, 'timesheet/assignproject_confirm_delete.html', context)

    def post(self, request, pk):
        assignment = get_object_or_404(AssignProject, pk=pk)
        next_url = request.GET.get('next', reverse('assign-project-list'))
        assignment.is_deleted = True
        assignment.save()
        messages.success(request, "Assignment removed successfully.")
        return redirect(next_url)

class CostCenterListView(ListView):
    model = CostCenter
    template_name = 'timesheet/costcenter_list.html'
    context_object_name = 'costcenters'
    paginate_by = 20  # Optional: add pagination for large lists

    def get_queryset(self):
        query = self.request.GET.get('search', '').strip()
        is_active_filter = self.request.GET.get('is_active', '').strip().lower()

        qs = CostCenter.objects.all()  # start with all

        if not is_active_filter or is_active_filter == 'active':
            # Default or "active" filter → show only active
            qs = qs.filter(is_active=True)
        elif is_active_filter == 'inactive':
            qs = qs.filter(is_active=False)
        elif is_active_filter == 'all':
            pass  # no filter → show all

        # Apply search filter
        if query:
            qs = qs.filter(costcenter_name__icontains=query)

        return qs.order_by('costcenter_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', '').strip(),
            'is_active_filter': self.request.GET.get('is_active', '').strip().lower(),
            'status_options': [
                ('', 'Active (default)'),  # default shows active
                ('active', 'Active'),
                ('inactive', 'Inactive'),
                ('all', 'All'),
            ]
        })
        return context



from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect

class CostCenterCreateView(CreateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'timesheet/costcenter_form.html'

    def get_success_url(self):
        # Use the 'next' URL parameter if it exists; otherwise, use the default list URL.
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('costcenter_list')

    def form_valid(self, form):
        # Optional: Add created_by or other logic here
        return super().form_valid(form)
#Employee App Features 
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect

class CostCenterUpdateView(UpdateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'timesheet/costcenter_form.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('costcenter_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the full path to the template to be used by the "Back" button.
        context['next'] = self.request.GET.get('next')
        return context

    def form_valid(self, form):
        # Optional: Add updated_by or other logic here
        return super().form_valid(form)



import calendar




def adjust_month_year(month, year, delta):
    month += delta
    if month < 1:
        return 12, year - 1
    elif month > 12:
        return 1, year + 1
    return month, year


# ---------------- 1️⃣ Config ----------------


import calendar
from datetime import date, timedelta
from django.db.models import Sum, Case, When, IntegerField
@employee_signin_required
def timesheet_calendar(request):
    """
    Renders the timesheet calendar with dynamic navigation and data.
    """
    employee = request.user.employee_profile
    is_manager = Employees.objects.filter(manager=employee).exists()
    today = timezone.localdate()

    # 1️⃣ Determine the earliest valid date for the employee
    joining_date = employee.enc_valid_from
    new_start_date_of_calendar = date(2025, 9, 1)
    effective_start_date = max(joining_date, new_start_date_of_calendar)

    # 2️⃣ Month & Year selection
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        month, year = today.month, today.year

    month = max(1, min(12, month))
    year = max(2000, min(2100, year))

    # 3️⃣ Apply Navigation Limits
    current_date_obj = date(year, month, 1)
    if current_date_obj < date(effective_start_date.year, effective_start_date.month, 1):
        month, year = effective_start_date.month, effective_start_date.year
        current_date_obj = date(year, month, 1)

    # 6️⃣ Build the calendar grid (we do this early so we know the full date range)
    cal = calendar.Calendar(firstweekday=6)  # Sunday first
    month_days = cal.monthdatescalendar(year, month)  # list of weeks -> list of dates
    # grid_start is first cell (usually from prev month), grid_end is last
    grid_start = month_days[0][0]
    grid_end = month_days[-1][-1]

    # 4️⃣ Timesheet items — fetch for the full grid range (so adjacent-month days have data)
    timesheet_qs = TimesheetItem.objects.filter(
        hdr__employee=employee,
        wrk_date__gte=grid_start,
        wrk_date__lte=grid_end
    ).values('wrk_date').annotate(
        total_hours=Sum('wrk_hours'),
        approved_count=Sum(
            Case(When(hdr__is_approved=True, then=1), default=0, output_field=IntegerField())
        )
    )

    # Map date -> totals
    timesheet_hours = {entry['wrk_date']: entry['total_hours'] for entry in timesheet_qs}
    timesheet_dates = set(timesheet_hours.keys())
    approved_dates = {entry['wrk_date'] for entry in timesheet_qs if entry['approved_count'] > 0}

    # 5️⃣ Holidays & leave — also across the grid range
    holidays_qs = Holiday.objects.filter(
        country=employee.country,
        date__gte=grid_start,
        date__lte=grid_end
    ).only('date', 'name')
    state_holidays_qs = StateHoliday.objects.filter(
        country=employee.country,
        state=employee.state,
        date__gte=grid_start,
        date__lte=grid_end
    ).only('date', 'name')

    all_holidays = {h.date: h.name for h in holidays_qs}
    all_holidays.update({sh.date: sh.name for sh in state_holidays_qs})

    # Leave dates — include leaves that overlap the grid range
    leave_dates = set()
    leave_qs = LeaveRequest.objects.filter(
        employee_master=employee,
        status='Approved',
        start_date__lte=grid_end,
        end_date__gte=grid_start
    ).values_list('start_date', 'end_date')
    

    for start, end in leave_qs:
        s = max(start, grid_start)
        e = min(end, grid_end)
        for i in range((e - s).days + 1):
            day = s + timedelta(days=i)
            if day.weekday() < 5 and day not in all_holidays:
                leave_dates.add(day)



    # 6️⃣ Build calendar_data — include outside-month days, add is_current_month flag
    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            # flags
            is_current_month = (day.month == month)
            is_weekend = day.weekday() >= 5  # Sat=5, Sun=6 (but with firstweekday=6 Sun is 6)
            is_holiday = day in all_holidays
            holiday_name = all_holidays.get(day, '')
            on_leave = day in leave_dates
            is_entered = day in timesheet_dates
            is_future = day > today
            is_approved = day in approved_dates
            is_before_joining_date = day < effective_start_date

            # Disabled logic (same as your previous rule)
            is_disabled = any([ on_leave, is_future, is_before_joining_date])
            # NOTE: we DO NOT automatically disable outside-month days here. Let frontend decide.
            # if you want to disable outside-month cells too, uncomment:
            # if not is_current_month:
            #     is_disabled = True

            # Status priority
            if on_leave:
                status = "status-leave"
            elif is_holiday and is_entered:
                status = "status-holiday-entered"
            elif is_weekend and is_entered:
                status = "status-weekend-entered"
            elif is_holiday:
                status = "status-holiday"
            elif is_weekend:
                status = "status-weekend"
            elif is_entered:
                status = "status-entered"
            else:
                status = "status-not-entered"


            hours = timesheet_hours.get(day, 0) if is_entered else None

            week_data.append({
                'date': day,
                'day': day.day,
                'is_today': day == today,
                'is_entered': is_entered,
                'is_approved': is_approved,
                'is_disabled': is_disabled,
                'status': status,
                'total_hours': hours,
                'holiday_name': holiday_name,
                'on_leave': on_leave,
                'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'is_current_month': is_current_month,
                'is_outside_month': not is_current_month,  # convenience flag
            })
        calendar_data.append(week_data)

    # 7️⃣ Navigation (same as you had)
    prev_month, prev_year = adjust_month_year(month, year, -1)
    next_month, next_year = adjust_month_year(month, year, 1)

    prev_date_obj = date(prev_year, prev_month, 1) if prev_month else None
    if prev_date_obj and prev_date_obj < date(effective_start_date.year, effective_start_date.month, 1):
        prev_month, prev_year = None, None

    # 8️⃣ Context — include grid range and also a timesheet list for grid (useful for popup)
    context = {
        'year': year,
        'month': month,
        'current_month_name': calendar.month_name[month],
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'calendar_data': calendar_data,
        'today': today,
        'activities': Activity.objects.only('act_id', 'act_name'),
        'work_locations': WrkLocation.objects.only('loc_id', 'loc_name'),
        'employee': employee,
        # monthly list preserved (for other places that depend on it)
        'timesheet_entries': TimesheetItem.objects.filter(
            hdr__employee=employee,
            wrk_date__year=year,
            wrk_date__month=month
        ).order_by('-wrk_date'),
        # full-grid timesheet items (for legend popup / quick lookup)
        'timesheet_entries_grid': TimesheetItem.objects.filter(
            hdr__employee=employee,
            wrk_date__gte=grid_start,
            wrk_date__lte=grid_end
        ).order_by('-wrk_date'),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'prev_month_name': calendar.month_name[prev_month] if prev_month else '',
        'next_month_name': calendar.month_name[next_month] if next_month else '',
        'prev_year_only': prev_year,
        'next_year_only': next_year,
        'current_year': today.year,
        'is_manager': is_manager,
        'joining_date': joining_date,
        'grid_start': grid_start,
        'grid_end': grid_end,
    }

    # 9️⃣ AJAX support
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'timesheet/calendar_grid.html', context)

    return render(request, 'timesheet/calendar.html', context)

@employee_signin_required
def submit_timesheet(request):
    """
    Create or update a TimesheetHdr (weekly) and TimesheetItem (daily)
    with project or cost center validation, activity, work location,
    and hours entry. Ensures daily total ≤ 12 hours and unique entry
    per project/cost center per day.
    """
    if request.method != 'POST':
        return _error_response(request, "Invalid request method.", 400)

    employee = request.user.employee_profile
    date_str = request.POST.get('date')

    # 1️⃣ Parse date safely
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return _error_response(request, "Invalid date format.", 400)

    # Week start (Sunday) & end (Saturday) for header
    week_start = date_obj - timedelta(days=(date_obj.weekday() + 1) % 7)
    week_end = week_start + timedelta(days=6)

    # 2️⃣ Determine project OR cost center
    project_value = request.POST.get('project', '').strip()
    project_assignment = None
    cost_center = None

    if project_value:
        if project_value.upper().startswith("COSTCENTER-"):
            cost_center = employee.cost_center
            if not cost_center:
                return _error_response(request, "No cost center assigned to you.", 400)
        else:
            try:
                assign_project_id = int(project_value)
            except ValueError:
                return _error_response(request, "Invalid project selection.", 400)

            project_assignment = AssignProject.objects.filter(
                employee=employee,
                pk=assign_project_id,
                start_date__lte=date_obj
            ).filter(
                Q(end_date__gte=date_obj) | Q(end_date__isnull=True)
            ).first()

            if not project_assignment:
                return _error_response(request, "No valid project assignment for this date.", 400)
            cost_center = None
    else:
        cost_center = employee.cost_center
        if not cost_center:
            return _error_response(request, "You do not have a cost center assigned.", 400)

    # 3️⃣ Fetch activity & work location
    activity = get_object_or_404(Activity, pk=request.POST.get('activity'))
    work_location = get_object_or_404(WrkLocation, pk=request.POST.get('work_location'))

    # 4️⃣ Hours worked
    hours_str = request.POST.get('hours_worked')
    try:
        hours_worked = int(hours_str) if hours_str else 0
    except ValueError:
        return _error_response(request, "Invalid hours value.", 400)

    # 5️⃣ Get or create TimesheetHdr for the week
    hdr, _ = TimesheetHdr.objects.get_or_create(
        employee=employee,
        week_start=week_start,
        week_end=week_end
    )
    
    # 6️⃣ Detect edit mode by entry ID
    entry_id = request.POST.get('entry_id')
    existing_entry = None
    if entry_id:
        try:
            existing_entry = TimesheetItem.objects.get(pk=entry_id, hdr__employee=employee)
        except TimesheetItem.DoesNotExist:
            return _error_response(request, "Entry not found.", 404)

    # 7️⃣ Calculate other entries' total (exclude current if editing)
    existing_items = TimesheetItem.objects.filter(hdr=hdr, wrk_date=date_obj)
    current_entry_hours = existing_entry.wrk_hours if existing_entry else 0
    other_total = sum(item.wrk_hours for item in existing_items) - current_entry_hours
    new_total = other_total + hours_worked

    if new_total > 12:
        return _error_response(
            request,
            f"Total hours for {date_obj} exceed 12",
            400
        )

    # 8️⃣ Check for duplicates based on project or cost center
    duplicate_qs = TimesheetItem.objects.filter(hdr=hdr, wrk_date=date_obj)

    if project_assignment:
        # Filter entries that have this project assignment
        duplicate_qs = duplicate_qs.filter(project_assignment=project_assignment)
    else:
        # Filter entries that have this cost center
        duplicate_qs = duplicate_qs.filter(costcenter=cost_center, project_assignment__isnull=True)

    if existing_entry:
        duplicate_qs = duplicate_qs.exclude(pk=existing_entry.pk)

    if duplicate_qs.exists():
        msg = f"A timesheet for this {'project' if project_assignment else 'cost center'} already exists on {date_obj}. Please edit the existing entry."
        return _error_response(request, msg, 400)


    # 9️⃣ Save or update entry
    if existing_entry:
        item = existing_entry
        item.project_assignment = project_assignment
        item.costcenter = cost_center
        item.activity = activity
        item.work_location = work_location
        item.wrk_hours = hours_worked
        item.description = request.POST.get('description', '').strip()
        item.save()
        created = False
    else:
        item = TimesheetItem.objects.create(
            hdr=hdr,
            wrk_date=date_obj,
            project_assignment=project_assignment,
            costcenter=cost_center,
            activity=activity,
            work_location=work_location,
            wrk_hours=hours_worked,
            description=request.POST.get('description', '').strip()
        )
        created = True

    # 🔟 Recalculate totals and delayed status
    hdr.recalc_totals()
    hdr.check_delayed_status()
    hdr.save()

    # 1️⃣1️⃣ Prepare success response
    response_data = {
        'status': 'success',
        'message': f"Timesheet for {date_obj} {'submitted' if created else 'updated'} successfully.",
        'date': date_obj.strftime('%Y-%m-%d'),
        'entry': {
            'id': item.pk,
            'date': item.wrk_date.strftime('%Y-%m-%d'),
            'hours_worked': item.wrk_hours,
            'projectAssignmentId': item.project_assignment.pk if item.project_assignment else None,
            'project_name': str(item.project_assignment.project) if item.project_assignment else (str(item.costcenter) if item.costcenter else None),
            'activity': item.activity.act_name if item.activity else None,
            'work_location': item.work_location.loc_name if item.work_location else None,
            'is_approved': hdr.is_approved,
            'is_cost_center': cost_center is not None,
        }
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response_data)

    messages.success(request, response_data['message'])
    return redirect('timesheet_calendar')

def _error_response(request, msg, status=400):

    if request.headers.get('x-silent-refresh') == '1':
        return JsonResponse({'status': 'silent_error', 'message': msg}, status=status)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': msg}, status=status)
    messages.error(request, msg)
    return redirect('timesheet_calendar')


from datetime import date, timedelta

def calculate_remaining_working_days(employee, start_date, end_date):
    """
    Calculate remaining working days between start_date and end_date for an employee.
    Excludes weekends, holidays, state holidays, and approved leaves.
    """
    if not end_date or start_date > end_date:
        return 0

    # Fetch holidays
    holidays = set(Holiday.objects.filter(
        country=employee.country,
        date__range=(start_date, end_date)
    ).values_list('date', flat=True))

    state_holidays = set(StateHoliday.objects.filter(
        country=employee.country,
        state=employee.state,
        date__range=(start_date, end_date)
    ).values_list('date', flat=True))

    # Fetch leave days
    leave_days = {
        leave.start_date + timedelta(days=i)
        for leave in LeaveRequest.objects.filter(
            employee_master=employee,
            status='Approved',
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        for i in range((leave.end_date - leave.start_date).days + 1)
    }

    # Count working days
    remaining = sum(
        1
        for cursor in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1))
        if cursor.weekday() < 5 and cursor not in holidays and cursor not in state_holidays and cursor not in leave_days
    )

    return remaining

from django.db.models import Q
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.core.serializers.json import DjangoJSONEncoder

# Assuming these models are defined elsewhere
# from .models import (
#     TimesheetItem, TimesheetHeader, LeaveRequest,
#     AssignProject, CostCenter, EmployeeProfile, EmployeeType
# )
# from .utils import calculate_remaining_working_days
# from django.contrib.auth.models import User

def get_timesheet_day_data(request):
    """
    Fetch and return all necessary data for a given day's timesheet entry screen:
      - Employee's timesheet entries for that day
      - Available projects and cost center options
      - Leave/holiday status for the day
      - Project end date and remaining working days
    """
    # 1. Fetch employee profile
    try:
        employee = request.user.employee_profile
    except Employees.DoesNotExist:
        return JsonResponse({"error": "Employee profile not found."}, status=404)

    # 2. Employee type code
    employee_type_code = employee.employee_type.code if employee.employee_type else None

    # 3. Parse date
    date_str = request.GET.get("date")
    date_obj = parse_date(date_str)
    if not date_obj:
        return JsonResponse({"error": "Invalid date"}, status=400)

    # 4. Check leave
    on_leave = (
            date_obj.weekday() < 5 and
            LeaveRequest.objects.filter(
                employee_master=employee,
                status="Approved",
                start_date__lte=date_obj,
                end_date__gte=date_obj
            ).exists()
        )

    # 5. Check holiday
    is_holiday = Holiday.objects.filter(
        country=employee.country,
        date=date_obj
    ).exists() or StateHoliday.objects.filter(
        country=employee.country,
        state=employee.state,
        date=date_obj
    ).exists()

    # 5.5. Check if it's a weekend (Saturday or Sunday)
    is_weekend = date_obj.weekday() >= 5 # 5 is Saturday, 6 is Sunday

    

    # 6. Timesheet entries
    items_qs = (
        TimesheetItem.objects
        .filter(hdr__employee=employee, wrk_date=date_obj)
        .select_related(
            "hdr",
            "project_assignment",
            "project_assignment__project",
            "project_assignment__project__client",
            "costcenter",
            "activity",
            "work_location"
        )
    )

    entry_list = []
    for item in items_qs:
        project_name = None
        project_id = None
        project_assignment_id = None
        is_costcenter = False

        if item.project_assignment:
            proj_obj = item.project_assignment.project
            client_alias = proj_obj.client.client_alias if proj_obj.client else "No Client"
            project_name = f"{client_alias} - {proj_obj.project_name}"
            project_id = proj_obj.project_id
            project_assignment_id = item.project_assignment.pk
        elif item.costcenter:
            costcenter = item.costcenter
            project_name = f"{costcenter.costcenter_id} - {costcenter.costcenter_name}"
            project_id = costcenter.costcenter_id
            project_assignment_id = f"COSTCENTER-{project_id}"
            is_costcenter = True

        entry_list.append({
            "tsheet_item_id": item.pk,
            "date": item.wrk_date,
            "projectAssignmentId": project_assignment_id,
            "project_id": project_id,
            "project_name": project_name,
            "activity_id": item.activity.act_id if item.activity else None,
            "activity_name": item.activity.act_name if item.activity else "",
            "work_location_id": item.work_location.loc_id if item.work_location else None,
            "work_location_name": item.work_location.loc_name if item.work_location else "",
            "hours_worked": item.wrk_hours,
            "description": item.description or "",
            "is_approved": item.hdr.is_approved,
            "is_costcenter": is_costcenter,
        })

    # 7. Fetch active project assignments
    project_assignments = AssignProject.objects.filter(
        employee=employee,
        start_date__lte=date_obj,
        project__is_active=True
    ).filter(
        Q(end_date__gte=date_obj) | Q(end_date__isnull=True)
    ).select_related("project__client")

    projects_list = []
    has_projects = bool(project_assignments)

    for pa in project_assignments:
        remaining_days = None
        if pa.end_date:
            remaining_days = calculate_remaining_working_days(employee, date_obj, pa.end_date)
            remaining_days = max(0, remaining_days)

        client_alias = pa.project.client.client_alias if pa.project and pa.project.client else ""

        projects_list.append({
            "projectAssignmentId": pa.pk,
            "project_id": pa.project.project_id if pa.project else None,
            "name": f"{client_alias} - {pa.project.project_name}" if pa.project and pa.project.project_name else "",
            "client_alias": client_alias,
            "is_costcenter": False,
            "selected": False,
            "assignment_start_date": pa.start_date,
            "assignment_end_date": pa.end_date,
            "remaining_days": remaining_days
        })

    # 8. Add cost center only if:
    #    - Employee has a cost center
    #    - Employee type is 'E'
    #    - It is not a holiday/leave day
    if employee.cost_center and employee_type_code == 'E' and not (on_leave or is_holiday or is_weekend):
        projects_list.insert(0, {
            "projectAssignmentId": f"COSTCENTER-{employee.cost_center.costcenter_id}",
            "project_id": employee.cost_center.costcenter_id,
            "name": f"{employee.cost_center.costcenter_id} - {employee.cost_center.costcenter_name}",
            "client_alias": "Cost Center",
            "is_costcenter": True,
            "selected": not has_projects,
            "assignment_start_date": None,
            "assignment_end_date": None,
            "remaining_days": None
        })

    # 9. Get first project entry’s end date & remaining working days
    first_project_entry = next(
        (e for e in items_qs if e.project_assignment and e.project_assignment.project),
        None
    )
    project_end_date, remaining_working_days = None, None
    if first_project_entry and first_project_entry.project_assignment.project.valid_to:
        project_end_date = first_project_entry.project_assignment.project.valid_to
        remaining_working_days = calculate_remaining_working_days(
            employee, now().date(), project_end_date
        )

    # ✅ 10. Return data
    return JsonResponse({
        "entries": entry_list,
        "is_leave_day": on_leave,
        "is_holiday": is_holiday,
        "is_weekend": is_weekend, # <-- Add this line
        "projects": projects_list,
        "remaining_working_days": remaining_working_days,
        "project_end_date": project_end_date,
        "employee_type_code": employee_type_code,
    }, encoder=DjangoJSONEncoder)

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
@login_required
@csrf_protect
@require_http_methods(["DELETE"])
def delete_timesheet_entry(request, entry_id):
    entry = get_object_or_404(TimesheetItem, pk=entry_id)

    # Business rule: only deletable if not approved
    if getattr(entry, "is_approved", False):
        return JsonResponse({"error": "Approved entries cannot be deleted."}, status=400)

    entry.delete()
    return JsonResponse({"success": True})

@require_POST
def copy_timesheet_entries(request):
    """
    Copy selected TimesheetItem entries to multiple target dates.
    Rules:
      - Can copy to weekends and holidays (projects allowed).
      - Approved leave on working days blocks copying.
      - Do NOT allow cost center entries on holidays.
    """
    employee = request.user.employee_profile

    # --- Get POST data ---
    item_ids = request.POST.getlist("entry_ids[]", [])
    raw_target_dates = request.POST.getlist("target_dates[]", [])
    target_dates = [d.strip() for td in raw_target_dates for d in td.split(",") if d.strip()]

    if not item_ids or not target_dates:
        return JsonResponse({"error": "Entries and target dates are required"}, status=400)

    # --- Parse target dates ---
    parsed_dates = {}
    skipped_details = {}
    today = date.today()
    for td in target_dates:
        date_obj = parse_date(td)
        if not date_obj:
            skipped_details.setdefault(td, []).append("Invalid date")
        elif date_obj > today:
            skipped_details.setdefault(td, []).append("Cannot copy to future dates")
        else:
            parsed_dates[td] = date_obj

    if not parsed_dates:
        return JsonResponse({"error": "No valid target dates to process"}, status=400)

    # --- Fetch timesheet items ---
    items = list(
        TimesheetItem.objects.filter(
            id__in=item_ids,
            hdr__employee=employee
        ).select_related(
            "hdr", "project_assignment", "project",
            "costcenter", "activity", "work_location"
        )
    )
    if not items:
        return JsonResponse({"error": "No valid entries found"}, status=404)

    # --- Fetch holidays ---
    emp_holidays = {}
    for date_obj in parsed_dates.values():
        year = date_obj.year
        month = date_obj.month
        holidays_qs = Holiday.objects.filter(
            country=employee.country,
            date__year=year,
            date__month=month
        ).only('date', 'name')
        state_holidays_qs = StateHoliday.objects.filter(
            country=employee.country,
            state=employee.state,
            date__year=year,
            date__month=month
        ).only('date', 'name')
        month_holidays = {h.date: h.name for h in holidays_qs}
        month_holidays.update({sh.date: sh.name for sh in state_holidays_qs})
        emp_holidays.update(month_holidays)

    # --- Fetch approved leave ---
    leave_ranges = LeaveRequest.objects.filter(
        employee_master=employee,
        status="Approved"
    ).filter(
        Q(start_date__lte=max(parsed_dates.values())) &
        Q(end_date__gte=min(parsed_dates.values()))
    ).values_list("start_date", "end_date")

    # --- Build leave days set, excluding weekends and holidays ---
    leave_days = set()
    for start, end in leave_ranges:
        for i in range((end - start).days + 1):
            day = start + timedelta(days=i)
            if day.weekday() >= 5:
                continue
            if day in emp_holidays:
                continue
            leave_days.add(day)

    # --- Existing entries map ---
    existing_entries = TimesheetItem.objects.filter(
        hdr__employee=employee,
        wrk_date__in=parsed_dates.values()
    ).select_related("project_assignment", "costcenter")

    existing_map = {}
    for entry in existing_entries:
        key = (entry.project_assignment_id, entry.costcenter_id)
        existing_map.setdefault(entry.wrk_date, {})[key] = entry.wrk_hours

    copied_dates = []

    # --- Process each target date ---
    for td, date_obj in parsed_dates.items():
        is_weekend = date_obj.weekday() >= 5
        is_holiday = date_obj in emp_holidays

        # Skip approved leave days (only working days)
        if date_obj in leave_days:
            skipped_details.setdefault(td, []).append("Approved leave on a working day")
            continue

        day_hours = sum(existing_map.get(date_obj, {}).values())
        entries_copied = 0

        with transaction.atomic():
            week_start = date_obj - timedelta(days=date_obj.weekday() + 1 if date_obj.weekday() != 6 else 0)
            week_end = week_start + timedelta(days=6)

            hdr, _ = TimesheetHdr.objects.get_or_create(
                employee=employee,
                week_start=week_start,
                week_end=week_end,
                defaults={"is_approved": False}
            )

            for item in items:
                key = (item.project_assignment_id, item.costcenter_id)
                if key in existing_map.get(date_obj, {}):
                    reason = (f"Project '{item.project_assignment.project.project_name}' already exists"
                              if item.project_assignment else "Cost center entry already exists")
                    skipped_details.setdefault(td, []).append(reason)
                    continue

                # 🌟 NEW CHECK: block cost center on holidays
                if item.costcenter and is_holiday:
                    skipped_details.setdefault(td, []).append(
                        f"Cannot copy cost center '{item.costcenter.costcenter_name}' to holiday"
                    )
                    continue
                if item.costcenter and is_weekend:
                    skipped_details.setdefault(td, []).append(
                        f"Cannot copy cost center '{item.costcenter.costcenter_name}' to Weekend"
                    )
                    continue

                # Project validity check
                if item.project_assignment:
                    valid_project = AssignProject.objects.filter(
                        pk=item.project_assignment.pk,
                        start_date__lte=date_obj
                    ).filter(
                        Q(end_date__gte=date_obj) | Q(end_date__isnull=True)
                    ).exists()
                    if not valid_project:
                        skipped_details.setdefault(td, []).append(
                            f"Project '{item.project_assignment.project.project_name}' invalid for this date"
                        )
                        continue

                # Hours check
                if day_hours + item.wrk_hours > 12:
                    skipped_details.setdefault(td, []).append("Copying would exceed 12h limit")
                    continue

                # --- Create entry ---
                TimesheetItem.objects.create(
                    hdr=hdr,
                    wrk_date=date_obj,
                    project_assignment=item.project_assignment,
                    costcenter=item.costcenter,
                    activity=item.activity,
                    work_location=item.work_location,
                    wrk_hours=item.wrk_hours,
                    description=item.description or ""
                )

                entries_copied += 1
                day_hours += item.wrk_hours
                existing_map.setdefault(date_obj, {})[key] = item.wrk_hours

        if entries_copied > 0:
            hdr.save()
            copied_dates.append(td)
        else:
            skipped_details.setdefault(td, []).append("No entries copied for this date")

    return JsonResponse({
        "status": "success",
        "copied": copied_dates,
        "skipped": skipped_details,
        "message": f"Copied to {len(copied_dates)} date(s). Skipped {len(skipped_details)} date(s)."
    })

# def get_week_start_end(year: int, week: int):
#     """Return Monday and Sunday dates for a given ISO week/year."""
#     try:
#         first_day = datetime.strptime(f'{year} {week} 1', '%G %V %u').date()
#         return first_day, first_day + timedelta(days=6)
#     except ValueError:
#         return None, None

from datetime import datetime, timedelta

def get_week_start_end(year: int, week: int):
    """
    Return Sunday–Saturday dates for a given Sunday-based week/year.
    Uses %U (week numbers where weeks start on Sunday).
    """
    try:
        # %U = week number (Sunday as first day, 00–53)
        wk_start = datetime.strptime(f"{year} {week} 0", "%Y %U %w").date()
        wk_end = wk_start + timedelta(days=6)
        return wk_start, wk_end
    except ValueError:
        return None, None



def build_leave_days(employee_ids, week_start, week_end):
    """Return a dict {employee_id: set of leave dates in the week}."""
    leaves_qs = LeaveRequest.objects.filter(
        employee_master_id__in=employee_ids,
        status='Approved',
        start_date__lte=week_end,
        end_date__gte=week_start
    ).only('employee_master_id', 'start_date', 'end_date')

    leave_days_map = {}
    for leave in leaves_qs:
        leave_dates = {
            leave.start_date + timedelta(days=i)
            for i in range((leave.end_date - leave.start_date).days + 1)
        }
        leave_days_map.setdefault(leave.employee_master_id, set()).update(leave_dates)
    return leave_days_map


def build_holidays_cache(subordinates, week_start, week_end):
    """Preload all holidays (country/state) with objects instead of just dates."""
    holidays_cache = {}

    # Collect unique (country_id, state_id) pairs
    country_state_pairs = {
        (emp.country.id, emp.state.id if emp.state else None)
        for emp in subordinates
    }

    for country_id, state_id in country_state_pairs:
        # Fetch Holiday objects instead of just date
        country_holidays = list(Holiday.objects.filter(
            country_id=country_id,
            date__range=(week_start, week_end)
        ))

        state_holidays = []
        if state_id:
            state_holidays = list(StateHoliday.objects.filter(
                country_id=country_id,
                state_id=state_id,
                date__range=(week_start, week_end)
            ))

        # Cache full objects (merge lists)
        holidays_cache[(country_id, state_id)] = country_holidays + state_holidays

    return holidays_cache


def get_all_holidays(emp, holidays_cache):
    key = (emp.country.id, emp.state.id if emp.state else None)
    holidays = holidays_cache.get(key, [])
    # Convert Holiday/StateHoliday objects into {date: name}
    return {h.date: getattr(h, "name", "Holiday") for h in holidays}

def calculate_timesheet_stats(emp, ts_hdr, week_start, leave_days, holidays_cache):
    """
    Calculates and returns a dictionary of all timesheet stats for an employee,
    including a detailed breakdown of entries for each day.
    Week: Sunday–Saturday
    """
    # --- 1. Base setup ---
    has_timesheets = ts_hdr is not None
    is_fully_approved = ts_hdr.is_approved if has_timesheets else False
    timesheet_items = list(ts_hdr.timesheet_items.all()) if has_timesheets else []

    # Working hours baseline
    min_daily_hours = getattr(emp.country, 'working_hours', 9) or 9
    weekly_threshold = min_daily_hours * 5

    # Leave / holiday caches for this employee
    week_end = week_start + timedelta(days=6)
    raw_leave_dates = leave_days.get(emp.id, set())
    emp_holidays = get_all_holidays(emp, holidays_cache)

    leave_dates = {
        d for d in raw_leave_dates
        if week_start <= d <= week_end and d.weekday() < 5 and d not in emp_holidays
    }

 

    



    num_leaves = len(leave_dates)
    num_holidays = len(emp_holidays)

    # --- 2. Aggregate hours ---
    weekday_hours = 0
    weekend_hours = 0
    for i in timesheet_items:
        if i.wrk_date.weekday() >= 5:  # Sat=5, Sun=6
            weekend_hours += i.wrk_hours
        else:
            weekday_hours += i.wrk_hours

    total_leave_hours = ts_hdr.tot_lev_hrs if has_timesheets else 0
    total_holiday_hours = ts_hdr.tot_hol_hrs if has_timesheets else 0

    detailed_entries = []

    # --- 3. Build day-by-day breakdown ---
    for i in range(7):  # Sunday–Saturday
        current_date = week_start + timedelta(days=i)
        is_weekend = current_date.weekday() >= 5
        is_holiday = current_date in emp_holidays
        is_leave = current_date in leave_dates and not is_weekend  # 🚫 no weekend leave

        entries_for_day = [item for item in timesheet_items if item.wrk_date == current_date]
        entered_hours = sum(e.wrk_hours for e in entries_for_day)

        # Default values
        day_total_hours = entered_hours
        status_message = "No entries made."
        holiday_name = emp_holidays.get(current_date)

        if is_holiday:
            if entered_hours == 0 or entered_hours < min_daily_hours:
                day_total_hours = min_daily_hours
            else:
                day_total_hours = entered_hours
            status_message = f"{holiday_name or 'Holiday'}"
        elif is_leave:
            day_total_hours = min_daily_hours
            status_message = "Leave Day"
        elif is_weekend:
            if entered_hours > 0:
                day_total_hours = entered_hours
            else:
                day_total_hours = 0
        else:
            if entered_hours > 0:
                status_message = "Entries made."
            day_total_hours = entered_hours

        detailed_entries.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'date_str': current_date.strftime('%b %d'),
            'day_name': current_date.strftime('%A'),
            'hours': day_total_hours,
            'is_holiday': is_holiday,
            'is_leave': is_leave,
            'is_weekend': is_weekend,
            'status_message': status_message,
            'holiday_name': holiday_name if is_holiday else None,
            'timesheet_entries': [
                {
                    'project_name': (
                        f"{e.project.client.client_alias}-{e.project.project_name}"
                        if e.project and e.project.client else
                        (e.project.project_name if e.project else None)
                    ),
                    'costcenter_name': (
                        f"{e.costcenter.costcenter_id}-{e.costcenter.costcenter_name}"
                        if e.costcenter else None
                    ),
                    'description': e.description,
                    'hours': e.wrk_hours,
                    'activity': e.activity.act_name if e.activity else 'N/A',
                    'work_location': e.work_location.loc_name if e.work_location else 'N/A'
                } for e in entries_for_day
            ]
        })

    # --- 4. Final total ---
    total_hours = weekday_hours + weekend_hours + total_leave_hours + total_holiday_hours

    # --- 5. Approval logic ---
    can_approve = has_timesheets

    if can_approve:
        if total_hours < weekly_threshold:
            can_approve = False

        # Daily check
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            if current_date.weekday() >= 5:  # skip weekend
                continue
            entered_hours_for_day = sum(
                item.wrk_hours for item in timesheet_items if item.wrk_date == current_date
            )
            if entered_hours_for_day > 0 and entered_hours_for_day < min_daily_hours:
                can_approve = False
                break

    # --- 6. Return result ---
    return {
        'employee': emp,
        'weekday_hours': weekday_hours,
        'weekend_hours': weekend_hours,
        'leave_hours': total_leave_hours,
        'holiday_hours': total_holiday_hours,
        'total_hours': total_hours,
        'num_leaves': num_leaves,
        'num_holidays': num_holidays,
        'is_fully_approved': is_fully_approved,
        'can_approve': can_approve,
        'has_timesheets': has_timesheets,
        'tsheet_id': ts_hdr.tsheet_id if has_timesheets else None,
        'detailed_entries': detailed_entries
    }

from datetime import datetime, timedelta

def build_weeks_list(num_weeks=8):
    """
    Return a list of Sunday–Saturday weeks for filters,
    starting from the previous week.
    """
    today = datetime.now().date()

    # Find the Sunday of the current week, then subtract one week
    previous_sunday = today - timedelta(days=(today.weekday() + 1) % 7) - timedelta(weeks=1)

    weeks_list = []
    for i in range(num_weeks):
        wk_start = previous_sunday - timedelta(weeks=i)
        wk_end = wk_start + timedelta(days=6)

        week_num = int(wk_start.strftime("%U"))
        if week_num == 0:  # handle first week of year
            week_num = 1

        year_num = wk_start.year
        label = f"Week {week_num} ({wk_start.strftime('%d %b')} - {wk_end.strftime('%d %b')})"

        weeks_list.append({'week': week_num, 'label': label, 'year': year_num})

    return weeks_list



from django.shortcuts import redirect
from django.http import HttpRequest
from django.contrib import messages

from django.shortcuts import redirect
from django.contrib import messages
@employee_signin_required
def timesheet_unapprove(request: HttpRequest, tsheet_id: int):
    next_url = request.GET.get('next', '/')  # Default fallback to home page
    try:
        hdr = TimesheetHdr.objects.get(pk=tsheet_id)
        if hdr.is_approved:
            hdr.is_approved = False
            hdr.approved_by = None
            hdr.approved_date = None
            hdr.save()
            messages.success(request, f"Timesheet for {hdr.employee.first_name} set to 'Pending Approval'.")
        else:
            messages.warning(request, "Timesheet is already pending approval.")
    except TimesheetHdr.DoesNotExist:
        messages.error(request, "Timesheet not found.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect(next_url)

from django.db.models import Prefetch, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.contrib import messages

# Assume all helper functions (get_week_start_end, build_leave_days,
# build_holidays_cache, calculate_timesheet_stats, build_weeks_list) are available.
@employee_signin_required
def timesheet_approval_list(request):
    """
    Manages the timesheet approval list for a manager.
    Supports Sunday–Saturday weeks and filtering by search/status.
    """
    try:
        manager = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

    # --- 1. Get and Validate User Inputs ---
    today = datetime.now().date()
    selected_year = int(request.GET.get('year', today.year))

    # Compute Sunday-based current week number (%U)
    current_week_num = int(today.strftime("%U"))-1
    selected_week = int(request.GET.get('week', current_week_num))


    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'All')

    # --- 2. Get week start/end (Sunday–Saturday) ---
    week_start, week_end = get_week_start_end(selected_year, selected_week)
    if not week_start:
        messages.error(request, "Invalid week/year selection.")
        context = {
            'timesheet_data': [],
            'weeks_list': build_weeks_list(),
            'unique_years': sorted({w['year'] for w in build_weeks_list()}, reverse=True),
            'selected_week': selected_week,
            'selected_year': selected_year,
            'search_query': search_query,
            'selected_status': status_filter,
            'employee': manager,
            'is_manager': False
        }
        return render(request, 'timesheet/approve_timesheets.html', context)

    # --- 3. Get Subordinates ---
    subordinates = Employees.objects.filter(manager=manager).select_related(
        'country', 'state'
    ).order_by('employee_id', 'first_name', 'last_name')

    if search_query:
        subordinates = subordinates.filter(
            Q(employee_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # --- 4. Prefetch Timesheet Headers ---
    timesheet_prefetch_queryset = TimesheetHdr.objects.filter(
        week_start=week_start, week_end=week_end
    ).prefetch_related('timesheet_items')

    subordinates = subordinates.prefetch_related(
        Prefetch(
            'timesheet_headers',
            queryset=timesheet_prefetch_queryset,
            to_attr='timesheet_header_list'
        )
    )

    # --- 5. Build Leave & Holiday Caches ---
    employee_ids = [emp.id for emp in subordinates]
    leave_days = build_leave_days(employee_ids, week_start, week_end)
    holidays_cache = build_holidays_cache(subordinates, week_start, week_end)

    # --- 6. Build Timesheet Data ---
    timesheet_data = []
    for emp in subordinates:
        ts_hdr = emp.timesheet_header_list[0] if emp.timesheet_header_list else None
        stats = calculate_timesheet_stats(emp, ts_hdr, week_start, leave_days, holidays_cache)
        timesheet_data.append(stats)

    # --- 7. Apply Status Filter ---
    if status_filter == 'Approved':
        timesheet_data = [d for d in timesheet_data if d.get('is_fully_approved')]
    elif status_filter == 'Pending':
        timesheet_data = [
            d for d in timesheet_data
            if d.get('has_timesheets') and not d.get('is_fully_approved') and d.get('can_approve')
        ]
    elif status_filter == 'Incomplete':
        timesheet_data = [
            d for d in timesheet_data
            if d.get('has_timesheets') and not d.get('is_fully_approved') and not d.get('can_approve')
        ]
    elif status_filter == 'No Data':
        timesheet_data = [d for d in timesheet_data if not d.get('has_timesheets')]

    # --- 8. Context & Render ---
    weeks_list = build_weeks_list()
    unique_years = sorted({w['year'] for w in weeks_list}, reverse=True)
    is_manager = subordinates.exists()

    context = {
        'timesheet_data': timesheet_data,
        'weeks_list': weeks_list,
        'unique_years': unique_years,
        'selected_week': selected_week,
        'selected_year': selected_year,
        'search_query': search_query,
        'selected_status': status_filter,
        'employee': manager,
        'is_manager': is_manager
    }

    return render(request, 'timesheet/approve_timesheets.html', context)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
@employee_signin_required
def pending_timesheets(request):
    """
    Shows all pending timesheet entries for weeks older than the previous week.
    Example: If current week is Sun 21 – Sat 28, shows only weeks ending on or before Sat 20.
    """
    try:
        manager = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        messages.error(request, "Employee profile not found. Please contact administrator.")
        return redirect('timesheet_approval_list')

    # Get current date and calculate cutoff
    today = datetime.now().date()
    current_week_num = int(today.strftime("%U"))  # Current week (0-based from %U)
    
    # Calculate cutoff: previous week's end (include previous week)
    cutoff_week = current_week_num - 1  # Previous week
    cutoff_year = today.year
    
    # Get cutoff week's end date (Saturday) - this will be the previous week's end
    cutoff_week_start, cutoff_week_end = get_week_start_end(cutoff_year, cutoff_week)
    if not cutoff_week_end:
        # Handle year boundary
        cutoff_year -= 1
        cutoff_week = 52
        cutoff_week_start, cutoff_week_end = get_week_start_end(cutoff_year, cutoff_week)
    
    
    # Get subordinates
    subordinates = Employees.objects.filter(manager=manager).select_related(
        'country', 'state'
    ).order_by('employee_id', 'first_name', 'last_name')
    
    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        subordinates = subordinates.filter(
            Q(employee_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Get pending timesheets for weeks older than cutoff
    pending_timesheets = TimesheetHdr.objects.filter(
        employee__in=subordinates,
        week_end__lte=cutoff_week_end,  # Only weeks ending on or before cutoff
        is_approved=False  # Only unapproved timesheets
    ).select_related('employee').prefetch_related('timesheet_items').order_by(
        '-week_end', 'employee__employee_id'  # Newest weeks first, then by employee
    )
    
    # Build timesheet data with additional fields
    timesheet_data = []
    for ts_hdr in pending_timesheets:
        # Calculate week info
        week_start, week_end = ts_hdr.week_start, ts_hdr.week_end
        week_num = int(week_end.strftime("%U")) - 1
        year = week_end.year
        
        
        # Get employee stats for that week
        employee_ids = [ts_hdr.employee.id]
        leave_days = build_leave_days(employee_ids, week_start, week_end)
        holidays_cache = build_holidays_cache([ts_hdr.employee], week_start, week_end)
        stats = calculate_timesheet_stats(ts_hdr.employee, ts_hdr, week_start, leave_days, holidays_cache)
        
        # Add additional fields
        stats.update({
            'tsheet_id': ts_hdr.tsheet_id,
            'week_start': week_start,
            'week_end': week_end,
            'week_num': week_num,
            'year': year,
            'submitted_date': ts_hdr.updated_at,  # Use updated_at for more accurate submission time
            'updated_date': ts_hdr.updated_at,
            'is_delayed': ts_hdr.is_delayed,
            'can_approve': stats.get('can_approve', False)
        })
        
        timesheet_data.append(stats)
    
    # Apply status filter - default to Pending
    status_filter = request.GET.get('status', 'Pending')
    if status_filter == 'Pending':
        timesheet_data = [d for d in timesheet_data if d.get('can_approve')]
    
    context = {
        'timesheet_data': timesheet_data,
        'search_query': search_query,
        'selected_status': status_filter,
        'employee': manager,
        'is_manager': subordinates.exists(),
        'cutoff_date': cutoff_week_end,
        'current_week': f"Week {current_week_num}, {today.year}"
    }
    
    return render(request, 'timesheet/pending_timesheets.html', context)

employee_signin_required
@require_POST
def approve_timesheet(request):
    """Approve a single employee's weekly timesheet (Sunday–Saturday)."""
    emp_id = request.POST.get('employee_id')
    year = int(request.POST.get('year'))
    week = int(request.POST.get('week'))

    week_start, week_end = get_week_start_end(year, week)
    if not week_start or not week_end:
        return JsonResponse({'success': False, 'message': 'Invalid week/year.'})

    try:
        hdr = TimesheetHdr.objects.get(
            employee_id=emp_id,
            week_start=week_start,
            week_end=week_end
        )

        if hdr.is_approved:
            return JsonResponse({'success': False, 'message': 'Already approved.'})

        hdr.is_approved = True
        hdr.approved_by = request.user.employee_profile
        hdr.approved_date = timezone.now()
        hdr.save()

        return JsonResponse({"success": True, "message": "Timesheet approved."})

    except TimesheetHdr.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Timesheet not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@employee_signin_required
@require_POST
def approve_selected_timesheets(request):
    """Approve multiple employees' weekly timesheets at once (Sunday–Saturday)."""
    ids = request.POST.getlist('ids[]')  # ["empID-year-week", ...]
    approved = []
    errors = []

    for composite_id in ids:
        try:
            emp_id, year, week = composite_id.split('-')
            week_start, week_end = get_week_start_end(int(year), int(week))
            if not week_start or not week_end:
                errors.append({'id': composite_id, 'error': 'Invalid week/year'})
                continue

            hdr = TimesheetHdr.objects.get(
                employee_id=emp_id,
                week_start=week_start,
                week_end=week_end
            )

            if not hdr.is_approved:
                hdr.is_approved = True
                hdr.approved_by = request.user.employee_profile
                hdr.approved_date = timezone.now()
                hdr.save()
                approved.append(composite_id)

        except TimesheetHdr.DoesNotExist:
            errors.append({'id': composite_id, 'error': 'Timesheet not found'})
        except Exception as e:
            errors.append({'id': composite_id, 'error': str(e)})

    return JsonResponse({
        "success": True,
        "message": f"{len(approved)} timesheet(s) approved.",
        "approved_ids": approved,
        "errors": errors
    })




from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from datetime import datetime, timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q





@employee_signin_required
def timesheet_week_details(request):
    try:
        emp_id = int(request.GET.get('employee_id'))
        year = int(request.GET.get('year'))
        week = int(request.GET.get('week'))

        # ✅ Use Sunday–Saturday logic (%U), not ISO
        week_start, week_end = get_week_start_end(year, week)
        if not week_start:
            return JsonResponse({'success': False, 'message': 'Invalid week/year'}, status=400)

        employee = Employees.objects.select_related('country', 'state').get(pk=emp_id)

        leave_days_map = build_leave_days([emp_id], week_start, week_end)
        holidays_cache = build_holidays_cache([employee], week_start, week_end)

        ts_hdr = TimesheetHdr.objects.filter(
            employee_id=emp_id,
            week_start=week_start
        ).prefetch_related(
            'timesheet_items__project',
            'timesheet_items__costcenter',
        ).first()

        stats = calculate_timesheet_stats(employee, ts_hdr, week_start, leave_days_map, holidays_cache)
        entries = stats['detailed_entries']

        # 🔹 Remove weekends (Saturday=5, Sunday=6) if they have no entries
        filtered_entries = []
        for e in entries:

            filtered_entries.append(e)

        return JsonResponse({'success': True, 'entries': filtered_entries})

    except Employees.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from datetime import timedelta

def generate_utilization_report(logged_in_employee, start_date, end_date):
    """
    Generate a utilization report for the employees managed by the logged-in user.
    Rules:
      - Mon–Fri are official working days.
      - Leave: counts as 1 day (minimum hours per day).
      - Holiday: if no entry → holiday day; if entry → work day.
      - Weekend: ignored unless employee enters → then counts in worked hours, not days.
    """
    # Step 1: Choose employees for report
    if logged_in_employee is None:  # Admin
        employees = Employees.objects.all().order_by("employee_id", "first_name", "last_name")
    else:
        if logged_in_employee.user.is_staff or logged_in_employee.user.is_superuser:
            employees = Employees.objects.all().order_by("employee_id", "first_name", "last_name")
        elif logged_in_employee.employees_managed.exists():
            employees = logged_in_employee.employees_managed.all().order_by("employee_id", "first_name", "last_name")
        else:
            raise PermissionDenied("You are not authorized to view this report.")

    report = []

    for emp in employees:
        work_hours_per_day = getattr(emp.country, "working_hours", 9)

        # --- Holidays (national + state) ---
        holidays = set(Holiday.objects.filter(
            country=emp.country,
            date__range=(start_date, end_date)
        ).values_list("date", flat=True))

        state_holidays = set(StateHoliday.objects.filter(
            country=emp.country,
            state=emp.state,
            date__range=(start_date, end_date)
        ).values_list("date", flat=True))

        all_holidays = holidays | state_holidays

        # --- Timesheet items ---
        items = TimesheetItem.objects.filter(
            hdr__employee=emp,
            wrk_date__range=(start_date, end_date)
        )

        worked_hours = leave_hours = holiday_hours = 0
        total_work_days = 0
        worked_days = leave_days = holiday_days = 0
        extra_weekend_days = 0

        current = start_date
        while current <= end_date:
            weekday = current.weekday()  # 0=Mon, 6=Sun
            day_items = [i for i in items if i.wrk_date == current]
            total_daily_hours = sum(i.wrk_hours for i in day_items)

            is_holiday = current in all_holidays
            is_leave = LeaveRequest.objects.filter(
                employee_master=emp,
                start_date__lte=current,
                end_date__gte=current,
                status="Approved"
            ).exists()

            if weekday < 5:  # Mon–Fri
                total_work_days += 1

                if is_holiday:
                    if total_daily_hours > 0:  # worked on holiday
                        worked_hours += total_daily_hours
                        worked_days += 1
                    else:  # holiday not worked
                        holiday_hours += work_hours_per_day
                        holiday_days += 1
                elif is_leave:
                    leave_hours += work_hours_per_day
                    leave_days += 1
                else:
                    worked_hours += total_daily_hours
                    if total_daily_hours >= work_hours_per_day:
                        worked_days += 1

            else:  # Weekend
                if total_daily_hours > 0:
                    worked_hours += total_daily_hours
                    extra_weekend_days += 1  # tracked separately, does not count in total_work_days

            current += timedelta(days=1)

        # --- Delayed entries ---
        delayed_entries = TimesheetHdr.objects.filter(
            employee=emp,
            week_end__gte=start_date,
            week_start__lte=end_date,
            is_delayed=True
        ).count()

        # --- Utilization: hours-based ---
        required_hours = total_work_days * work_hours_per_day
        actual_hours = worked_hours + leave_hours + holiday_hours
        utilization = min((actual_hours / required_hours) * 100, 100) if required_hours > 0 else 0.0

        report.append({
            "employee_obj": emp,
            "employee_name": f"{emp.employee_id}-{emp.first_name} {emp.last_name}",
            "worked_days": worked_days,          # int, weekdays worked
            "leave_days": leave_days,            # int, weekdays on leave
            "holiday_days": holiday_days,        # int, weekdays holiday not worked
            "total_work_days": total_work_days,  # int, Mon–Fri only
            "extra_weekend_days": extra_weekend_days,  # int, weekends worked
            "delayed_entries": delayed_entries,  # int
            "utilization": round(utilization, 2) # float, hours-based
        })

    return report

@admin_signin_required
def admin_work_utilization_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Admins only.")

    today = datetime.today().date()
    default_end = today
    default_start = today - timedelta(days=6)

    # --- Get dates from query params ---
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else default_start
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else default_end
    except ValueError:
        start_date, end_date = default_start, default_end

    # --- Enforce min/max allowed dates ---
    min_allowed = datetime(2025, 8, 1).date()
    start_date = max(start_date, min_allowed)
    end_date = min(end_date, today)

    if start_date > end_date:
        start_date = end_date - timedelta(days=6)
        if start_date < min_allowed:
            start_date = min_allowed

    # --- Admins do not need an Employees object ---
    # Pass None to generate_utilization_report to indicate admin
    report_data = generate_utilization_report(None, start_date, end_date) if request.GET else []

    return render(request, "timesheet/admin/work_utilization.html", {
        "report_data": report_data,
        "start_date": start_date,
        "end_date": end_date,
        "today": today
    })


@employee_signin_required
@employee_signin_required
def employee_work_utilization_view(request):
    today = datetime.today().date()
    default_end = today
    default_start = today - timedelta(days=6)

    # --- Get dates from query ---
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else default_start
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else default_end
    except ValueError:
        start_date, end_date = default_start, default_end

    # --- Date bounds ---
    min_allowed = datetime(2025, 8, 1).date()
    start_date = max(start_date, min_allowed)
    end_date = min(end_date, today)

    if start_date > end_date:
        start_date = end_date - timedelta(days=6)
        if start_date < min_allowed:
            start_date = min_allowed

    # --- Get logged-in employee ---
    try:
        employee_obj = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        raise PermissionDenied("Employee profile not found.")

    # --- Check if user manages others ---
    is_manager = employee_obj.employees_managed.exists()

    report_data = []
    if request.GET and is_manager:
        # Only generate report if manager with subordinates
        report_data = generate_utilization_report(employee_obj, start_date, end_date)

        # Filter to include only subordinates
        report_data = [
            r for r in report_data if r["employee_obj"] in employee_obj.employees_managed.all()
        ]

    return render(request, "timesheet/employee/work_utilization.html", {
        "report_data": report_data,
        "employee": employee_obj,
        "start_date": start_date,
        "end_date": end_date,
        "today": today,
        "is_manager": is_manager,
    })

import openpyxl
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from datetime import datetime

def _build_excel_response(report_data, filename):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Employee Utilization"

    # Header row
    headers = [
        "Employee",
        "Weekdays Worked",
        "Weekends Worked",
        "Leave Days",
        "Holidays",
        "Total Work Days",
        "Delayed Entries",
        "Work Utilization %"
    ]
    sheet.append(headers)

    # Data rows
    for entry in report_data:
        sheet.append([
            entry.get("employee_name", ""),
            entry.get("worked_days", 0),
            entry.get("extra_weekend_days",0),
            entry.get("leave_days", 0),
            entry.get("holiday_days", 0),
            entry.get("total_work_days", 0),
            entry.get("delayed_entries", 0),
            f"{entry.get('utilization', 0)}%",
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


@admin_signin_required
def export_admin_utilization(request):
    # --- Permission check ---
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Admins only.")

    # --- Get query parameters ---
    start_str = request.GET.get("start_date", "").strip()
    end_str = request.GET.get("end_date", "").strip()

    if not start_str or not end_str:
        return HttpResponseBadRequest("Start and End date parameters are required.")

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date format. Use YYYY-MM-DD.")

    # --- Generate report ---
    # For admins, pass None to indicate admin (no employee object needed)
    report_data = generate_utilization_report(None, start_date, end_date)

    # --- Return Excel response ---
    return _build_excel_response(report_data, "Admin_Employee_Utilization.xlsx")

@employee_signin_required
def export_employee_utilization(request):
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    if not start_date or not end_date:
        return HttpResponseBadRequest("Start and End date parameters are required.")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date format. Use YYYY-MM-DD.")

    try:
        employee_obj = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        raise PermissionDenied("Employee profile not found.")

    report_data = generate_utilization_report(employee_obj, start_date, end_date)

    return _build_excel_response(report_data, "Employee_Utilization.xlsx")

from datetime import timedelta
from django.core.exceptions import PermissionDenied

def generate_project_cc_utilization_report(logged_in_employee, start_date, end_date):
    from collections import defaultdict
    from datetime import timedelta

    # --- Employee scope ---
    if logged_in_employee is None:
        employees = Employees.objects.all().order_by('employee_id', 'first_name', 'last_name')
    elif logged_in_employee.user.is_staff or logged_in_employee.user.is_superuser:
        employees = Employees.objects.all().order_by('employee_id','first_name','last_name')
    elif logged_in_employee.employees_managed.exists():
        employees = logged_in_employee.employees_managed.all().order_by('employee_id','first_name','last_name')
    else:
        raise PermissionDenied("You are not authorized to view this report.")

    report = []

    for emp in employees:
        min_working_hours = getattr(emp.country, "working_hours", 9)

        # --- Holidays ---
        holidays = set(Holiday.objects.filter(
            country=emp.country,
            date__range=(start_date, end_date)
        ).values_list("date", flat=True))
        state_holidays = set(StateHoliday.objects.filter(
            country=emp.country,
            state=emp.state,
            date__range=(start_date, end_date)
        ).values_list("date", flat=True))
        all_holidays = holidays | state_holidays

        # --- Timesheet items ---
        items = TimesheetItem.objects.filter(
            hdr__employee=emp,
            wrk_date__range=(start_date, end_date)
        )

        daily_project_hours = defaultdict(float)
        daily_cc_hours = defaultdict(float)
        for item in items:
            if item.project:
                daily_project_hours[item.wrk_date] += item.wrk_hours
            if item.costcenter:
                daily_cc_hours[item.wrk_date] += item.wrk_hours

        # --- Counters ---
        weekday_worked = 0
        weekend_worked = 0
        leave_days = 0
        holiday_days = 0
        project_days_count = 0
        cc_days_count = 0
        total_hours_project = 0.0
        total_hours_cc = 0.0
        total_working_days = 0  # Mon–Fri

        current = start_date
        while current <= end_date:
            weekday = current.weekday()  # 0=Mon, 6=Sun
            proj_hours = daily_project_hours.get(current, 0)
            cc_hours = daily_cc_hours.get(current, 0)
            total_daily_hours = proj_hours + cc_hours

            is_holiday = current in all_holidays
            is_leave = LeaveRequest.objects.filter(
                employee_master=emp,
                start_date__lte=current,
                end_date__gte=current,
                status="Approved"
            ).exists()

            if weekday < 5:  # Mon–Fri
                total_working_days += 1

                if is_leave:
                    leave_days += 1
                elif is_holiday and total_daily_hours == 0:
                    holiday_days += 1
                else:
                    if total_daily_hours > 0:
                        weekday_worked += 1
                        total_hours_project += proj_hours
                        total_hours_cc += cc_hours
                        if proj_hours >= min_working_hours:
                            project_days_count += 1
                        if cc_hours >= min_working_hours:
                            cc_days_count += 1

            else:  # Weekend
                if total_daily_hours > 0:
                    weekend_worked += 1
                    total_hours_project += proj_hours
                    total_hours_cc += cc_hours

                    # ✅ Also count weekend entries for project/cc days
                    if proj_hours >= min_working_hours:
                        project_days_count += 1
                    if cc_hours >= min_working_hours:
                        cc_days_count += 1

            current += timedelta(days=1)


        available_days = total_working_days - leave_days - holiday_days

        # --- Utilization ---
        project_util = (total_hours_project / (available_days * min_working_hours) * 100) if available_days > 0 else 0.0
        cc_util = (total_hours_cc / (available_days * min_working_hours) * 100) if available_days > 0 else 0.0
        project_util = min(project_util, 100.0)
        cc_util = min(cc_util, 100.0)

        report.append({
            "employee_obj": emp,
            "employee_name": f"{emp.employee_id}-{emp.first_name} {emp.last_name}",
            "total_working_days": total_working_days,   # Mon–Fri count
            "weekday_worked": weekday_worked,           # weekdays with work hours
            "weekend_worked": weekend_worked,           # weekends worked
            "leave_days": leave_days,
            "holiday_days": holiday_days,
            "project_days": project_days_count,
            "cc_days": cc_days_count,
            "project_utilization": round(project_util, 2),
            "cc_utilization": round(cc_util, 2),
        })

    return report

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta

# ✅ Admin / Manager view
@admin_signin_required
def admin_project_cc_utilization_view(request):
    today = datetime.today().date()
    default_end = today
    default_start = today - timedelta(days=6)

    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else default_start
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else default_end
    except ValueError:
        start_date, end_date = default_start, default_end

    min_allowed = datetime(2025, 8, 1).date()
    start_date = max(start_date, min_allowed)
    end_date = min(end_date, today)

    if start_date > end_date:
        start_date = end_date - timedelta(days=6)
        if start_date < min_allowed:
            start_date = min_allowed

    # ✅ Pass None for admin to indicate "all employees"
    employee_obj = Employees.objects.filter(user=request.user).first()  # Optional, just for template
    report_data = generate_project_cc_utilization_report(None, start_date, end_date) if request.GET else []

    return render(request, "timesheet/admin/project_cc_utilization.html", {
        "report_data": report_data,
        "employee": employee_obj,
        "start_date": start_date,
        "end_date": end_date,
        "today": today,
    })


# ✅ Employee self view
@employee_signin_required
def employee_project_cc_utilization_view(request):
    today = datetime.today().date()
    default_end = today
    default_start = today - timedelta(days=6)

    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else default_start
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else default_end
    except ValueError:
        start_date, end_date = default_start, default_end

    min_allowed = datetime(2025, 8, 1).date()
    start_date = max(start_date, min_allowed)
    end_date = min(end_date, today)

    if start_date > end_date:
        start_date = end_date - timedelta(days=6)
        if start_date < min_allowed:
            start_date = min_allowed

    try:
        employee_obj = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        raise PermissionDenied("Employee profile not found.")

    # Check if user manages others
    is_manager = employee_obj.employees_managed.exists()

    report_data = []
    if request.GET and is_manager:
        # Only generate report for managers with subordinates
        report_data = generate_project_cc_utilization_report(employee_obj, start_date, end_date)

        # Filter to include only subordinates and optionally manager themselves
        report_data = [
            r for r in report_data if r["employee_obj"] in employee_obj.employees_managed.all()
        ]

    return render(request, "timesheet/employee/project_cc_utilization.html", {
        "report_data": report_data,
        "employee": employee_obj,
        "start_date": start_date,
        "end_date": end_date,
        "today": today,
        "is_manager": is_manager
    })

import openpyxl
from django.http import HttpResponse


def export_project_cc_utilization(request):
    # --- Get and validate dates ---
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    if not start_str or not end_str:
        return HttpResponseBadRequest("Start and End date are required.")

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date format. Use YYYY-MM-DD.")

    # --- Determine employee scope ---
    if request.user.is_staff or request.user.is_superuser:
        employee_obj = None  # Admin sees all
    else:
        try:
            employee_obj = Employees.objects.get(user=request.user)
        except Employees.DoesNotExist:
            raise PermissionDenied("Employee profile not found.")

    # --- Generate report data ---
    report_data = generate_project_cc_utilization_report(employee_obj, start_date, end_date)

    # --- Create Excel workbook ---
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Project vs CC Utilization"

    headers = [
        "Employee",
        "Total Working Days",
        "Weekday Worked",
        "Weekend Worked",
        "Holidays",
        "Leave Days",
        "Available Days",
        "Project Days",
        "CC Days",
        "Project Utilization %",
        "CC Utilization %",
    ]
    sheet.append(headers)

    for entry in report_data:
        sheet.append([
            entry.get("employee_name"),
            entry.get("total_working_days", 0),
            entry.get("weekday_worked", 0),
            entry.get("weekend_worked", 0),
            entry.get("holiday_days", 0),
            entry.get("leave_days", 0),
            entry.get("available_days", 0),
            entry.get("project_days", 0),
            entry.get("cc_days", 0),
            f"{entry.get('project_utilization', 0)}%",
            f"{entry.get('cc_utilization', 0)}%",
        ])

    # --- Prepare response ---
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Project_CC_Utilization.xlsx"'
    wb.save(response)
    return response