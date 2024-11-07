from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponseNotAllowed

from tracker.models import Account, Transaction, Income, Expense
from tracker.filters import TransactionFilter
from tracker.forms import TransactionForm


def index(request):
    return render(request, 'tracker/index.html')


class TransactionsListView(LoginRequiredMixin, ListView):
    model = Transaction

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).select_related('expense_transaction', 'income_transaction')
        
        if self.request.GET:
            transaction_filter = TransactionFilter(self.request.GET, queryset=queryset)
            return transaction_filter.qs
        return queryset

    def get(self, request, *args, **kwargs):
        transaction_filter = TransactionFilter(
            request.GET,
            queryset=self.get_queryset()
        )
        total_income = transaction_filter.qs.get_total_income()
        total_expenses = transaction_filter.qs.get_total_expenses()
        context = {
            'filter': transaction_filter,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': total_income - total_expenses
        }

        if request.htmx:
            return render(request, 'tracker/partials/transactions-container.html', context)

        return render(request, 'tracker/transactions-list.html', context)


class TransactionsCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'tracker/partials/create-transaction.html'
    success_url = '/transactions/success/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        if self.request.htmx:
            return render(
                self.request,
                'tracker/partials/transaction-success.html',
                {'message': 'Transaction successfully added!'},
                )

        return response

    def form_invalid(self, form):
        if self.request.htmx:
            return render(
                self.request,
                'tracker/partials/create-transaction.html',
                {'form': form},
            )

        return super().form_invalid(form)


class TransactionsUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'tracker/partials/update-transaction.html'
    success_url = '/transactions/success/'

    def get_initial(self):
        initial = super().get_initial()
        transaction = self.object

        if transaction.type == 'income':
            try:
                income = transaction.income_transaction
                initial.update({
                    'income_category': income.category,
                    'amount': income.amount,
                    'date': income.date,
                    'account': income.account,
                })
            except Income.DoesNotExist:
                pass

        elif transaction.type == 'expense':
            try:
                expense = transaction.expense_transaction
                initial.update({
                    'expense_category': expense.category,
                    'expense_type': expense.fixed_or_variable,
                    'amount': expense.amount,
                    'date': expense.date,
                    'account': expense.account,
                })
            except Expense.DoesNotExist:
                pass

        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        transaction = form.save(commit=False)

        # Track original values before updating
        original_transaction = Transaction.objects.get(pk=transaction.pk)
        original_amount = original_transaction.amount
        original_origin_account = original_transaction.origin_account
        original_destination_account = original_transaction.destination_account

        # Adjust balances based on the original values
        if transaction.type == 'income' and original_destination_account:
            original_destination_account.balance -= original_amount
            original_destination_account.save()

            income, created = Income.objects.update_or_create(
                transaction=transaction,
                defaults={
                    'amount': transaction.amount,
                    'date': transaction.date,
                    'category': form.cleaned_data.get('income_category'),
                    'account': transaction.destination_account,
                }
            )

            # Recalculate the tax amount if a tax percentage exists
            if original_transaction.tax_percentage:
                original_tax_amount = original_transaction.amount * (original_transaction.tax_percentage / 100)
                tax_account = Account.objects.get(account_type='virtual_tax')

                tax_account.balance -= original_tax_amount
                tax_account.save()

            if transaction.tax_percentage:
                new_tax_amount = transaction.amount * (transaction.tax_percentage / 100)

                tax_account.balance += new_tax_amount
                tax_account.save()

            transaction.destination_account.balance += transaction.amount
            transaction.destination_account.save()

            if original_transaction.fee:
                fee_expense = Expense.objects.get(transaction=original_transaction)
                fee_expense.amount = transaction.fee
                fee_expense.save()

        elif transaction.type == 'expense' and original_origin_account:
            original_origin_account.balance += original_amount
            original_origin_account.save()

            expense, created = Expense.objects.update_or_create(
                transaction=transaction,
                defaults={
                    'amount': transaction.amount,
                    'date': transaction.date,
                    'category': form.cleaned_data.get('expense_category'),
                    'account': transaction.origin_account,
                    'fixed_or_variable': form.cleaned_data.get('expense_type')
                }
            )

            transaction.origin_account.balance -= transaction.amount
            transaction.origin_account.save()

        transaction.save()

        if self.request.htmx:
            return render(
                self.request,
                'tracker/partials/transaction-success.html',
                {'message': 'Transaction successfully updated!'},
            )

        return super().form_valid(form)


class TransactionsDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'tracker/partials/transaction-success.html'
    success_url = '/transactions/success/'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if self.object.user != request.user:
            return HttpResponseNotAllowed(['DELETE'])
        
        amount = self.object.amount
        date = self.object.date
        
        self.object.delete()

        context = {
            'message': f"Transaction of {amount} on {date} was deleted successfully!"
        }
        return render(request, self.template_name, context)
