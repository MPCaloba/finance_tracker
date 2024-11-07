from django import forms
from tracker.models import Transaction, Expense, Income


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

    class Meta:
        model = Transaction
        fields = (
            'type',
            'date',
            'description',
            'amount',
            'origin_account',
            'destination_account',
            'tax_percentage',
            'fee',
        )
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
    
    def save(self, commit=True):
        transaction = super().save(commit=False)

        if transaction.type == 'expense':
            expense = Expense(
                amount=transaction.amount,
                date=transaction.date,
                category=self.cleaned_data['expense_category'],
                source=self.cleaned_data['expense_source'],
                fixed_or_variable=self.cleaned_data['expense_type'],
                account=transaction.origin_account,
                transaction=transaction
            )
            if commit:
                transaction.save()
                expense.save()

        elif transaction.type == 'income':
            income = Income(
                amount=transaction.amount,
                date=transaction.date,
                category=self.cleaned_data['income_category'],
                account=transaction.destination_account,
                transaction=transaction
            )
            if commit:
                transaction.save()
                income.save()

        if commit:
            transaction.save()
        return transaction
