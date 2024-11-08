from django import forms

from tracker.models import Transaction, Expense, Income
from tracker.tracker_helpers import adjust_account_balances


class TransactionForm(forms.ModelForm):
    expense_category = forms.ChoiceField(
        choices=[('', '---------')] + list(Expense.EXPENSE_CATEGORIES),
        widget=forms.Select(),
        label="Expense Category",
        required=False
    )

    income_category = forms.ChoiceField(
        choices=[('', '---------')] + list(Income.INCOME_CATEGORIES),
        widget=forms.Select(),
        label="Income Category",
        required=False
    )

    expense_source = forms.ChoiceField(
        choices=[('', '---------')] + list(Expense.SOURCES),
        widget=forms.Select(),
        label="Expense Source",
        required=False
    )

    expense_type = forms.ChoiceField(
        choices=[('', '---------')] + list(Expense.TYPES),
        widget=forms.Select(),
        label="Expense Type",
        required=False
    )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be a positive number")
        return amount

    class Meta:
        model = Transaction
        fields = (
            'type',
            'date',
            'description',
            'amount',
            'origin_account',
            'destination_account',
        )
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

    def save(self, commit=True):
        transaction = super().save(commit=False)

        if commit:
            transaction.save()

        if transaction.type == 'expense':
            expense = Expense(
                amount=transaction.amount,
                category=self.cleaned_data['expense_category'],
                date=transaction.date,
                source=self.cleaned_data['expense_source'],
                fixed_or_variable=self.cleaned_data['expense_type'],
                transaction=transaction,
                account=transaction.origin_account,
            )
            if commit:
                expense.save()

        elif transaction.type == 'income':
            income = Income(
                amount=transaction.amount,
                category=self.cleaned_data['income_category'],
                date=transaction.date,
                transaction=transaction,
                account=transaction.destination_account,
            )
            if commit:
                income.save()

        # Adjust the account balance after saving the transaction
        adjust_account_balances(transaction)

        return transaction
