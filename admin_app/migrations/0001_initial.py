# Generated by Django 3.2 on 2025-03-11 09:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dep_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Employees',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emp_id', models.CharField(max_length=10, unique=True)),
                ('emp_fname', models.CharField(max_length=50, verbose_name='Employee First Name')),
                ('emp_mname', models.CharField(max_length=50, verbose_name='Employee Middle Name')),
                ('emp_lname', models.CharField(max_length=50, verbose_name='Employee Last Name')),
                ('emp_email', models.EmailField(max_length=254, unique=True, verbose_name='Company Email')),
                ('emp_pemail', models.EmailField(max_length=254, verbose_name='Personal Email')),
                ('emp_mob_ph', models.CharField(max_length=15)),
                ('emp_off_ph', models.CharField(max_length=15)),
                ('emp_home_ph', models.CharField(max_length=15)),
                ('emp_val_from', models.DateField()),
                ('emp_val_to', models.DateField()),
                ('emp_addr', models.CharField(max_length=150, null=True)),
                ('emp_home_street', models.CharField(max_length=80)),
                ('emp_home_city', models.CharField(max_length=80)),
                ('pincode', models.CharField(max_length=10, null=True)),
                ('designation', models.CharField(max_length=100)),
                ('employee_status', models.CharField(max_length=10)),
                ('emp_cp_name', models.CharField(max_length=100)),
                ('emp_cp_ph', models.CharField(max_length=15)),
                ('emp_cp_email', models.EmailField(max_length=254)),
                ('emp_cp_relation', models.CharField(max_length=100)),
                ('emp_base', models.DecimalField(decimal_places=2, max_digits=10)),
                ('emp_resume', models.FileField(upload_to='documents/')),
                ('emp_certif', models.FileField(upload_to='documents/')),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('is_delete', models.BooleanField(default=False)),
                ('floating_holidays_balance', models.IntegerField(default=2)),
                ('floating_holidays_used', models.IntegerField(default=0)),
                ('emp_total_leaves', models.PositiveIntegerField(default=15)),
                ('emp_used_leaves', models.PositiveIntegerField(default=0)),
                ('emp_password', models.CharField(blank=True, max_length=128, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.country')),
                ('dep', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.department')),
                ('employee_manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees_managed', to='admin_app.employees')),
            ],
        ),
        migrations.CreateModel(
            name='FloatingHoliday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('year', models.IntegerField(default=2025)),
            ],
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('day', models.CharField(max_length=50, null=True)),
                ('year', models.IntegerField(default=2025)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('role_id', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                ('role_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Salutation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sal_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='state',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='admin_app.country')),
            ],
        ),
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('leave_type', models.CharField(choices=[('Floating Leave', 'Floating Leave'), ('Casual Leave', 'Casual Leave')], default='Casual Leave', max_length=20)),
                ('status', models.CharField(default='Pending', max_length=20)),
                ('leave_days', models.PositiveIntegerField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_leaves', to=settings.AUTH_USER_MODEL)),
                ('employee_master', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='leave_requests', to='admin_app.employees')),
                ('employee_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Leave Request',
                'verbose_name_plural': 'Leave Requests',
            },
        ),
        migrations.AddField(
            model_name='employees',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.role'),
        ),
        migrations.AddField(
            model_name='employees',
            name='sal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.salutation'),
        ),
        migrations.AddField(
            model_name='employees',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.state'),
        ),
        migrations.AddField(
            model_name='employees',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
