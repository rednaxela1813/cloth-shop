from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass
from typing import Iterable

from locust import HttpUser, between, task


PRODUCT_LINK_RE = re.compile(r'href="(?P<path>/shop/[0-9a-f-]+/[^"/]+/)"')
CATEGORY_LINK_RE = re.compile(r'href="(?P<path>/catalog/[^"/]+/)"')
CSRF_RE = re.compile(r'name="csrfmiddlewaretoken" value="(?P<token>[^"]+)"')
VARIANT_ID_RE = re.compile(r'id="variant-public-id"[^>]*value="(?P<variant>[0-9a-f-]+)"')
CART_SET_RE = re.compile(r'action="(?P<path>/cart/set/(?P<variant>[0-9a-f-]+)/)"')
CART_REMOVE_RE = re.compile(r'action="(?P<path>/cart/remove/(?P<variant>[0-9a-f-]+)/)"')


@dataclass
class CartLine:
    variant_id: str
    set_path: str
    remove_path: str


class CatalogMixin:
    catalog_paths: list[str]
    product_paths: list[str]

    def on_start(self):
        self.catalog_paths = []
        self.product_paths = []
        self._warm_catalog()

    def _warm_catalog(self) -> None:
        self.client.get("/", name="GET /")
        self.client.get("/shop/", name="GET /shop/")
        self.client.get("/catalog/", name="GET /catalog/")
        self._refresh_catalog_index()

    def _refresh_catalog_index(self) -> None:
        shop_response = self.client.get("/shop/", name="GET /shop/")
        self.product_paths = self._extract_unique(PRODUCT_LINK_RE, shop_response.text)

        catalog_response = self.client.get("/catalog/", name="GET /catalog/")
        self.catalog_paths = self._extract_unique(CATEGORY_LINK_RE, catalog_response.text)

    def _extract_unique(self, pattern: re.Pattern[str], html: str) -> list[str]:
        results: list[str] = []
        seen: set[str] = set()
        for match in pattern.finditer(html):
            path = match.group("path")
            if path in seen:
                continue
            seen.add(path)
            results.append(path)
        return results

    def _pick_product_path(self) -> str | None:
        if not self.product_paths:
            self._refresh_catalog_index()
        return random.choice(self.product_paths) if self.product_paths else None

    def _pick_category_path(self) -> str | None:
        if not self.catalog_paths:
            self._refresh_catalog_index()
        return random.choice(self.catalog_paths) if self.catalog_paths else None

    def _extract_csrf(self, html: str) -> str:
        match = CSRF_RE.search(html)
        return match.group("token") if match else ""

    def _extract_variant_id(self, html: str) -> str | None:
        match = VARIANT_ID_RE.search(html)
        return match.group("variant") if match else None

    def _extract_cart_lines(self, html: str) -> list[CartLine]:
        set_matches = {match.group("variant"): match.group("path") for match in CART_SET_RE.finditer(html)}
        remove_matches = {match.group("variant"): match.group("path") for match in CART_REMOVE_RE.finditer(html)}

        lines: list[CartLine] = []
        for variant_id, set_path in set_matches.items():
            remove_path = remove_matches.get(variant_id)
            if not remove_path:
                continue
            lines.append(CartLine(variant_id=variant_id, set_path=set_path, remove_path=remove_path))
        return lines

    def _checkout_payload(self) -> dict[str, str]:
        suffix = random.randint(1000, 9999)
        return {
            "full_name": f"Load User {suffix}",
            "email": f"load{suffix}@example.com",
            "phone": f"0900{suffix}",
            "country": "SK",
            "shipping_method": random.choice(["paketa_pickup", "dpd_home"]),
            "region": "Bratislava",
            "city": "Bratislava",
            "postal_code": "81101",
            "address_line1": f"Test Street {suffix}",
            "address_line2": "",
        }


