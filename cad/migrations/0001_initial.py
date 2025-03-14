# Generated by Django 5.1.5 on 2025-01-24 19:00

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SomeDetails",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(editable=False, unique=True)),
                ("logo", models.ImageField(upload_to="logo/")),
                ("right_image", models.ImageField(upload_to="right-image/")),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
