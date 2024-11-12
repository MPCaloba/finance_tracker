from import_export import resources, fields
from tracker.models import Transaction, Account
from import_export.widgets import DateWidget, ForeignKeyWidget

class TransactionResource(resources.ModelResource):
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
        import_id_fields = (
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
