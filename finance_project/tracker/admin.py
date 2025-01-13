from django.contrib import admin
from tracker.models import User, Account, AccountBalanceHistory, Transaction, Income, Expense, Tax

# Register your models here.
admin.site.register(User)
admin.site.register(Account)
admin.site.register(AccountBalanceHistory)
admin.site.register(Transaction)
admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(Tax)
