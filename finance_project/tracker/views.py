from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponseNotAllowed, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Sum

from tracker.models import Transaction, Income, Expense
from tracker.filters import TransactionFilter
from tracker.forms import TransactionForm
from tracker.resources import TransactionExportResource, TransactionImportResource
from tracker.tracker_helpers import adjust_account_balances

from tablib import Dataset

PAGE_TRANSACTIONS = 20

def index(request):
    return render(request, 'tracker/index.html')


class TransactionsListView(LoginRequiredMixin, ListView):
    model = Transaction
    context_object_name = 'transactions'

    def get_queryset(self):
        """Fetches and filters the queryset based on user and optional filtering."""
        queryset = Transaction.objects.filter(user=self.request.user).select_related('expense_transaction', 'income_transaction')
        
        if self.request.GET:
            transaction_filter = TransactionFilter(self.request.GET, queryset=queryset)
            return transaction_filter.qs
        return queryset

    def get_context_data(self, **kwargs):
        """Adds filtered transactions, pagination, and income/expense totals to the context."""
        self.object_list = self.get_queryset()
        
        # Call the parent's method to initialize context
        context = super().get_context_data(**kwargs)

        # Apply filtering
        transaction_filter = TransactionFilter(self.request.GET, queryset=self.get_queryset())
        filtered_transactions = transaction_filter.qs

        # Pagination logic
        paginator = Paginator(filtered_transactions, PAGE_TRANSACTIONS)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Add income and expense totals
        total_income = filtered_transactions.get_total_income()
        total_expenses = filtered_transactions.get_total_expenses()

        # Add to context
        context = {
            'filter': transaction_filter,
            'page_obj': page_obj,
            'transactions': page_obj.object_list,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': total_income - total_expenses
        }
        return context

    def get(self, request, *args, **kwargs):
        """Handles both regular and HTMX requests to render partials or full templates."""
        context = self.get_context_data()
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

        transaction_filter = TransactionFilter(
            request.GET,
            queryset=Transaction.objects.filter(user=request.user).select_related('expense_transaction', 'income_transaction')
        )

        data = TransactionExportResource().export(transaction_filter.qs)
        response = HttpResponse(data.csv, content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        return response


class TransactionsImportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'tracker/partials/import-transaction.html')

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return render(request, 'tracker/partials/transaction-success.html', {'message': 'No file uploaded.'})

        resource = TransactionImportResource()
        dataset = Dataset()

        # Load the file into the dataset
        try:
            dataset.load(file.read().decode(), format='csv', headers=True)
        except Exception as e:
            return render(request, 'tracker/partials/transaction-success.html', {'message': f"Error loading dataset: {e}"})
        
        # Dry run the import to first check for errors
        try:
            result = resource.import_data(dataset, user=request.user, dry_run=True, raise_errors=True)
        except Exception as e:
            return render(request, 'tracker/partials/transaction-success.html', {'message': f"Error during dry run: {e}"})

        # Log any errors from the dry run
        if result.has_errors():
            errors = []
            for row in result.row_errors():
                row_number, row_errors = row
                row_error_messages = [f"Row {row_number}: {error}" for error in row_errors]
                errors.extend(row_error_messages)
            return render(request, 'tracker/partials/transaction-success.html', {
                'message': 'Errors found during dry run import.',
                'errors': errors,
            })

        # Perform the actual import
        try:
            resource.import_data(dataset, user=request.user, dry_run=False)
        except Exception as e:
            return render(request, 'tracker/partials/transaction-success.html', {'message': f"Error during actual import: {e}"})

        # Return the success message after the transaction import
        return render(request, 'tracker/partials/transaction-success.html', {'message': f'{len(dataset)} transactions uploaded successfully!'})


class TotalsView(LoginRequiredMixin, ListView):
    model = Transaction
    context_object_name = 'totals'
    template_name = "tracker/totals.html"

    def get_queryset(self):
        """Fetches the queryset."""
        queryset = Transaction.objects.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        
        # Calculate totals
        total_income = Transaction.objects.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = Transaction.objects.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        
        context = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': total_income - total_expenses
        }
        
        return context
