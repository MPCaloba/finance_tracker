from django.db.models import Sum
from decimal import Decimal

from tracker.models import Account


def update_account_balance(account):
    """
    Calculates the balance for the given account based on related transactions
    and updates the balance field directly.
    """
    incoming = Decimal(account.transactions_to.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0)
    outgoing = Decimal(account.transactions_from.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0)
    internal_in = Decimal(account.transactions_to.filter(type='internal').aggregate(total=Sum('amount'))['total'] or 0)
    internal_out = Decimal(account.transactions_from.filter(type='internal').aggregate(total=Sum('amount'))['total'] or 0)
    
    # Calculate new balance
    new_balance = incoming - outgoing + internal_in - internal_out
    
    # Update and save the balance
    account.balance = new_balance
    account.save()


def adjust_account_balances(self):
    """
    Adjusts the balances of the involved accounts based on the transaction type.
    """
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
