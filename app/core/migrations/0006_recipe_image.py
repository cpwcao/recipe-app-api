# Generated by Django 3.2.25 on 2025-03-31 02:07

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_recipe_status_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(null=True, upload_to=core.models.recipe_image_file_path),
        ),
    ]
