# Generated by Django 5.1.2 on 2024-12-21 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "instrument_master",
            "0005_tradinginstrument_instrument__exchang_000a17_idx_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadedfile",
            name="error_message",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="uploadedfile",
            name="status",
            field=models.CharField(default="uploaded", max_length=50),
        ),
    ]
