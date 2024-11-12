from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponseNotAllowed, HttpResponse

from tracker.models import Transaction, Income, Expense
from tracker.filters import TransactionFilter
from tracker.forms import TransactionForm
from tracker.resources import TransactionResource
from tracker.tracker_helpers import adjust_account_balances


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
        # Set the user before saving the transaction
        form.instance.user = self.request.user

        # Save the transaction
        response = super().form_valid(form)

        # Adjust account balances based on the newly created transaction
        adjust_account_balances(form.instance)

        # Handle HTMX requests
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
                    'expense_source': expense.source,
                    'amount': expense.amount,
                    'date': expense.date,
                    'account': expense.account,
                })
            except Expense.DoesNotExist:
                pass

        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user

        # Get the new transaction from the form without saving to the DB
        transaction = form.save(commit=False)

        # Get the original transaction values before updating
        original_transaction = Transaction.objects.get(pk=transaction.pk)
        original_amount = original_transaction.amount
        original_origin_account = original_transaction.origin_account
        original_destination_account = original_transaction.destination_account

        # Adjust balances based on the type of transaction and the original values
        if transaction.type == 'income':
            # Deduct the original amount from the original destination account
            original_destination_account.balance -= original_amount
            original_destination_account.save()

            # Update the Income record associated with the transaction
            income, created = Income.objects.update_or_create(
                transaction=transaction,
                defaults={
                    'amount': transaction.amount,
                    'date': transaction.date,
                    'category': form.cleaned_data.get('income_category'),
                    'account': transaction.destination_account,
                }
            )
        elif transaction.type == 'expense':
            # Add the original amount to the original origin account
            original_origin_account.balance += original_amount
            original_origin_account.save()

            # Update the Expense record associated with the transaction
            expense, created = Expense.objects.update_or_create(
                transaction=transaction,
                defaults={
                    'amount': transaction.amount,
                    'date': transaction.date,
                    'category': form.cleaned_data.get('expense_category'),
                    'account': transaction.origin_account,
                    'fixed_or_variable': form.cleaned_data.get('expense_type'),
                    'source': form.cleaned_data.get('expense_source'),
                }
            )
        elif transaction.type == 'internal':
            # Restore original amounts to both origin and destination accounts
            original_origin_account.balance += original_amount
            original_origin_account.save()
            original_destination_account.balance -= original_amount
            original_destination_account.save()
        elif transaction.type == 'tax':
            # Income-related tax transaction
            if original_destination_account:
                original_destination_account.balance -= original_amount
                original_destination_account.save()
            # Expense-related tax transaction
            elif original_origin_account:
                original_origin_account.balance += original_amount
                original_origin_account.save()

        # Save the updated transaction
        transaction.save()

        # Adjust account balances after the update
        adjust_account_balances(transaction)

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

        # Store the transaction details to display a message
        amount = self.object.amount
        date = self.object.date

        # Perform the deletion
        self.object.delete()

        # Adjust the account balances after deleting the transaction
        adjust_account_balances(self.object)

        context = {
            'message': f"Transaction of {amount} on {date} was deleted successfully!"
        }
        return render(request, self.template_name, context)


class TransactionsExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.htmx:
            return HttpResponse(headers={'HX-Redirect': request.get_full_path()})

        print(request.GET)

        transaction_filter = TransactionFilter(
            request.GET,
            queryset=Transaction.objects.filter(user=request.user).select_related('expense_transaction', 'income_transaction')
        )
        
        print(transaction_filter.qs.query)

        data = TransactionResource().export(transaction_filter.qs)
        response = HttpResponse(data.csv, content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        return response


class TransactionsImportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.htmx:
            return HttpResponse(headers={'HX-Redirect': request.get_full_path()})
