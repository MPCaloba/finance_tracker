import random
from faker import Faker
from decimal import Decimal
from django.core.management.base import BaseCommand
from tracker.models import Account, Income, Expense, Transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Generates test transactions for incomes and expenses"

    def handle(self, *args, **options):
        fake = Faker()

        # Get accounts from the database
        accounts = Account.objects.all()

        if not accounts.exists():
            self.stdout.write(self.style.ERROR("No accounts found. Please create accounts first."))
            return

        # Generate Income Transactions
        for _ in range(10):
            account = random.choice(accounts)
            amount = Decimal(random.uniform(50, 2500))
            date = timezone.make_aware(fake.date_time_between(start_date="-1y", end_date="now"))

            Transaction.objects.create(
                type='income',
                amount=amount,
                date=date,
                origin_account=None,
                destination_account=account,
                description=f'Income of {amount:.2f}€'
            )
            Income.objects.create(
                amount=amount,
                category=random.choice(['salary', 'interest', 'parents', 'birthday']),
                date=date,
                transaction=Transaction.objects.last(),
                account=account
            )

        # Generate Expense Transactions
        for _ in range(20):
            account = random.choice(accounts)
            amount = Decimal(random.uniform(5, 250))
            date = timezone.make_aware(fake.date_time_between(start_date="-1y", end_date="now"))

            Transaction.objects.create(
                type='expense',
                amount=amount,
                date=date,
                origin_account=account,
                destination_account=None,
                description=f'Expense of {amount:.2f}€'
            )
            Expense.objects.create(
                amount=amount,
                category=random.choice([
                    'accessories', 'books', 'car', 'clothing', 'groceries', 
                    'dining out', 'transportation', 'utilities', 'vacation',
                    'petrol', 'healthcare', 'phone', 'personal development'
                ]),
                date=date,
                transaction=Transaction.objects.last(),
                account=account,
                source=random.choice(['personal', 'shared']),
                fixed_or_variable=random.choice(['fixed', 'variable'])
            )

        self.stdout.write(self.style.SUCCESS("Test transactions generated successfully."))
