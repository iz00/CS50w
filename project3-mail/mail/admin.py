from django.contrib import admin

from .models import *

# Register your models here.
class EmailAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "sender", "subject", "timestamp", "read", "archived"]
    filter_horizontal = ["recipients"]


class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "email"]


admin.site.register(Email, EmailAdmin)
admin.site.register(User, UserAdmin)
