# Generated by Django 5.1.2 on 2024-10-31 20:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_folder_uploadedfile_folder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='folder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.folder'),
        ),
    ]