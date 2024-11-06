import django_filters
from django import forms
from tracker.models import Transaction, Expense, Income

class TransactionFilter(django_filters.FilterSet):
    transaction_type = django_filters.ChoiceFilter(
        choices=Transaction.TRANSACTION_TYPES,
        field_name='type',
        lookup_expr='iexact',
        empty_label='Any',
    )

    start_date = django_filters.DateFilter(
        field_name="date",
        lookup_expr="gte",
        label="Date From",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    end_date = django_filters.DateFilter(
        field_name="date",
        lookup_expr="lte",
        label="Date To",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    expense_category = django_filters.MultipleChoiceFilter(
        field_name='expense_transaction__category',
        choices=Expense.EXPENSE_CATEGORIES,
        label="Expense Category",
        widget=forms.CheckboxSelectMultiple()
    )

    income_category = django_filters.MultipleChoiceFilter(
        field_name='income_transaction__category',
        choices=Income.INCOME_CATEGORIES,
        label="Income Category",
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Transaction
        fields = ("transaction_type", "start_date", "end_date", "expense_category", "income_category")
