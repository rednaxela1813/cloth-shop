#!/usr/bin/env python3
"""
Lightweight architecture guardrails for selected apps.

This script checks high-value boundaries:
1) views stay transport-only (no direct domain/service imports)
2) use_cases must not import views
3) services must not import views/use_cases
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def module_name_for(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    return ".".join(rel.parts)


def _resolve_relative(current_module: str, imported_module: str | None, level: int) -> str:
    parts = current_module.split(".")
    base = parts[:-level]
    if imported_module:
        return ".".join(base + imported_module.split("."))
    return ".".join(base)


def collect_imports(path: Path) -> set[str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    current = module_name_for(path)
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                resolved = _resolve_relative(current, node.module, node.level)
                if resolved:
                    imports.add(resolved)
            elif node.module:
                imports.add(node.module)
    return imports


def starts_with_any(value: str, prefixes: tuple[str, ...]) -> bool:
    return any(value == p or value.startswith(p + ".") for p in prefixes)


def check_orders_architecture() -> list[str]:
    errors: list[str] = []

    views_file = ROOT / "apps/orders/views.py"
    services_file = ROOT / "apps/orders/services.py"
    use_case_files = sorted((ROOT / "apps/orders/use_cases").glob("*.py"))

    view_imports = collect_imports(views_file)
    forbidden_for_views = ("apps.orders.services", "apps.orders.gateways", "stripe")
    for imp in sorted(view_imports):
        if starts_with_any(imp, forbidden_for_views):
            errors.append(f"{views_file}: forbidden import in views layer: {imp}")

    service_imports = collect_imports(services_file)
    forbidden_for_services = ("apps.orders.views", "apps.orders.use_cases")
    for imp in sorted(service_imports):
        if starts_with_any(imp, forbidden_for_services):
            errors.append(f"{services_file}: forbidden import in services layer: {imp}")

    for use_case in use_case_files:
        if use_case.name == "__init__.py":
            continue
        imports = collect_imports(use_case)
        for imp in sorted(imports):
            if starts_with_any(imp, ("apps.orders.views",)):
                errors.append(f"{use_case}: forbidden import in use_cases layer: {imp}")

    return errors


def _check_use_cases_do_not_import_views(*, app_name: str) -> list[str]:
    errors: list[str] = []
    use_case_dir = ROOT / f"apps/{app_name}/use_cases"
    if not use_case_dir.exists():
        return errors

    for use_case in sorted(use_case_dir.glob("*.py")):
        if use_case.name == "__init__.py":
            continue
        imports = collect_imports(use_case)
        for imp in sorted(imports):
            if starts_with_any(imp, (f"apps.{app_name}.views",)):
                errors.append(f"{use_case}: forbidden import in use_cases layer: {imp}")
    return errors


def _check_services_do_not_import_higher_layers(*, app_name: str) -> list[str]:
    errors: list[str] = []
    services_dir = ROOT / f"apps/{app_name}/services"
    if not services_dir.exists():
        return errors

    for service_file in sorted(services_dir.glob("*.py")):
        if service_file.name == "__init__.py":
            continue
        imports = collect_imports(service_file)
        forbidden_for_services = (f"apps.{app_name}.views", f"apps.{app_name}.use_cases")
        for imp in sorted(imports):
            if starts_with_any(imp, forbidden_for_services):
                errors.append(f"{service_file}: forbidden import in services layer: {imp}")
    return errors


def _check_view_imports(*, app_name: str, forbidden: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    views_file = ROOT / f"apps/{app_name}/views.py"
    if not views_file.exists():
        return errors

    view_imports = collect_imports(views_file)
    for imp in sorted(view_imports):
        if starts_with_any(imp, forbidden):
            errors.append(f"{views_file}: forbidden import in views layer: {imp}")
    return errors


def check_catalog_architecture() -> list[str]:
    errors: list[str] = []
    errors.extend(
        _check_view_imports(
            app_name="catalog",
            forbidden=("apps.products.models", "apps.catalog.breadcrumbs"),
        )
    )
    errors.extend(_check_use_cases_do_not_import_views(app_name="catalog"))
    return errors


def check_products_architecture() -> list[str]:
    errors: list[str] = []
    errors.extend(
        _check_view_imports(
            app_name="products",
            forbidden=("apps.products.models", "apps.catalog.breadcrumbs"),
        )
    )
    errors.extend(_check_use_cases_do_not_import_views(app_name="products"))
    errors.extend(_check_services_do_not_import_higher_layers(app_name="products"))
    return errors


def main() -> int:
    errors = []
    errors.extend(check_orders_architecture())
    errors.extend(check_catalog_architecture())
    errors.extend(check_products_architecture())
    if errors:
        print("Architecture check failed:")
        for e in errors:
            print(f"- {e}")
        return 1
    print("Architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
