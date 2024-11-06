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

    class Meta:
        model = Transaction
        fields = (
            'type',
            'date',
            'description',
            'amount',
            'expense_category', 
            'income_category'      
        )
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
