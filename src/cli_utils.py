# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Reusable terminal input prompts and ASCII table formatting for StockFlow CLI."""

from __future__ import annotations

import math

from src.models import Product


def prompt_non_empty(label: str, default: str | None = None) -> str:
    """Prompt the user until a non-empty string is provided or a default is accepted."""
    prompt_text = f"{label} [{default}]: " if default is not None else f"{label}: "
    while True:
        raw = input(prompt_text).strip()
        if raw:
            return raw
        if default is not None and default.strip():
            return default.strip()
        print("Input cannot be empty. Please try again.")


def prompt_int(
    label: str,
    min_value: int = 0,
    default: int | None = None,
) -> int:
    """Prompt the user for an integer greater than or equal to ``min_value``."""
    prompt_text = f"{label} [{default}]: " if default is not None else f"{label}: "
    while True:
        raw = input(prompt_text).strip()
        if not raw and default is not None:
            if default >= min_value:
                return default
        try:
            value = int(raw)
        except ValueError:
            print("Invalid integer. Please enter a whole number.")
            continue

        if value < min_value:
            print(f"Value must be at least {min_value}.")
            continue
        return value


def prompt_float(
    label: str,
    min_value: float = 0.0,
    default: float | None = None,
) -> float:
    """Prompt the user for a finite float greater than or equal to ``min_value``."""
    if default is not None:
        prompt_text = f"{label} [{default:.2f}]: "
    else:
        prompt_text = f"{label}: "

    while True:
        raw = input(prompt_text).strip()
        if not raw and default is not None:
            if math.isfinite(default) and default >= min_value:
                return float(default)
        try:
            value = float(raw)
        except ValueError:
            print("Invalid number. Please enter a valid numeric value.")
            continue

        if not math.isfinite(value):
            print("Value must be a finite number.")
            continue
        if value < min_value:
            print(f"Value must be at least {min_value:.2f}.")
            continue
        return value


def prompt_confirm(label: str) -> bool:
    """Prompt the user for a yes/no confirmation (accepts y/yes/n/no)."""
    while True:
        raw = input(f"{label} (y/n): ").strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please enter 'y' or 'n'.")


def format_products_table(products: list[Product]) -> str:
    """Format a list of products into an aligned ASCII table."""
    if not products:
        return "No products found."

    headers = (
        "SKU",
        "Name",
        "Category",
        "Qty",
        "Unit Price",
        "Total Value",
        "Status",
    )
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for product in products:
        status = "LOW" if product.is_low_stock() else "OK"
        rows.append(
            (
                product.sku,
                product.name,
                product.category,
                str(product.quantity),
                f"${product.unit_price:,.2f}",
                f"${product.total_value():,.2f}",
                status,
            )
        )

    right_aligned = {3, 4, 5}
    widths = [
        max(len(headers[col]), *(len(row[col]) for row in rows))
        for col in range(len(headers))
    ]

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def _format_row(cells: tuple[str, ...]) -> str:
        formatted = []
        for idx, cell in enumerate(cells):
            if idx in right_aligned:
                formatted.append(cell.rjust(widths[idx]))
            else:
                formatted.append(cell.ljust(widths[idx]))
        return "| " + " | ".join(formatted) + " |"

    lines = [border, _format_row(headers), border]
    lines.extend(_format_row(row) for row in rows)
    lines.append(border)
    return "\n".join(lines)
