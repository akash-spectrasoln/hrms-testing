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




def client_list(request):
    """List all clients with search, filter, and sorting."""
    search = request.GET.get('search', '').strip()
    alias = request.GET.get('alias', '')
    country = request.GET.get('country', '')
    sort = request.GET.get('sort', 'client_name')

    allowed_sorts = [
        'client_name', '-client_name',
        'client_alias', '-client_alias',
        'client_addr', '-client_addr',
        'country__country_name', '-country__country_name'
    ]
    sort = sort if sort in allowed_sorts else 'client_name'

    # Base queryset
    clients = Client.objects.select_related('country')

    # Filters
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

    clients = clients.order_by(sort)

    context = {
        'clients': clients,
        'search_query': search,
        'alias_filter': alias,
        'country_filter': country,
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
    }

    return render(request, 'timesheet/client_list.html', context)
    



def client_create(request):
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)

        # store created_by correctly
        if hasattr(request.user, "employee_profile"):
            client.created_by = request.user.employee_profile  # assign object

        client.save()
        return redirect('client_list')

    return render(request, 'timesheet/client_form.html', {'form': form})




def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    print(request.user)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)

        # ✅ Directly get Employee using request.user
        try:
            employee = Employees.objects.get(company_email=request.user)
            client.updated_by = employee
        except Employees.DoesNotExist:
            pass  # Optionally handle this case

        client.save()
        return redirect('client_list')

    return render(request, 'timesheet/client_form.html', {'form': form})



def client_delete(request, pk):
    """Delete a client."""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'timesheet/client_confirm_delete.html', {'client': client})






from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_GET




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
        projects = projects.filter(valid_to__lt=today)
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

def project_create(request):
    """
    Create a new project. Show form (GET) or save data (POST).
    """
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('project_list')
    return render(request, 'timesheet/project_form.html', {'form': form})


def project_update(request, pk):
    """
    Update an existing project. Show prefilled form or save changes.
    """
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('project_list')
    return render(request, 'timesheet/project_form.html', {'form': form, 'project': project})


def project_delete_view(request, pk):

    """
    Soft delete a project after confirmation.
    """
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        project.soft_delete()
        messages.success(request, "Project deactivated (soft-deleted) successfully!")
        return redirect('project_list')

    return render(request, 'timesheet/project_confirm_delete.html', {'project': project})


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
    qs = Employees.objects.all().order_by('employee_id','first_name','last_name')

    if term:
        qs = qs.filter(
            Q(employee_id__icontains=term) |
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term)
        ).order_by('employee_id','first_name','last_name')

    results = [
        {"id": e.pk, "text": f"{e.employee_id} - {e.first_name} {e.last_name}"}
        for e in qs
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
    template_name = 'timesheet/assignproject_form.html'
    form_class = AssignProjectCreateForm
    success_url = reverse_lazy('assign-project-list')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Project assigned successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class AssignProjectUpdateView(UpdateView):
    model = AssignProject
    form_class = AssignProjectUpdateForm
    template_name = 'timesheet/assignproject_form.html'
    success_url = reverse_lazy('assign-project-list')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Assignment updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


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

    # Optional: logger.debug for production instead of print
    logger.debug(f"AJAX client_id={client_id}, projects={list(projects)}")

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
            qs = qs.filter(end_date__lt=today)
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
        return render(request, 'timesheet/assignproject_confirm_delete.html', {'assignment': assignment})

    def post(self, request, pk):
        assignment = get_object_or_404(AssignProject, pk=pk)
        assignment.is_active = False
        assignment.save()
        messages.success(request, "Assignment removed successfully.")
        return redirect('assign-project-list')

  
class CostCenterListView(ListView):
    model = CostCenter
    template_name = 'timesheet/costcenter_list.html'
    context_object_name = 'costcenters'
    paginate_by = 20  # Optional: add pagination for large lists

    def get_queryset(self):
        query = self.request.GET.get('search', '').strip()
        is_active_filter = self.request.GET.get('is_active', '').strip().lower()

        # Default queryset: only active cost centers
        qs = CostCenter.objects.filter(is_active=True)

        # Search by name
        if query:
            qs = qs.filter(costcenter_name__icontains=query)

        # Active/inactive filter (overrides default if explicitly set)
        if is_active_filter == 'active':
            qs = qs.filter(is_active=True)
        elif is_active_filter == 'inactive':
            qs = qs.filter(is_active=False)
        # else: default already active, no change

        return qs.order_by('costcenter_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', '').strip(),
            'is_active_filter': self.request.GET.get('is_active', '').strip().lower(),
            'status_options': [
                ('active', 'Active'),
                ('inactive', 'Inactive'),
            ]
        })
        return context



