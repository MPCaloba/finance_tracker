from django.urls import path
from tracker import views

from .views import TransactionsListView, TransactionsCreateView, TransactionsUpdateView, TransactionsDeleteView, TransactionsExportView, TransactionsImportView, TotalsView


urlpatterns = [
    path("", views.index, name='index'),
    path('transactions/', TransactionsListView.as_view(), name='transactions-list'),
    path('totals/', TotalsView.as_view(), name='totals-view'),
    path('transactions/create/', TransactionsCreateView.as_view(), name='create-transaction'),

    path('transactions/<int:pk>/update/', TransactionsUpdateView.as_view(), name='update-transaction'),
    path('transactions/<int:pk>/delete/', TransactionsDeleteView.as_view(), name='delete-transaction'),

    path('transactions/export', TransactionsExportView.as_view(), name='export'),
    path('transactions/import', TransactionsImportView.as_view(), name='import'),
]
