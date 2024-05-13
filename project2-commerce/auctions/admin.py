from django.contrib import admin

from .models import *

# Register your models here.
class BidAdmin(admin.ModelAdmin):
    list_display = ["id", "price", "listing", "bidder"]


class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "content", "listing", "commenter"]


class ListingAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "category", "starting_bid", "time", "status", "lister"]


class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "email"]
    filter_horizontal = ["watchlist"]


admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(User, UserAdmin)
