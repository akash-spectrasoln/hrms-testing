# Generated by Django 5.1.4 on 2025-03-26 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0006_alter_employees_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='employees',
            name='resignation_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
