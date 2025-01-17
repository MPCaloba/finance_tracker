from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.timezone import now
from .managers import TransactionQuerySet


class User(AbstractUser):
    pass


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('normal', 'Normal'),
        ('investment', 'Investment'),
        ('virtual_tax', 'Virtual Tax'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='normal')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class AccountBalanceHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='balance_history')
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-timestamp']
        unique_together = ('account', 'timestamp')

    def __str__(self):
        return f"{self.account.name} - {self.balance} at {self.timestamp}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('internal', 'Internal'),
        ('tax', 'Tax'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    description = models.TextField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    
    origin_account = models.ForeignKey(Account, related_name='transactions_from', on_delete=models.CASCADE, blank=True, null=True)
    destination_account = models.ForeignKey(Account, related_name='transactions_to', on_delete=models.CASCADE, blank=True, null=True)

    objects = TransactionQuerySet.as_manager()

    def __str__(self):
        return f'{self.type.capitalize()} - {self.amount} on {self.date}'

    class Meta:
        ordering = ['-date']


class Income(models.Model):
    INCOME_CATEGORIES = [
        ('salary', 'Salary'),
        ('interest', 'Interest'),
        ('parents', 'Parents'),
        ('joint transfer', 'Joint Transfer'),
        ('birthday', 'Birthday'),
        ('christmas', 'Christmas'),
        ('tax', 'Tax'),
        ('other', 'Other'),
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
        ('car', 'Car'),
        ('cash', 'Cash'),
        ('clothing', 'Clothing'),
        ('coffees & snacks', 'Coffees & Snacks'),
        ('dining out', 'Dining Out'),
        ('entertainment', 'Entertainment'),
        ('farm', 'Farm'),
        ('fees', 'Fees'),
        ('gifts', 'Gifts'),
        ('groceries', 'Groceries'),
        ('gym', 'Gym'),
        ('housing', 'Housing'),
        ('medical appointments', 'Medical Appointments'),
        ('miscellaneous', 'Miscellaneous'),
        ('personal care', 'Personal Care'),
        ('personal development', 'Personal Development'),
        ('pet', 'Pet'),
        ('petrol', 'Petrol'),
        ('pharmacy', 'Pharmacy'),
        ('phone', 'Phone'),
        ('sports', 'Sports'),
        ('supplements', 'Supplements'),
        ('tattoos', 'Tattoos'),
        ('taxes', 'Taxes'),
        ('transportation', 'Transportation'),
        ('utilities', 'Utilities'),
        ('vacation', 'Vacation'),
        ('wedding', 'Wedding'),
        ('workspace', 'Workspace'),
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
