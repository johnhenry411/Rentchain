# Generated by Django 3.0.5 on 2024-12-09 07:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('property_app', '0014_auto_20241209_1046'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='property',
            name='image',
        ),
    ]