class StoreUser(CatalogMixin, HttpUser):
    wait_time = between(1, 4)

    @task(6)
    def browse(self):
        self.client.get("/", name="GET /")
        self.client.get("/shop/", name="GET /shop/")

        category_path = self._pick_category_path()
        if category_path:
            self.client.get(category_path, name="GET /catalog/:slug/")

        product_path = self._pick_product_path()
        if product_path:
            self.client.get(product_path, name="GET /shop/:product/")

    @task(4)
    def cart_flow(self):
        product_path = self._pick_product_path()
        if not product_path:
            return

        product_response = self.client.get(product_path, name="GET /shop/:product/")
        csrf_token = self._extract_csrf(product_response.text)
        variant_id = self._extract_variant_id(product_response.text)
        if not csrf_token or not variant_id:
            return

        self.client.post(
            "/cart/add/",
            data={
                "csrfmiddlewaretoken": csrf_token,
                "variant_public_id": variant_id,
                "quantity": "1",
                "next": product_path,
            },
            headers={"Referer": self._absolute_url(product_path)},
            name="POST /cart/add/",
            allow_redirects=False,
        )

        cart_response = self.client.get("/cart/", name="GET /cart/")
        cart_lines = self._extract_cart_lines(cart_response.text)
        if not cart_lines:
            return

        chosen = random.choice(cart_lines)
        cart_csrf = self._extract_csrf(cart_response.text)
        if not cart_csrf:
            return

        self.client.post(
            chosen.set_path,
            data={"csrfmiddlewaretoken": cart_csrf, "quantity": str(random.randint(1, 3)), "next": "/cart/"},
            headers={"Referer": self._absolute_url("/cart/")},
            name="POST /cart/set/:variant/",
            allow_redirects=False,
        )

        if random.random() < 0.5:
            self.client.post(
                chosen.remove_path,
                data={"csrfmiddlewaretoken": cart_csrf, "next": "/cart/"},
                headers={"Referer": self._absolute_url("/cart/")},
                name="POST /cart/remove/:variant/",
                allow_redirects=False,
            )

    @task(2)
    def checkout(self):
        product_path = self._pick_product_path()
        if not product_path:
            return

        product_response = self.client.get(product_path, name="GET /shop/:product/")
        product_csrf = self._extract_csrf(product_response.text)
        variant_id = self._extract_variant_id(product_response.text)
        if not product_csrf or not variant_id:
            return

        self.client.post(
            "/cart/add/",
            data={
                "csrfmiddlewaretoken": product_csrf,
                "variant_public_id": variant_id,
                "quantity": "1",
                "next": "/checkout/",
            },
            headers={"Referer": self._absolute_url(product_path)},
            name="POST /cart/add/",
            allow_redirects=False,
        )

        checkout_response = self.client.get("/checkout/", name="GET /checkout/")
        checkout_csrf = self._extract_csrf(checkout_response.text)
        if not checkout_csrf:
            return

        payload = self._checkout_payload()
        payload["csrfmiddlewaretoken"] = checkout_csrf

        with self.client.post(
            "/checkout/",
            data=payload,
            headers={"Referer": self._absolute_url("/checkout/")},
            name="POST /checkout/",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            location = response.headers.get("Location", "")
            if response.status_code in {301, 302} and location.startswith("/checkout/pay/"):
                response.success()
            elif response.status_code == 200:
                response.failure("Checkout stayed on page. Likely validation, empty cart, or stock issue.")
            else:
                response.failure(f"Unexpected checkout response: {response.status_code}")

    @task(1)
    def hot_item_contention(self):
        hot_product_path = os.getenv("HOT_PRODUCT_PATH", "").strip()
        if not hot_product_path:
            return

        product_response = self.client.get(hot_product_path, name="GET /shop/:hot-product/")
        csrf_token = self._extract_csrf(product_response.text)
        variant_id = self._extract_variant_id(product_response.text)
        if not csrf_token or not variant_id:
            return

        self.client.post(
            "/cart/add/",
            data={
                "csrfmiddlewaretoken": csrf_token,
                "variant_public_id": variant_id,
                "quantity": "1",
                "next": "/checkout/",
            },
            headers={"Referer": self._absolute_url(hot_product_path)},
            name="POST /cart/add/:hot-item/",
            allow_redirects=False,
        )

        checkout_response = self.client.get("/checkout/", name="GET /checkout/")
        checkout_csrf = self._extract_csrf(checkout_response.text)
        if not checkout_csrf:
            return

        payload = self._checkout_payload()
        payload["csrfmiddlewaretoken"] = checkout_csrf

        self.client.post(
            "/checkout/",
            data=payload,
            headers={"Referer": self._absolute_url("/checkout/")},
            name="POST /checkout/:hot-item/",
            allow_redirects=False,
        )

    def _absolute_url(self, path: str) -> str:
        return f"{self.environment.host.rstrip('/')}{path}"
