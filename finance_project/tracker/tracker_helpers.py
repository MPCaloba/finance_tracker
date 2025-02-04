from django.db.models import Sum
from django.utils.timezone import now
from decimal import Decimal

from tracker.models import AccountBalanceHistory


def adjust_account_balances(transaction):
    """
    Adjusts the balances of the involved accounts based on the transaction type.
    """
    # Handle income transactions
    if transaction.type == 'income':
        # Update the destination account balance
        update_account_balance(transaction.destination_account)

    # Handle expense transactions
    elif transaction.type == 'expense':
        # Update the origin account balance
        update_account_balance(transaction.origin_account)

    # Handle internal transactions
    elif transaction.type == 'internal':
        # Update balances for both the origin and destination accounts
        update_account_balance(transaction.origin_account)
        update_account_balance(transaction.destination_account)

    # Handle tax-related transactions
    elif transaction.type == 'tax':
        if transaction.origin_account:
            # Tax payment (expense, deduct from tax account)
            update_account_balance(transaction.origin_account)
        else:
            # Tax related to income (add to tax account)
            update_account_balance(transaction.destination_account)


def update_account_balance(account):
    """
    Calculates the balance for the given account based on related transactions
    and updates the balance field directly.
    """
    # Get all movements
    incoming = Decimal(account.transactions_to.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0)
    outgoing = Decimal(account.transactions_from.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0)

    internal_in = Decimal(account.transactions_to.filter(type='internal').aggregate(total=Sum('amount'))['total'] or 0)
    internal_out = Decimal(account.transactions_from.filter(type='internal').aggregate(total=Sum('amount'))['total'] or 0)

    tax_in = Decimal(account.transactions_to.filter(type='tax').aggregate(total=Sum('amount'))['total'] or 0)
    tax_out = Decimal(account.transactions_from.filter(type='tax').aggregate(total=Sum('amount'))['total'] or 0)

    # Calculate new balance
    if account.account_type == 'virtual_tax':
        new_balance = tax_in - tax_out
    else:
        new_balance = incoming - outgoing + internal_in - internal_out

    # Update the balance and save
    account.balance = new_balance
    account.save()

    # Record the updated balance in the history
    record_account_balance(account)


def record_account_balance(account):
    """
    Records the current balance of the given account in AccountBalanceHistory.
    """
    current_time = now()

    # Check if there's already a record for the same account with the same balance
    last_balance_record = AccountBalanceHistory.objects.filter(account=account).order_by('-timestamp').first()

    if last_balance_record and last_balance_record.balance == account.balance:
        # If the balance is the same as the last record, do not create a new one
        return

    AccountBalanceHistory.objects.create(
        account=account,
        balance=account.balance,
        timestamp=current_time,
    )
