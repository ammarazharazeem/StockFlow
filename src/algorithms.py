# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Custom sorting, searching, and filtering algorithms for StockFlow."""

from __future__ import annotations

from typing import Callable

from src.models import Product

_SORT_KEY_EXTRACTORS: dict[str, Callable[[Product], str | int | float]] = {
    "sku": lambda product: product.sku.lower(),
    "name": lambda product: product.name.lower(),
    "category": lambda product: product.category.lower(),
    "quantity": lambda product: product.quantity,
    "unit_price": lambda product: product.unit_price,
}


def merge_sort_products(
    products: list[Product],
    key: str = "name",
    reverse: bool = False,
) -> list[Product]:
    """Sort products using a custom merge sort algorithm without built-in sort.

    Args:
        products: List of Product instances to sort.
        key: Field name to sort by ('sku', 'name', 'category', 'quantity',
            or 'unit_price'). String comparisons are case-insensitive.
        reverse: When True, sort in descending order.

    Returns:
        A new sorted list of Product instances.

    Raises:
        ValueError: If ``key`` is not a supported sort field.
    """
    if not isinstance(key, str) or key not in _SORT_KEY_EXTRACTORS:
        supported = ", ".join(_SORT_KEY_EXTRACTORS.keys())
        raise ValueError(
            f"Unsupported sort key '{key}'. Supported keys: {supported}."
        )

    if len(products) <= 1:
        return list(products)

    key_fn = _SORT_KEY_EXTRACTORS[key]
    return _merge_sort_recursive(list(products), key_fn, reverse)


def _merge_sort_recursive(
    items: list[Product],
    key_fn: Callable[[Product], str | int | float],
    reverse: bool,
) -> list[Product]:
    """Recursively split and merge-sort a list of products."""
    if len(items) <= 1:
        return items

    mid = len(items) // 2
    left = _merge_sort_recursive(items[:mid], key_fn, reverse)
    right = _merge_sort_recursive(items[mid:], key_fn, reverse)
    return _merge_halves(left, right, key_fn, reverse)


def _merge_halves(
    left: list[Product],
    right: list[Product],
    key_fn: Callable[[Product], str | int | float],
    reverse: bool,
) -> list[Product]:
    """Merge two sorted product halves into a single ordered list."""
    merged: list[Product] = []
    left_index = 0
    right_index = 0

    while left_index < len(left) and right_index < len(right):
        left_val = key_fn(left[left_index])
        right_val = key_fn(right[right_index])

        take_left = (
            left_val >= right_val if reverse else left_val <= right_val
        )
        if take_left:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    if left_index < len(left):
        merged.extend(left[left_index:])
    if right_index < len(right):
        merged.extend(right[right_index:])

    return merged


def binary_search_by_sku(
    sorted_products: list[Product],
    target_sku: str,
) -> Product | None:
    """Perform case-insensitive binary search for a SKU on a SKU-sorted list.

    Args:
        sorted_products: Product list sorted in ascending order by ``sku``.
        target_sku: SKU string to locate.

    Returns:
        The matching Product if found, otherwise None.

    Raises:
        ValueError: If ``target_sku`` is not a string.
    """
    if not isinstance(target_sku, str):
        raise ValueError("Target SKU must be a string.")

    normalized_target = target_sku.strip().lower()
    if not normalized_target or not sorted_products:
        return None

    low = 0
    high = len(sorted_products) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_product = sorted_products[mid]
        mid_sku = mid_product.sku.lower()

        if mid_sku == normalized_target:
            return mid_product
        if mid_sku < normalized_target:
            low = mid + 1
        else:
            high = mid - 1

    return None


def filter_products(
    products: list[Product],
    query: str = "",
    category: str | None = None,
) -> list[Product]:
    """Filter products by partial query across SKU/name/category and optional category.

    Args:
        products: Product list to filter.
        query: Case-insensitive substring matched against sku, name, and category.
        category: Optional exact category filter (case-insensitive).

    Returns:
        A new list containing all matching Product instances.

    Raises:
        ValueError: If ``query`` is not a string or ``category`` is neither str nor None.
    """
    if not isinstance(query, str):
        raise ValueError("Search query must be a string.")
    if category is not None and not isinstance(category, str):
        raise ValueError("Category filter must be a string or None.")

    normalized_query = query.strip().lower()
    normalized_category = (
        category.strip().lower() if category and category.strip() else None
    )

    results: list[Product] = []
    for product in products:
        if normalized_category is not None:
            if product.category.lower() != normalized_category:
                continue

        if normalized_query:
            matches_query = (
                normalized_query in product.sku.lower()
                or normalized_query in product.name.lower()
                or normalized_query in product.category.lower()
            )
            if not matches_query:
                continue

        results.append(product)

    return results
