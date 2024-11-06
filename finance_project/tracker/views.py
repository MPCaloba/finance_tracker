from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from tracker.models import Transaction
from tracker.filters import TransactionFilter


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
