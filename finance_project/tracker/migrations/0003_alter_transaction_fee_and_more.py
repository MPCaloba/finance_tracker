# Generated by Django 4.2 on 2024-10-24 09:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0002_account_transaction_tax_income_expense"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="fee",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0.0, max_digits=8, null=True
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="origin_account",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions_from",
                to="tracker.account",
            ),
        ),
    ]
