# Generated by Django 3.0.5 on 2024-12-19 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property_app', '0042_auto_20241217_1220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
