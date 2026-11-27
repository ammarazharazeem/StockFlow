# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Unit tests for custom merge sort, binary search, and filtering algorithms."""

from __future__ import annotations

import unittest

from src.algorithms import (
    binary_search_by_sku,
    filter_products,
    merge_sort_products,
)
from src.models import Product


class TestAlgorithms(unittest.TestCase):
    """Verify sorting, binary search, and filtering behavior."""

    def setUp(self) -> None:
        self.products = [
            Product("EL-103", "usb-c Dock", "Electronics", 15, 79.99, 5),
            Product("OF-201", "A4 Copier Paper", "Office Supplies", 40, 6.50, 10),
            Product("PR-102", "Mechanical Keyboard", "Peripherals", 4, 89.00, 5),
            Product("NW-301", "Gigabit Switch", "Networking", 8, 45.00, 3),
        ]

    def test_merge_sort_all_keys_ascending_and_descending(self) -> None:
        expected_orders = {
            "sku": ["EL-103", "NW-301", "OF-201", "PR-102"],
            "name": ["OF-201", "NW-301", "PR-102", "EL-103"],
            "category": ["EL-103", "NW-301", "OF-201", "PR-102"],
            "quantity": ["PR-102", "NW-301", "EL-103", "OF-201"],
            "unit_price": ["OF-201", "NW-301", "EL-103", "PR-102"],
        }

        original_snapshot = list(self.products)
        for key, expected_skus in expected_orders.items():
            with self.subTest(key=key):
                asc = merge_sort_products(self.products, key=key, reverse=False)
                desc = merge_sort_products(self.products, key=key, reverse=True)
                self.assertEqual([p.sku for p in asc], expected_skus)
                self.assertEqual(
                    [p.sku for p in desc], list(reversed(expected_skus))
                )

        # Input list must remain unchanged
        self.assertEqual(self.products, original_snapshot)

    def test_merge_sort_edge_cases_and_invalid_key(self) -> None:
        self.assertEqual(merge_sort_products([]), [])

        single = [self.products[0]]
        sorted_single = merge_sort_products(single)
        self.assertEqual(sorted_single, single)
        self.assertIsNot(sorted_single, single)

        with self.assertRaises(ValueError):
            merge_sort_products(self.products, key="invalid_key")

    def test_binary_search_by_sku(self) -> None:
        sorted_by_sku = merge_sort_products(self.products, key="sku")

        found = binary_search_by_sku(sorted_by_sku, "PR-102")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Mechanical Keyboard")

        found_ci = binary_search_by_sku(sorted_by_sku, "  el-103 ")
        self.assertIsNotNone(found_ci)
        self.assertEqual(found_ci.sku, "EL-103")

        self.assertIsNone(binary_search_by_sku(sorted_by_sku, "AA-000"))
        self.assertIsNone(binary_search_by_sku(sorted_by_sku, "NW-999"))
        self.assertIsNone(binary_search_by_sku(sorted_by_sku, "ZZ-999"))
        self.assertIsNone(binary_search_by_sku(sorted_by_sku, "   "))
        self.assertIsNone(binary_search_by_sku([], "EL-103"))

        with self.assertRaises(ValueError):
            binary_search_by_sku(sorted_by_sku, 103)  # type: ignore[arg-type]

    def test_filter_products(self) -> None:
        # Keyword matching SKU, name, and category case-insensitively
        self.assertEqual(
            [p.sku for p in filter_products(self.products, query="usb")],
            ["EL-103"],
        )
        self.assertEqual(
            [p.sku for p in filter_products(self.products, query="nw-3")],
            ["NW-301"],
        )
        self.assertEqual(
            [p.sku for p in filter_products(self.products, query="office")],
            ["OF-201"],
        )

        # Category filter only
        self.assertEqual(
            [
                p.sku
                for p in filter_products(self.products, category="peripherals")
            ],
            ["PR-102"],
        )

        # Combined query + category
        self.assertEqual(
            [
                p.sku
                for p in filter_products(
                    self.products, query="switch", category="Networking"
                )
            ],
            ["NW-301"],
        )
        self.assertEqual(
            filter_products(
                self.products, query="switch", category="Electronics"
            ),
            [],
        )

        # Empty query & None category returns all products
        self.assertEqual(len(filter_products(self.products)), 4)


if __name__ == "__main__":
    unittest.main()
