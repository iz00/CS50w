from decimal import Decimal
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import *


class BidForm(forms.Form):
    price = forms.DecimalField(decimal_places=2, label="Bid", label_suffix=": $", max_digits=64, min_value=Decimal("0.01"), step_size=0.01, widget=forms.NumberInput(attrs={"placeholder": "000.00"}))


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"autocomplete":"off", "cols": 80, "placeholder": "Enter your comment here.", "rows": 5}),
        }


class CreateListingForm(ModelForm):
    starting_bid = forms.DecimalField(decimal_places=2, label="Starting bid", label_suffix=": $", max_digits=64, min_value=Decimal("0.01"), step_size=0.01, widget=forms.NumberInput(attrs={"placeholder": "000.00"}))
    class Meta:
        model = Listing
        fields = ["title", "description", "starting_bid", "image", "category"]
        widgets = {
            "description": forms.Textarea(attrs={"autocomplete":"off", "cols": 80, "placeholder": "Enter the listing's description here.", "rows": 5}),
            "image": forms.TextInput(attrs={"autocomplete":"off", "placeholder": "https://example.com"}),
            "title": forms.TextInput(attrs={"autocomplete":"off", "placeholder": "Enter the listing's title here."})
        }


def index(request):
    listings = Listing.objects.filter(status="open").all().order_by("-time")

    listings_prices = []

    for listing in listings:

        bid = Bid.objects.filter(listing=listing).order_by("-price").first()

        if bid:
            listings_prices.append(bid.price)
        else:
            listings_prices.append(listing.starting_bid)

    listings = zip(listings, listings_prices)

    return render(request, "auctions/index.html", {
        "listings": listings
    })


@login_required
def bid(request):
    if request.method == "POST":
        try:
            listing = Listing.objects.get(pk=int(request.POST.get("listing")))
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse("index"))

        form = BidForm(request.POST)

        if not form.is_valid():
            return HttpResponseRedirect(reverse("index"))

        bids = Bid.objects.filter(listing=listing).order_by("-price").all()

        bid = form.cleaned_data["price"]

        if bids:
            if bid <= bids.first().price:
                return HttpResponseRedirect(reverse("index"))
        else:
            if bid < listing.starting_bid:
                return HttpResponseRedirect(reverse("index"))

        Bid(price=bid, bidder=User.objects.get(pk=request.user.id), listing=listing).save()

        return HttpResponseRedirect(reverse("listing", args=[listing.id]))


def categories(request):
    if request.method == "GET":
        if not request.GET.get("cat"):
            return render(request, "auctions/categories.html", {
                "categories": Listing.CATEGORIES[1:],
                "listings": None
            })

        listings = Listing.objects.filter(category=request.GET.get("cat"), status="open").all().order_by("-time")

        listings_prices = []

        for listing in listings:

            bid = Bid.objects.filter(listing=listing).order_by("-price").first()

            if bid:
                listings_prices.append(bid.price)
            else:
                listings_prices.append(listing.starting_bid)

        listings = zip(listings, listings_prices)

        return render(request, "auctions/categories.html", {
            "categories": None,
            "listings": listings
        })

@login_required
def close(request):
    if request.method == "POST":
        try:
            listing = Listing.objects.get(pk=int(request.POST.get("listing")))
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse("index"))

        Listing.objects.filter(pk=int(request.POST.get("listing"))).update(status="closed")

        return HttpResponseRedirect(reverse("listing", args=(listing.id,)))


@login_required
def comment(request):
    if request.method == "POST":
        try:
            listing = Listing.objects.get(pk=int(request.POST.get("listing")))
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse("index"))
    
        form = CommentForm(request.POST)

        if not form.is_valid():
            return HttpResponseRedirect(reverse("index"))

        Comment(
            content=form.cleaned_data["content"],
            commenter=User.objects.get(pk=request.user.id),
            listing = listing
        ).save()

        return HttpResponseRedirect(reverse("index"))


@login_required
def create(request):
    if request.method == "GET":
        return render(request, "auctions/create.html", {
            "form": CreateListingForm()
        })

    form = CreateListingForm(request.POST)

    if not form.is_valid():
        return render(request, "auctions/create.html", {
            "form": form
        })

    Listing(
        category=form.cleaned_data["category"],
        description=form.cleaned_data["description"].capitalize(),
        image=form.cleaned_data["image"],
        starting_bid=Decimal(form.cleaned_data["starting_bid"]),
        status="open",
        title=form.cleaned_data["title"].title(),
        lister=User.objects.get(pk=request.user.id)
    ).save()

    return HttpResponseRedirect(reverse("index"))


def listing(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
    except ObjectDoesNotExist:
        listing = watchlist = None
    else:
        watchlist = User.objects.filter(pk=request.user.id).first() in listing.users_watchlisted.all()

    return render(request, "auctions/listing.html", {
        "bids": Bid.objects.filter(listing=listing).all().order_by("-price"),
        "comments": Comment.objects.filter(listing=listing).all(),
        "bid_form": BidForm(),
        "comment_form": CommentForm(),
        "listing": listing,
        "watchlist": watchlist
    })


def login_view(request):
    if request.method == "GET":
        return render(request, "auctions/login.html", {
            "next_page": f"{request.GET.get('next', '')}"
        })

    # Attempt to sign user in
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)

    # Check if authentication successful
    if user:
        login(request, user)

        next_page = request.POST["next_page"]

        if next_page:
            return HttpResponseRedirect(f"{next_page}")

        return HttpResponseRedirect(reverse("index"))

    return render(request, "auctions/login.html", {
        "message": "Invalid username and/or password."
    })


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "GET":
        return render(request, "auctions/register.html")

    username = request.POST["username"]
    email = request.POST["email"]

    # Ensure password matches confirmation
    password = request.POST["password"]
    confirmation = request.POST["confirmation"]
    if password != confirmation:
        return render(request, "auctions/register.html", {
            "message": "Passwords must match."
        })

    # Attempt to create new user
    try:
        user = User.objects.create_user(username, email, password)
        user.save()
    except IntegrityError:
        return render(request, "auctions/register.html", {
            "message": "Username already taken."
        })

    login(request, user)
    return HttpResponseRedirect(reverse("index"))


@login_required
def watchlist(request):
    if request.method == "GET":

        listings = User.objects.get(pk=request.user.id).watchlist.all()

        listings_prices = []

        for listing in listings:

            bid = Bid.objects.filter(listing=listing).order_by("-price").first()

            if bid:
                listings_prices.append(bid.price)
            else:
                listings_prices.append(listing.starting_bid)

        listings = zip(listings, listings_prices)

        return render(request, "auctions/watchlist.html", {
            "listings": listings
        })

    user = User.objects.get(pk=request.user.id)
    listing = Listing.objects.get(pk=int(request.POST.get("listing")))

    if not listing:
        return HttpResponseRedirect(reverse("index"))

    if listing in user.watchlist.all():
        user.watchlist.remove(listing)
    else:
        user.watchlist.add(listing)

    user.save()

    return HttpResponseRedirect(reverse("watchlist"))
