# Generated by Django 3.2 on 2025-05-21 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0029_alter_holiday_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='employees',
            name='joining_bonus',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
    ]
