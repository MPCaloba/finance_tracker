from django.contrib import admin
from tracker.models import Account, Transaction, Income, Expense, Tax

# Register your models here.
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(Tax)