class CostCenterCreateView(CreateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'timesheet/costcenter_form.html'
    success_url = reverse_lazy('costcenter_list')


class CostCenterUpdateView(UpdateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'timesheet/costcenter_form.html'
    success_url = reverse_lazy('costcenter_list')


#Employee App Features 

import calendar




def adjust_month_year(month, year, delta):
    month += delta
    if month < 1:
        return 12, year - 1
    elif month > 12:
        return 1, year + 1
    return month, year


# ---------------- 1️⃣ Config ----------------


def timesheet_calendar(request):
    """
    Renders the timesheet calendar with dynamic navigation and data.
    """
    employee = request.user.employee_profile
    is_manager = Employees.objects.filter(manager=employee).exists()
    today = timezone.localdate()

    # ---------------- 1️⃣ Config ----------------
    # Hardcode the earliest month and year an employee can navigate to.
    EARLIEST_NAV_MONTH = 7  # July
    EARLIEST_NAV_YEAR = 2025

    # ---------------- 2️⃣ Month & Year selection ----------------
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        month, year = today.month, today.year

    # Validate month/year
    month = max(1, min(12, month))
    year = max(2000, min(2100, year))

    # ---------------- 3️⃣ Apply Navigation Limits ----------------
    # Limit backward navigation to the fixed earliest date.
    current_date_obj = date(year, month, 1)
    earliest_date_obj = date(EARLIEST_NAV_YEAR, EARLIEST_NAV_MONTH, 1)

    if current_date_obj < earliest_date_obj:
        month, year = EARLIEST_NAV_MONTH, EARLIEST_NAV_YEAR
    
    # The forward navigation limit will be applied later in the context.
    # No need to change the month/year here.

    # ---------------- 4️⃣ Timesheet items ----------------
    timesheet_qs = TimesheetItem.objects.filter(
        hdr__employee=employee,
        wrk_date__year=year,
        wrk_date__month=month
    ).values('wrk_date').annotate(
        total_hours=Sum('wrk_hours'),
        approved_count=Sum(
            Case(When(hdr__is_approved=True, then=1), default=0, output_field=IntegerField())
        )
    )

    timesheet_hours = {entry['wrk_date']: entry['total_hours'] for entry in timesheet_qs}
    timesheet_dates = set(timesheet_hours.keys())
    approved_dates = {entry['wrk_date'] for entry in timesheet_qs if entry['approved_count'] > 0}

    # ---------------- 5️⃣ Holidays & Leave ----------------
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

    all_holidays = {h.date: h.name for h in holidays_qs}
    all_holidays.update({sh.date: sh.name for sh in state_holidays_qs})

    # Leave dates
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])

    leave_dates = set()
    for start, end in LeaveRequest.objects.filter(
        employee_master=employee,
        status='Approved',
        start_date__lte=month_end,
        end_date__gte=month_start
    ).values_list('start_date', 'end_date'):
        for i in range((end - start).days + 1):
            day = start + timedelta(days=i)
            if day.month == month:
                leave_dates.add(day)

    # ---------------- 6️⃣ Build calendar grid (Corrected) ----------------
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)
    calendar_data = []

    for week in month_days:
        week_data = []
        for day in week:
            if day.month != month:
                week_data.append(None)
                continue

            is_weekend = day.weekday() >= 5
            is_holiday = day in all_holidays
            holiday_name = all_holidays.get(day, '')
            on_leave = day in leave_dates
            is_entered = day in timesheet_dates
            is_future = day > today
            is_approved = day in approved_dates

            status, hours, is_disabled = "", None, False

            # Disabling logic: Weekends, Holidays, and Leave days are ALWAYS disabled.
            if is_weekend or is_holiday or on_leave:
                is_disabled = True
            elif is_future:
                is_disabled = True
            else:
                is_disabled = False

            # Status logic: Prioritize special days for the class name
            if is_weekend:
                status = "status-weekend"
            elif is_holiday:
                status = "status-holiday"
            elif on_leave:
                status = "status-leave"
            elif is_entered:
                status = "status-entered"
            else:
                status = "status-not-entered"

            # Set hours only if entries exist, regardless of status class
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
            })
        calendar_data.append(week_data)

    # ---------------- 7️⃣ Navigation ----------------
    prev_month, prev_year = adjust_month_year(month, year, -1)
    next_month, next_year = adjust_month_year(month, year, 1)

    # Disable previous navigation if before earliest date
    prev_date_obj = date(prev_year, prev_month, 1) if prev_month else None
    if prev_date_obj and prev_date_obj < earliest_date_obj:
        prev_month, prev_year = None, None

    # Enable next navigation to any month in the current year, but not future years.
    # This now allows navigation up to December of the current year.
    next_date_obj = date(next_year, next_month, 1) if next_month else None
    if next_date_obj and next_date_obj > date(today.year, 12, 1):
        next_month, next_year = None, None

    # ---------------- 8️⃣ Context ----------------
    context = {
        'year': year,
        'month': month,
        'current_month_name': calendar.month_name[month],
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'calendar_data': calendar_data,
        'today': today,
        'activities': Activity.objects.only('act_id', 'act_name'),
        'work_locations': WrkLocation.objects.only('loc_id', 'loc_name'),
        'employee': employee,
        'timesheet_entries': TimesheetItem.objects.filter(
            hdr__employee=employee,
            wrk_date__year=year,
            wrk_date__month=month
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
    }

    # ---------------- 9️⃣ AJAX support ----------------
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'timesheet/calendar_grid.html', context)
        
    return render(request, 'timesheet/calendar.html', context)
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

    # Week start (Monday) & end (Sunday) for header
    week_start = date_obj - timedelta(days=date_obj.weekday())
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
            pass

    # 7️⃣ Fetch all items for same date in one go (optimize queries)
    existing_items = list(TimesheetItem.objects.filter(
        hdr__employee=employee,
        wrk_date=date_obj
    ))

    # 8️⃣ Calculate other entries' total (exclude current if editing)
    other_total = sum(item.wrk_hours for item in existing_items if not existing_entry or item.pk != existing_entry.pk)
    new_total = other_total + hours_worked
    if new_total > 12:
        return _error_response(
            request,
            f"Total hours for {date_obj} exceed 12. (Existing total: {other_total}, Attempted: {hours_worked})",
            400
        )

    # 9️⃣ Check for duplicates (works in both create & edit mode)
    for item in existing_items:
        if existing_entry and item.pk == existing_entry.pk:
            continue  # skip self

        same_costcenter = (item.costcenter == cost_center and cost_center is not None)
        same_project = (
            project_assignment and item.project_assignment
            and item.project_assignment.project == project_assignment.project
        )

        if same_costcenter or same_project:
            msg = f"A timesheet for this {'project' if project_assignment else 'cost center'} already exists on {date_obj}."
            return _error_response(request, msg, 400)

    # 🔟 Save entry
    if existing_entry:
        existing_entry.project_assignment = project_assignment
        existing_entry.costcenter = cost_center
        existing_entry.activity = activity
        existing_entry.work_location = work_location
        existing_entry.wrk_hours = hours_worked
        existing_entry.description = request.POST.get('description', '').strip()
        existing_entry.save()
        created = False
        item = existing_entry
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

    # ✅ Recalculate totals and delayed status
    hdr.recalc_totals()
    hdr.check_delayed_status()

    # 🔟 Prepare success response
    response_data = {
        'status': 'success',
        'message': f"Timesheet for {date_obj} {'submitted' if created else 'updated'} successfully.",
        'date': date_obj.strftime('%Y-%m-%d'),
        'entry': {
            'id': item.pk,
            'date': item.wrk_date.strftime('%Y-%m-%d'),
            'hours_worked': item.wrk_hours,
            'project_id': project_assignment.project.project_id if project_assignment else None,
            'project_name': project_assignment.project.project_name if project_assignment else (str(cost_center) if cost_center else None),
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

def get_timesheet_day_data(request):
    """
    Fetch and return all necessary data for a given day's timesheet entry screen:
      - Employee's timesheet entries for that day
      - Available projects and cost center options
      - Leave status for the day
      - Project end date and remaining working days
    """
    employee = request.user.employee_profile
    date_str = request.GET.get("date")
    date_obj = parse_date(date_str)

    # ❌ Invalid date check
    if not date_obj:
        return JsonResponse({"error": "Invalid date"}, status=400)

    # ✅ 1. Check if the employee is on approved leave that day
    on_leave = LeaveRequest.objects.filter(
        employee_master=employee,
        status="Approved",
        start_date__lte=date_obj,
        end_date__gte=date_obj
    ).only("id").exists()  # .only("id") for efficiency

    # ✅ 2. Get all timesheet entries for that date (with related fields to avoid N+1 queries)
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

    # ✅ 3. Build entries list for frontend
    entry_list = []
    for item in items_qs:
        if item.project_assignment and item.project_assignment.project:
            # Entry linked to a project
            proj_obj = item.project_assignment.project
            project_name = proj_obj.project_name
            project_id = proj_obj.project_id
            project_assignment_id = item.project_assignment.pk
            is_costcenter = False
        else:
            # Entry linked to a cost center
            costcenter = item.costcenter
            project_name = costcenter.costcenter_name if costcenter else "Cost Center"
            project_id = costcenter.costcenter_id if costcenter else None
            project_assignment_id = f"COSTCENTER-{project_id}" if project_id else None
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

    # ✅ 4. Fetch active project assignments for that day
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
        # Calculate remaining working days (if project has an end date)
        remaining_days = None
        if pa.end_date:
            remaining_days = calculate_remaining_working_days(employee, date_obj, pa.end_date)
            remaining_days = max(0, remaining_days)  # Prevent negative values

        client_alias = pa.project.client.client_alias if pa.project and pa.project.client else ""

        projects_list.append({
            "projectAssignmentId": pa.pk,
            "project_id": pa.project.project_id if pa.project else None,
            "name": pa.project.project_name if pa.project else "",
            "client_alias": client_alias,
            "is_costcenter": False,
            "selected": False,
            "assignment_start_date": pa.start_date,   # 🔹 NEW
            "assignment_end_date": pa.end_date,       # 🔹 NEW
            "remaining_days": remaining_days
        })

    # ✅ 5. Add cost center as first option if exists
    if employee.cost_center:
        projects_list.insert(0, {
            "projectAssignmentId": f"COSTCENTER-{employee.cost_center.costcenter_id}",
            "project_id": employee.cost_center.costcenter_id,
            "name": employee.cost_center.costcenter_name,
            "client_alias": "Cost Center",
            "is_costcenter": True,
            "selected": not has_projects,  # Preselect cost center if no projects available
            "assignment_start_date": None,   # 🔹 NEW
            "assignment_end_date": None ,      # 🔹 NEW
            "remaining_days": None

        })

    # ✅ 6. Get first project entry’s end date & remaining working days
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

    # ✅ 7. Return data as JSON
    return JsonResponse({
        "entries": entry_list,
        "is_leave_day": on_leave,
        "projects": projects_list,
        "remaining_working_days": remaining_working_days,
        "project_end_date": project_end_date
    }, encoder=DjangoJSONEncoder)


from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date




# @login_required
# @require_POST
# def copy_timesheet_entries(request):
#     """
#     Copy selected TimesheetItem entries to multiple target dates for the current employee.

#     Rules:
#     - Target date cannot be in the future.
#     - Target date cannot be an approved leave day.
#     - Each date may have max 12 hours total.
#     - Only one entry per (costcenter, date) OR (project_assignment, date).
#     - Project assignments must be valid on the target date.
#     - Prevents creating duplicates (bulk checked for efficiency).

#     Optimizations:
#     - Flattened date parsing.
#     - Preloads all existing TimesheetItems for target dates in a single query.
#     - Groups validation and duplication checks to avoid repeated DB hits.
#     """
#     employee = request.user.employee_profile

#     # Parse POST data: entry_ids[] and target_dates[]
#     item_ids = request.POST.getlist("entry_ids[]", [])
#     raw_target_dates = request.POST.getlist("target_dates[]", [])

#     # Flatten comma-separated dates
#     target_dates = [d.strip() for td in raw_target_dates for d in td.split(",") if d.strip()]

#     if not item_ids or not target_dates:
#         return JsonResponse({"error": "Entries and target dates are required"}, status=400)

#     # Fetch selected timesheet items for this employee
#     items = list(
#         TimesheetItem.objects.filter(
#             id__in=item_ids,
#             hdr__employee=employee
#         ).select_related(
#             "hdr", "project_assignment", "project",
#             "costcenter", "activity", "work_location"
#         )
#     )

#     if not items:
#         return JsonResponse({"error": "No valid entries found"}, status=404)

#     today = date.today()
#     parsed_dates = {}

#     # Pre-parse dates and filter invalid ones early
#     skipped_details = []
#     for td in target_dates:
#         date_obj = parse_date(td)
#         if not date_obj:
#             skipped_details.append({"date": td, "reason": "Invalid date"})
#         elif date_obj > today:
#             skipped_details.append({"date": td, "reason": "Cannot copy to future dates"})
#         else:
#             parsed_dates[td] = date_obj

#     if not parsed_dates:
#         return JsonResponse({"error": "No valid target dates to process"}, status=400)

#     # Pre-fetch leaves for all relevant dates
#     leave_dates = set(
#         LeaveRequest.objects.filter(
#             employee_master=employee,
#             status="Approved"
#         ).filter(
#             Q(start_date__lte=max(parsed_dates.values())) &
#             Q(end_date__gte=min(parsed_dates.values()))
#         ).values_list("start_date", "end_date")
#     )

#     # Expand leave date ranges into a set for faster lookup
#     leave_days = set()
#     for start, end in leave_dates:
#         leave_days.update([start + timedelta(days=i) for i in range((end - start).days + 1)])

#     # Pre-fetch all existing entries for target dates (avoid .exists() per loop)
#     existing_entries = TimesheetItem.objects.filter(
#         hdr__employee=employee,
#         wrk_date__in=parsed_dates.values()
#     ).select_related("project_assignment", "costcenter")

#     # Map: date_obj -> {(project_assignment_id, costcenter_id): wrk_hours}
#     existing_map = {}
#     for entry in existing_entries:
#         key = (entry.project_assignment_id, entry.costcenter_id)
#         existing_map.setdefault(entry.wrk_date, {})[key] = entry.wrk_hours

#     copied_dates = []

#     for td, date_obj in parsed_dates.items():
#         if date_obj in leave_days:
#             skipped_details.append({"date": td, "reason": "Approved leave"})
#             continue

#         # Get total hours already logged for the day
#         day_hours = sum(existing_map.get(date_obj, {}).values())

#         entries_copied = 0

#         with transaction.atomic():
#             # Find week boundaries for header
#             week_start = date_obj - timedelta(days=date_obj.weekday())
#             week_end = week_start + timedelta(days=6)

#             hdr, _ = TimesheetHdr.objects.get_or_create(
#                 employee=employee,
#                 week_start=week_start,
#                 week_end=week_end,
#                 defaults={"is_approved": False}
#             )

#             for item in items:
#                 key = (item.project_assignment_id, item.costcenter_id)

#                 # Skip if duplicate for this date
#                 if key in existing_map.get(date_obj, {}):
#                     reason = (f"Project '{item.project_assignment.project.project_name}' already exists"
#                               if item.project_assignment else "Cost center entry already exists")
#                     skipped_details.append({"date": td, "reason": reason})
#                     continue

#                 # Validate project date range
#                 if item.project_assignment:
#                     valid_project = AssignProject.objects.filter(
#                         pk=item.project_assignment.pk,
#                         start_date__lte=date_obj
#                     ).filter(
#                         Q(end_date__gte=date_obj) | Q(end_date__isnull=True)
#                     ).exists()
#                     if not valid_project:
#                         skipped_details.append({
#                             "date": td,
#                             "reason": f"Project '{item.project_assignment.project.project_name}' invalid for this date"
#                         })
#                         continue

#                 # Check daily 12h limit
#                 if day_hours + item.wrk_hours > 12:
#                     skipped_details.append({"date": td, "reason": "Copying would exceed 12h limit"})
#                     continue

#                 # Create new item
#                 TimesheetItem.objects.create(
#                     hdr=hdr,
#                     wrk_date=date_obj,
#                     project_assignment=item.project_assignment,
#                     costcenter=item.costcenter,
#                     activity=item.activity,
#                     work_location=item.work_location,
#                     wrk_hours=item.wrk_hours,
#                     description=item.description or ""
#                 )

#                 # Update tracking structures
#                 entries_copied += 1
#                 day_hours += item.wrk_hours
#                 existing_map.setdefault(date_obj, {})[key] = item.wrk_hours

#         if entries_copied > 0:
#             copied_dates.append(td)
#         else:
#             skipped_details.append({"date": td, "reason": "No entries copied for this date"})

#     # Group skip reasons by date
#     skipped_summary = {}
#     for s in skipped_details:
#         skipped_summary.setdefault(s["date"], []).append(s["reason"])

#     return JsonResponse({
#         "status": "success",
#         "copied": copied_dates,
#         "skipped": skipped_summary,
#         "message": f"Copied to {len(copied_dates)} date(s). Skipped {len(skipped_summary)} date(s)."
#     })
import datetime
from datetime import timedelta, date
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.dateparse import parse_date

# Assuming you have imported necessary modules and models
from django.utils.dateparse import parse_date
from datetime import date, timedelta
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Make sure you have your get_all_holidays and any necessary cache/model imports
# from your_app.utils import get_all_holidays, holidays_cache
# from your_app.models import TimesheetItem, TimesheetHdr, LeaveRequest, AssignProject

@require_POST
def copy_timesheet_entries(request):
    """
    Copy selected TimesheetItem entries to multiple target dates,
    allowing copying to weekends and holidays with overlapping approved leave.
    """
    employee = request.user.employee_profile

    # Fetch holidays for the employee's country/state
    holidays_cache = {} # Placeholder for your actual cache
    emp_holidays = get_all_holidays(employee, holidays_cache)

    item_ids = request.POST.getlist("entry_ids[]", [])
    raw_target_dates = request.POST.getlist("target_dates[]", [])
    target_dates = [d.strip() for td in raw_target_dates for d in td.split(",") if d.strip()]

    if not item_ids or not target_dates:
        return JsonResponse({"error": "Entries and target dates are required"}, status=400)

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

    today = date.today()
    parsed_dates = {}
    skipped_details = {}

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

    leave_dates = set(
        LeaveRequest.objects.filter(
            employee_master=employee,
            status="Approved"
        ).filter(
            Q(start_date__lte=max(parsed_dates.values())) &
            Q(end_date__gte=min(parsed_dates.values()))
        ).values_list("start_date", "end_date")
    )

    leave_days = set()
    for start, end in leave_dates:
        leave_days.update([start + timedelta(days=i) for i in range((end - start).days + 1)])

    existing_entries = TimesheetItem.objects.filter(
        hdr__employee=employee,
        wrk_date__in=parsed_dates.values()
    ).select_related("project_assignment", "costcenter")

    existing_map = {}
    for entry in existing_entries:
        key = (entry.project_assignment_id, entry.costcenter_id)
        existing_map.setdefault(entry.wrk_date, {})[key] = entry.wrk_hours

    copied_dates = []

    for td, date_obj in parsed_dates.items():
        is_weekend = date_obj.weekday() >= 5
        is_holiday = date_obj in emp_holidays  # Now correctly checks if the date is a holiday

        if date_obj in leave_days and not is_weekend and not is_holiday:
            skipped_details.setdefault(td, []).append("Approved leave on a working day")
            continue

        day_hours = sum(existing_map.get(date_obj, {}).values())
        entries_copied = 0

        with transaction.atomic():
            week_start = date_obj - timedelta(days=date_obj.weekday())
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

                if day_hours + item.wrk_hours > 12:
                    skipped_details.setdefault(td, []).append("Copying would exceed 12h limit")
                    continue

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
            copied_dates.append(td)
        else:
            skipped_details.setdefault(td, []).append("No entries copied for this date")

    return JsonResponse({
        "status": "success",
        "copied": copied_dates,
        "skipped": skipped_details,
        "message": f"Copied to {len(copied_dates)} date(s). Skipped {len(skipped_details)} date(s)."
    })

from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.shortcuts import render
from django.contrib import messages


def get_week_start_end(year: int, week: int):
    """Return Monday and Sunday dates for a given ISO week/year."""
    try:
        first_day = datetime.strptime(f'{year} {week} 1', '%G %V %u').date()
        return first_day, first_day + timedelta(days=6)
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



from datetime import timedelta

from datetime import timedelta

from datetime import timedelta

def calculate_timesheet_stats(emp, ts_hdr, week_start, leave_days, holidays_cache):
    """
    Calculates and returns a dictionary of all timesheet stats for an employee,
    including a detailed breakdown of entries for each day.
    """
    # --- 1. Base setup ---
    has_timesheets = ts_hdr is not None
    is_fully_approved = ts_hdr.is_approved if has_timesheets else False
    timesheet_items = list(ts_hdr.timesheet_items.all()) if has_timesheets else []

    # Working hours baseline
    min_daily_hours = getattr(emp.country, 'working_hours', 9) or 9

    # Leave / holiday caches for this employee
    leave_dates = leave_days.get(emp.id, set())
    emp_holidays = get_all_holidays(emp, holidays_cache)

    num_leaves = len(leave_dates)
    num_holidays = len(emp_holidays)

    # --- 2. Aggregate hours (Retrieve from database) ---
    if has_timesheets:
        weekday_hours = ts_hdr.tot_hrs_wrk
        total_holiday_hours = ts_hdr.tot_hol_hrs
        total_leave_hours = ts_hdr.tot_lev_hrs
    else:
        weekday_hours = 0
        total_holiday_hours = 0
        total_leave_hours = 0
    
    # Weekend hours are not stored, so we sum them manually from the items
    weekend_hours = sum(i.wrk_hours for i in timesheet_items if i.wrk_date.weekday() >= 5)

    detailed_entries = []

    # --- 3. Build day-by-day breakdown for display ---
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        is_holiday = current_date in emp_holidays
        is_leave = current_date in leave_dates

        entries_for_day = [item for item in timesheet_items if item.wrk_date == current_date]
        entered_hours = sum(e.wrk_hours for e in entries_for_day)

        # Logic for what hours to display for each day
        day_total_hours = entered_hours
        status_message = "No entries made."
        holiday_name = emp_holidays.get(current_date)

        if is_holiday:
            # Display logic for holidays: show credited hours
            if entered_hours == 0:
                day_total_hours = min_daily_hours
            elif entered_hours < min_daily_hours:
                day_total_hours = min_daily_hours
            else:
                day_total_hours = entered_hours
            status_message = f"{holiday_name or 'Holiday'}"
        elif is_leave:
            # Display logic for leave days
            day_total_hours = min_daily_hours
            status_message = "Leave Day"
        else:
            # Normal workday display
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
            'status_message': status_message,
            'holiday_name': holiday_name if is_holiday else None,
            'timesheet_entries': [
                {
                    'project_name': e.project.project_name if e.project else None,
                    'costcenter_name': e.costcenter.costcenter_name if e.costcenter else None,
                    'description': e.description,
                    'hours': e.wrk_hours,
                    'activity': e.activity.act_name if e.activity else 'N/A',
                    'work_location': e.work_location.loc_name if e.work_location else 'N/A'
                } for e in entries_for_day
            ]
        })

    # --- 4. Final total for display ---
    total_hours = weekday_hours + weekend_hours + total_leave_hours + total_holiday_hours

    # --- 5. Approval logic ---
    can_approve = has_timesheets
    if can_approve:
        for i in range(5):  # only Mon–Fri
            current_date = week_start + timedelta(days=i)
            entered_hours_for_day = sum(item.wrk_hours for item in timesheet_items if item.wrk_date == current_date)

            day_is_complete = (
                entered_hours_for_day >= min_daily_hours or 
                current_date in leave_dates or 
                current_date in emp_holidays
            )
            if not day_is_complete:
                can_approve = False
                break

    print(emp.id, emp.first_name, "<<<   number of leaves", len(leave_dates))
    print(emp.id, emp.first_name, "<<<< holiday count", len(emp_holidays))
    print(emp.id, emp.first_name, "<<<< total hours", total_hours)


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
def build_weeks_list(num_weeks=8):
    """Return a list of `num_weeks` week data for filters, starting from the previous week."""
    today = datetime.now().date()
    # Find the Monday of the current week, then subtract one week to get the previous week's Monday
    previous_monday = today - timedelta(days=today.weekday()) - timedelta(weeks=1)
    weeks_list = []
    for i in range(num_weeks):
        wk_start = previous_monday - timedelta(weeks=i)
        wk_end = wk_start + timedelta(days=6)
        week_num = wk_start.isocalendar()[1]
        year_num = wk_start.isocalendar()[0]
        label = f"Week {week_num} ({wk_start.strftime('%d %b')} - {wk_end.strftime('%d %b')})"
        weeks_list.append({'week': week_num, 'label': label, 'year': year_num})
    return weeks_list



