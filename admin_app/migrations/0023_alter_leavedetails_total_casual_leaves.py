# Generated by Django 3.2 on 2025-07-07 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0022_rename_total_leaves_leavedetails_total_casual_leaves'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leavedetails',
            name='total_casual_leaves',
            field=models.IntegerField(default=12, null=True),
        ),
    ]
