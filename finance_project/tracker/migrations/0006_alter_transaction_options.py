# Generated by Django 4.2 on 2024-11-06 10:32

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0005_transaction_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="transaction",
            options={"ordering": ["-date"]},
        ),
    ]
