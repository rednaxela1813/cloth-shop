from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import AccountLoginForm, AccountRegisterForm
from .use_cases import (
    authenticate_customer,
    build_account_dashboard_context,
    build_account_orders_context,
    create_customer_account,
)


@require_http_methods(["GET", "POST"])
def account_login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = AccountLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate_customer(
            request=request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            form.add_error(None, "Nesprávny email alebo heslo.")
        else:
            login(request, user)
            messages.success(request, "Ste prihlásený.")
            next_url = request.POST.get("next") or request.GET.get("next") or reverse("accounts:dashboard")
            return redirect(next_url)

    return render(
        request,
        "csm/pages/account_login.html",
        {
            "form": form,
            "next": request.POST.get("next") or request.GET.get("next") or "",
        },
    )


@require_http_methods(["GET", "POST"])
def account_register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = AccountRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = create_customer_account(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
        )
        login(request, user)
        messages.success(request, "Účet bol vytvorený.")
        next_url = request.POST.get("next") or request.GET.get("next") or reverse("accounts:dashboard")
        return redirect(next_url)

    return render(
        request,
        "csm/pages/account_register.html",
        {
            "form": form,
            "next": request.POST.get("next") or request.GET.get("next") or "",
        },
    )


@login_required
def account_logout_view(request):
    logout(request)
    messages.success(request, "Boli ste odhlásený.")
    return redirect("pages:home")


@login_required
def account_dashboard_view(request):
    context = build_account_dashboard_context(user=request.user)
    return render(request, "csm/pages/account_dashboard.html", context)


@login_required
def account_orders_view(request):
    context = build_account_orders_context(user=request.user)
    return render(request, "csm/pages/account_orders.html", context)
