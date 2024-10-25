from django.urls import path
from tracker import views

from .views import TransactionsListView


urlpatterns = [
    path("", views.index, name='index'),
    path('transactions/', TransactionsListView.as_view(), name='transactions-list'),
]
