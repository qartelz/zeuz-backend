# Generated by Django 5.1.2 on 2024-12-23 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trades", "0012_limitorder"),
    ]

    operations = [
        migrations.AddField(
            model_name="limitorder",
            name="status",
            field=models.CharField(default="NOT EXECUTED", max_length=255, null=True),
        ),
    ]
