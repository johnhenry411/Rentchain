# Generated by Django 3.0.5 on 2024-12-16 21:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('property_app', '0037_auto_20241217_0008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='landlord',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='landlord_contracts', to=settings.AUTH_USER_MODEL),
        ),
    ]
