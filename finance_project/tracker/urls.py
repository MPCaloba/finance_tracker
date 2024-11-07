from django.urls import path
from tracker import views

from .views import TransactionsListView, TransactionsCreateView, TransactionsUpdateView, TransactionsDeleteView


urlpatterns = [
    path("", views.index, name='index'),
    path('transactions/', TransactionsListView.as_view(), name='transactions-list'),
    path('transactions/create/', TransactionsCreateView.as_view(), name='create-transaction'),

    path('transactions/<int:pk>/update/', TransactionsUpdateView.as_view(), name='update-transaction'),
    path('transactions/<int:pk>/delete/', TransactionsDeleteView.as_view(), name='delete-transaction'),
]
