from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.cart.services import get_or_create_cart
from apps.shipping.services import calculate_shipping_cost, normalize_shipping_method
from .forms import CheckoutForm
from .use_cases.checkout import build_checkout_initial, process_checkout_submission
from .use_cases.handle_stripe_webhook import process_stripe_webhook
from .use_cases.order_lookup import get_accessible_order
from .use_cases.present_order_pages import build_checkout_success_context, build_payment_return_context
from .use_cases.start_payment import resolve_payment_start_decision

@require_http_methods(["GET", "POST"])
def checkout_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("variant", "variant__product").order_by("created")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Delegate submission orchestration to use case and keep view HTTP-only.
            decision = process_checkout_submission(request, cart, form.cleaned_data)
            if decision.form_error:
                form.add_error(None, decision.form_error)
            elif decision.redirect_url:
                return redirect(decision.redirect_url)
    else:
        form = CheckoutForm(initial=build_checkout_initial(request))

    selected_shipping_method = normalize_shipping_method(
        form.data.get("shipping_method") if form.is_bound else form.initial.get("shipping_method")
    )
    shipping_cost_preview = calculate_shipping_cost(
        shipping_method=selected_shipping_method,
        subtotal=cart.subtotal,
        country=form.data.get("country") if form.is_bound else form.initial.get("country"),
    )
    order_total_preview = cart.subtotal + shipping_cost_preview
    field_error_names = [
        "full_name",
        "email",
        "phone",
        "country",
        "shipping_method",
        "region",
        "city",
        "postal_code",
        "address_line1",
        "address_line2",
    ]
    has_field_errors = any(form[name].errors for name in field_error_names)

    return render(
        request,
        "csm/pages/checkout.html",
        {
            "cart": cart,
            "items": items,
            "form": form,
            "has_field_errors": has_field_errors,
            "shipping_cost_preview": shipping_cost_preview,
            "order_total_preview": order_total_preview,
        },
    )


def checkout_success_view(request, public_id):
    # Use centralized order lookup + access check shared by order-related views.
    order_ctx = get_accessible_order(request, public_id)
    page_ctx = build_checkout_success_context(order_ctx)
    return render(
        request,
        "csm/pages/checkout_success.html",
        {"order": page_ctx.order},
    )


@require_http_methods(["GET"])
def payment_start_view(request, public_id):
    # Use centralized order lookup + access check shared by order-related views.
    order_ctx = get_accessible_order(request, public_id)
    # Keep the view transport-only: orchestration is delegated to the use case.
    decision = resolve_payment_start_decision(request, order_ctx.order, order_ctx.access_token)
    if decision.bad_request_message:
        return HttpResponseBadRequest(decision.bad_request_message)
    return redirect(decision.redirect_url)


@require_http_methods(["GET"])
def payment_return_view(request):
    page_ctx = build_payment_return_context(request.GET.get("status"))
    return render(
        request,
        "csm/pages/payment_return.html",
        {"status": page_ctx.status},
    )


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook_view(request):
    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    result = process_stripe_webhook(
        payload=payload,
        signature=signature,
        webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
    )
    if not result.ok:
        return HttpResponseBadRequest(result.error_message)
    return HttpResponse("OK")
