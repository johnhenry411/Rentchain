# Generated by Django 3.0.5 on 2024-12-16 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property_app', '0034_auto_20241216_2247'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
