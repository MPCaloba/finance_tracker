import logging

from django.utils import timezone
from datetime import datetime

from decimal import Decimal, InvalidOperation

from import_export import resources, fields
from tracker.models import Transaction, Account, Expense, Income
from tracker.tracker_helpers import adjust_account_balances
from import_export.widgets import DateWidget, ForeignKeyWidget
from import_export.results import RowResult

logger = logging.getLogger(__name__)

class TransactionExportResource(resources.ModelResource):
    date = fields.Field(
        column_name='Date',
        attribute='date',
        widget=DateWidget(format='%d-%m-%Y')
    )

    type = fields.Field(column_name='Type', attribute='type')
    description = fields.Field(column_name='Description', attribute='description')
    amount = fields.Field(column_name='Amount', attribute='amount')

    income_category = fields.Field(column_name='Income Category')
    expense_category = fields.Field(column_name='Expense Category')
    source = fields.Field(column_name='Source')
    fixed_or_variable = fields.Field(column_name='Fixed or Variable')

    origin_account = fields.Field(
        column_name='Origin Account',
        attribute='origin_account',
        widget=ForeignKeyWidget(Account, 'name')
    )
    destination_account = fields.Field(
        column_name='Destination Account',
        attribute='destination_account',
        widget=ForeignKeyWidget(Account, 'name')
    )

    def dehydrate_type(self, transaction):
        return transaction.get_type_display()

    def dehydrate_amount(self, transaction):
        return f"€ {transaction.amount:,.2f}"

    def dehydrate_income_category(self, transaction):
        if transaction.type == 'income' and transaction.income_transaction:
            return transaction.income_transaction.category.capitalize()
        return ''

    def dehydrate_expense_category(self, transaction):
        if transaction.type == 'expense' and transaction.expense_transaction:
            return transaction.expense_transaction.category.capitalize()
        return ''

    def dehydrate_source(self, transaction):
        if transaction.type == 'expense' and transaction.expense_transaction:
            return transaction.expense_transaction.source.capitalize()
        return ''

    def dehydrate_fixed_or_variable(self, transaction):
        if transaction.type == 'expense' and transaction.expense_transaction:
            return transaction.expense_transaction.fixed_or_variable.capitalize()
        return ''

    def after_init_instance(self, instance, new, row, **kwargs):
        instance.user = kwargs.get('user')

    class Meta:
        model = Transaction
        fields = (
            'date',
            'type',
            'description',
            'amount',
            'income_category',
            'expense_category',
            'source',
            'fixed_or_variable',
            'origin_account',
            'destination_account',
        )


class TransactionImportResource(resources.ModelResource):
    class Meta:
        model = Transaction
        fields = (
            'date',
            'type',
            'description',
            'amount',
            'user',
        )
        import_id_fields = (
            'date',
            'type',
            'description',
            'amount',          
        )

    def import_row(self, row, *args, **kwargs):
        # Check if it's a dry run and get the user
        dry_run = kwargs.get('dry_run', False)
        user = kwargs.get('user')
        if not user:
            raise ValueError("User is required to create a transaction.")

        # Step 1: Parse and validate the date
        date_str = row['date']
        try:
            date = datetime.strptime(date_str, '%d-%m-%Y').date()
            row['date'] = timezone.make_aware(datetime.combine(date, datetime.min.time()), timezone.get_current_timezone())
        except ValueError as e:
            raise ValueError(f"Error parsing date '{date_str}': Expected format is dd-mm-yyyy.") from e

        # Step 2: Parse and validate the amount
        try:
            row['amount'] = Decimal(row['amount'].replace(',', ''))
        except InvalidOperation:
            raise ValueError(f"Invalid amount: {row['amount']}")

        # Step 3: Validate the transaction type
        if row['type'] not in dict(Transaction.TRANSACTION_TYPES):
            raise ValueError(f"Invalid transaction type: {row['type']}")

        # Step 4: Resolve ForeignKey relationships for accounts
        try:
            row['origin_account'] = (
                Account.objects.get(name=row['origin_account']) if row['origin_account'] else None
            )
            row['destination_account'] = (
                Account.objects.get(name=row['destination_account']) if row['destination_account'] else None
            )
        except Account.DoesNotExist as e:
            raise ValueError(f"Account not found: {e}")

        # Step 5: Check if transaction already exists, to avoid duplicates
        transaction = Transaction.objects.filter(
            date=row['date'],
            type=row['type'],
            description=row['description'],
            amount=row['amount'],
            origin_account=row.get('origin_account'),
            destination_account=row.get('destination_account'),
        ).first()

        # Step 6: Create Transaction instance if it doesn't exist
        if not transaction:
            transaction = Transaction(
                user=kwargs.get('user'),
                date=row['date'],
                type=row['type'],
                description=row['description'],
                amount=row['amount'],
                origin_account=row.get('origin_account'),
                destination_account=row.get('destination_account'),
            )
            # Do not save during dry run
            if not dry_run:
                transaction.save()
                adjust_account_balances(transaction)
        else:
            logger.debug(f"Found existing transaction: {transaction}")

        # Step 7: Handle related model creation based on transaction type
        if transaction.type == 'income':
            if not dry_run:
                Income.objects.create(
                    transaction=transaction,
                    category=row.get('income_category', ''),
                    amount=transaction.amount,
                    account=transaction.destination_account,
                    date=transaction.date,
                )
        elif transaction.type == 'expense':
            if not dry_run:
                Expense.objects.create(
                    transaction=transaction,
                    category=row.get('expense_category', ''),
                    source=row.get('source', ''),
                    fixed_or_variable=row.get('fixed_or_variable', ''),
                    amount=transaction.amount,
                    account=transaction.origin_account,
                    date=transaction.date,
                )

        # Create a RowResult instance
        row_result = RowResult()

        # Set attributes directly
        row_result.errors = []
        row_result.diff = None
        row_result.instance = transaction
        row_result.import_type = RowResult.IMPORT_TYPE_NEW

        return row_result
