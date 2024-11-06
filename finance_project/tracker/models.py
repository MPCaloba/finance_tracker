from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .managers import TransactionQuerySet

from decimal import Decimal


class User(AbstractUser):
    pass


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('normal', 'Normal'),
        ('investment', 'Investment'),
        ('virtual_tax', 'Virtual Tax'),
    ]

    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='normal')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

    def calculate_balance(self):
        """
        A method to calculate the balance based on related transactions.
        This will sum up incoming transactions and subtract outgoing ones.
        """
        incoming = Decimal(self.transactions_to.filter(type='income').aggregate(total=models.Sum('amount'))['total'] or 0)
        outgoing = Decimal(self.transactions_from.filter(type='expense').aggregate(total=models.Sum('amount'))['total'] or 0)
        internal_in = Decimal(self.transactions_to.filter(type='internal').aggregate(total=models.Sum('amount'))['total'] or 0)
        internal_out = Decimal(self.transactions_from.filter(type='internal').aggregate(total=models.Sum('amount'))['total'] or 0)

        self.balance = incoming - outgoing + internal_in - internal_out
        self.save()


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('internal', 'Internal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    
    origin_account = models.ForeignKey(Account, related_name='transactions_from', on_delete=models.CASCADE, blank=True, null=True)
    destination_account = models.ForeignKey(Account, related_name='transactions_to', on_delete=models.CASCADE, blank=True, null=True)
    
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    objects = TransactionQuerySet.as_manager()

    def __str__(self):
        return f'{self.type.capitalize()} - {self.amount} on {self.date}'

    def save(self, *args, **kwargs):
        """
        Override the save method to handle balance adjustments automatically when a transaction is created.
        """
        super().save(*args, **kwargs)
        self.adjust_account_balances()

    def adjust_account_balances(self):
        """
        Adjusts the balances of the involved accounts based on the transaction type.
        For incoming transactions, apply tax and fee handling.
        """
        # Tax handling for incoming transactions
        if self.type == 'income':
            tax_amount = (self.tax_percentage or Decimal(0)) * self.amount / Decimal(100)

            self.destination_account.balance += self.amount
            self.destination_account.save()
            
            virtual_tax_account = Account.objects.get(account_type='virtual_tax')
            virtual_tax_account.balance += tax_amount
            virtual_tax_account.save()

        elif self.type == 'internal':
            self.origin_account.calculate_balance()
            self.destination_account.calculate_balance()

        elif self.type == 'expense':
            self.origin_account.calculate_balance()

        # Fee handling
        if self.fee > 0:
            self.create_fee_transaction()

    def create_fee_transaction(self):
        """
        Creates a separate expense transaction to record the fee as an expense.
        """
        fee_transaction = Transaction.objects.create(
            type='expense',
            amount=self.fee,
            origin_account=self.origin_account,
            description=f"Fee for transaction {self.id}: {self.description}",
            date=self.date
        )

        Expense.objects.create(
        category='fees',
        amount=self.fee,
        account=self.origin_account,
        transaction=fee_transaction,
        date=self.date,
        )

        fee_transaction.save()

    class Meta:
        ordering = ['-date']


class Income(models.Model):
    INCOME_CATEGORIES = [
        ('salary', 'Salary'),
        ('interest', 'Interest'),
        ('parents', 'Parents'),
        ('birthday', 'Birthday'),
        ('iva_reimbursement', 'IVA_Reimbursement'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=INCOME_CATEGORIES)
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    
    transaction = models.OneToOneField('Transaction', on_delete=models.CASCADE, related_name='income_transaction')
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='income_account')

    def __str__(self):
        return f'{self.date} - {self.get_category_display()} income - {self.amount}€'


class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('accessories', 'Accessories'),
        ('books', 'Books'),
        ('car', 'Car'),
        ('cash', 'Cash'),
        ('clothing', 'Clothing'),
        ('coffees & snacks', 'Coffees & Snacks'),
        ('dining out', 'Dining Out'),
        ('entertainment', 'Entertainment'),
        ('fees', 'Fees'),
        ('gifts', 'Gifts'),
        ('groceries', 'Groceries'),
        ('gym', 'Gym'),
        ('haircut', 'Haircut'),
        ('housing', 'Housing'),
        ('insurance', 'Insurance'),
        ('healthcare', 'Healthcare'),
        ('miscellaneous', 'Miscellaneous'),
        ('office', 'Office'),
        ('personal development', 'Personal Development'),
        ('petrol', 'Petrol'),
        ('pharmacy', 'Pharmacy'),
        ('phone', 'Phone'),
        ('rent', 'Rent'),
        ('sports', 'Sports'),
        ('supplements', 'Supplements'),
        ('tattoo', 'Tattoo'),
        ('taxes', 'Taxes'),
        ('tech', 'Tech'),
        ('transportation', 'Transportation'),
        ('utilities', 'Utilities'),
        ('vacation', 'Vacation'),
    ]

    SOURCES = [
        ('personal', 'Personal'),
        ('shared', 'Shared'),
    ]

    TYPES = [
        ('fixed', 'Fixed'),
        ('variable', 'Variable'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    
    source = models.CharField(max_length=50, choices=SOURCES)
    fixed_or_variable = models.CharField(max_length=50, choices=TYPES)

    transaction = models.OneToOneField('Transaction', on_delete=models.CASCADE, related_name='expense_transaction')
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='expense_account')

    def __str__(self):
        return f'{self.date} - {self.get_category_display()} expense - {self.amount}€'


class Tax(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)

    transaction = models.OneToOneField('Transaction', on_delete=models.CASCADE, related_name='tax_transaction')
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='tax_account')

    def __str__(self):
        return f'Tax - {self.amount} for {self.year}'