from django.shortcuts import redirect
from django.http import HttpRequest
from django.contrib import messages

def timesheet_unapprove(request: HttpRequest, tsheet_id: int):
    try:
        hdr = TimesheetHdr.objects.get(pk=tsheet_id)
        if hdr.is_approved:
            hdr.is_approved = False
            hdr.save()
            messages.success(request, f"Timesheet for {hdr.employee.first_name} set to 'Pending Approval'.")
        else:
            messages.warning(request, "Timesheet is already pending approval.")
    except TimesheetHdr.DoesNotExist:
        messages.error(request, "Timesheet not found.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    # Check for a 'next' URL parameter and redirect there
    next_url = request.GET.get('next', 'timesheet_approval_list')
    return redirect(next_url)

from django.db.models import Prefetch, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.contrib import messages

# Assume all helper functions (get_week_start_end, build_leave_days,
# build_holidays_cache, calculate_timesheet_stats, build_weeks_list) are available.

@login_required
def timesheet_approval_list(request):
    """
    Manages the timesheet approval list for a manager.
    """
    try:
        manager = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

    # --- 1. Get and Validate User Inputs ---
    selected_year = int(request.GET.get('year', datetime.now().year))
    today = datetime.now().date()
    previous_week_start = today - timedelta(weeks=1)
    previous_week_num = previous_week_start.isocalendar()[1]
    selected_week = int(request.GET.get('week', previous_week_num))

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'All')

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

    # --- 2. Get Subordinates ---
    subordinates = Employees.objects.filter(manager=manager).select_related(
        'country', 'state'
    ).order_by('first_name')

    if search_query:
        subordinates = subordinates.filter(
            Q(employee_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # --- 3. Prefetch Timesheet Headers ---
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

    # --- 4. Build Leave & Holiday Caches ---
    employee_ids = [emp.id for emp in subordinates]
    leave_days = build_leave_days(employee_ids, week_start, week_end)

    holidays_cache = build_holidays_cache(subordinates, week_start, week_end)

    # --- 5. Build Timesheet Data for Each Employee ---
    timesheet_data = []
    for emp in subordinates:
        ts_hdr = emp.timesheet_header_list[0] if emp.timesheet_header_list else None
        stats = calculate_timesheet_stats(emp, ts_hdr, week_start, leave_days, holidays_cache)
        timesheet_data.append(stats)

    # --- 6. Apply Status Filter ---
    if status_filter == 'Approved':
        timesheet_data = [d for d in timesheet_data if d.get('is_fully_approved')]
    elif status_filter == 'Pending':
        # Pending means they have a timesheet, are not fully approved, but can be
        timesheet_data = [d for d in timesheet_data if d.get('has_timesheets') and not d.get('is_fully_approved') and d.get('can_approve')]
    elif status_filter == 'Incomplete':
        # Incomplete means they have a timesheet, are not approved, and cannot be approved (because of missing data)
        timesheet_data = [d for d in timesheet_data if d.get('has_timesheets') and not d.get('is_fully_approved') and not d.get('can_approve')]
    elif status_filter == 'No Data':
        timesheet_data = [d for d in timesheet_data if not d.get('has_timesheets')]

    # --- 7. Context & Render ---
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

@login_required
@require_POST
def approve_timesheet(request):
    """Approve a single employee's weekly timesheet."""
    print("Hittting the single approval view ")
    emp_id = request.POST.get('employee_id')
    year = request.POST.get('year')
    week = request.POST.get('week')
    print(emp_id,"-",year,"-",week)

    try:
        week_start = date.fromisocalendar(int(year), int(week), 1)  # Monday
        week_end = date.fromisocalendar(int(year), int(week), 7)    # Sunday

        print(week_start,"-",week_end)

        hdr = TimesheetHdr.objects.get(
            employee_id=emp_id,
            week_start=week_start,
            week_end=week_end
        )
        print(hdr)
        if hdr.is_approved:
            return JsonResponse({'success': False, 'message': 'Already approved.'})

        hdr.is_approved = True
        hdr.approved_by = request.user.employee_profile  # FIXED
        hdr.approved_date = timezone.now()
        hdr.save()

        return JsonResponse({"success": True, "message": "Timesheet approved."})


    except TimesheetHdr.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Timesheet not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def approve_selected_timesheets(request):
    """Approve multiple employees' weekly timesheets at once."""
    ids = request.POST.getlist('ids[]')  # ["empID-year-week", ...]
    approved = []
    errors = []

    for composite_id in ids:
        try:
            emp_id, year, week = composite_id.split('-')
            week_start = date.fromisocalendar(int(year), int(week), 1)
            week_end = date.fromisocalendar(int(year), int(week), 7)

            hdr = TimesheetHdr.objects.get(
                employee_id=emp_id,
                week_start=week_start,
                week_end=week_end
            )

            if not hdr.is_approved:
                hdr.is_approved = True
                hdr.approved_by = request.user.employee_profile  # FIXED
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



# The corrected calculate_timesheet_stats must be imported or in the same file.
# This function is crucial as it provides the structured detailed_entries list.
# from .timesheet_app.views import calculate_timesheet_stats

from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required

@login_required
def timesheet_week_details(request):
    try:
        emp_id = int(request.GET.get('employee_id'))
        year = int(request.GET.get('year'))
        week = int(request.GET.get('week'))

        week_start = datetime.fromisocalendar(year, week, 1).date()
        week_end = week_start + timedelta(days=6)

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

        # 🔹 Remove weekends (Sat=5, Sun=6) if they have no items
        filtered_entries = []
        for e in entries:
            date = datetime.strptime(e['date'], "%Y-%m-%d").date()
            is_weekend = date.weekday() in [5, 6]  # Sat=5, Sun=6

            if is_weekend and not e.get('items'):  
                # Skip weekends with no timesheet items
                continue
            filtered_entries.append(e)

        return JsonResponse({'success': True, 'entries': filtered_entries})

    except Employees.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
