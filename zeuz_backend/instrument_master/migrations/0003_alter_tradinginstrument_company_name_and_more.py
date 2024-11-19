# Generated by Django 5.1.2 on 2024-11-15 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instrument_master", "0002_alter_tradinginstrument_lot_size"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tradinginstrument",
            name="company_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="tradinginstrument",
            name="expiry_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="tradinginstrument",
            name="instrument_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="tradinginstrument",
            name="lot_size",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="tradinginstrument",
            name="script_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="tradinginstrument",
            name="series",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name="tradinginstrument",
            name="ticker",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
