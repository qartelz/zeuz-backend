# Generated by Django 5.1.2 on 2024-11-15 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instrument_master", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tradinginstrument",
            name="lot_size",
            field=models.FloatField(),
        ),
    ]