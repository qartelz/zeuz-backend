# Generated by Django 5.1.2 on 2024-11-21 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0006_alter_beetlecoins_used_coins"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beetlecoins",
            name="coins",
            field=models.DecimalField(
                decimal_places=2, default=1000000.0, max_digits=10
            ),
        ),
        migrations.AlterField(
            model_name="beetlecoins",
            name="used_coins",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]