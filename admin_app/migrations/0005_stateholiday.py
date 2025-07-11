# Generated by Django 3.2 on 2025-06-17 09:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0004_alter_employees_base_salary'),
    ]

    operations = [
        migrations.CreateModel(
            name='StateHoliday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=100)),
                ('year', models.IntegerField(default=2025)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.country')),
            ],
        ),
    ]
