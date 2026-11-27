# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Unit tests for the Product data model and validation rules."""

from __future__ import annotations

import math
import unittest

from src.models import Product


class TestProductModel(unittest.TestCase):
    """Verify Product creation, normalization, helpers, and validation."""

    def test_valid_creation_and_normalization(self) -> None:
        product = Product(
            sku="  el-101 ",
            name="  Wireless Mouse  ",
            category="  Peripherals ",
            quantity=12,
            unit_price=25,
        )
        self.assertEqual(product.sku, "EL-101")
        self.assertEqual(product.name, "Wireless Mouse")
        self.assertEqual(product.category, "Peripherals")
        self.assertEqual(product.quantity, 12)
        self.assertIsInstance(product.unit_price, float)
        self.assertEqual(product.unit_price, 25.0)
        self.assertEqual(product.reorder_level, 5)

    def test_total_value_and_low_stock_helpers(self) -> None:
        adequate = Product("PR-1", "Keyboard", "Peripherals", 10, 49.99, 5)
        at_threshold = Product("PR-2", "Mousepad", "Peripherals", 5, 9.99, 5)
        zero_stock = Product("PR-3", "Webcam", "Electronics", 0, 39.50, 3)

        self.assertEqual(adequate.total_value(), 499.9)
        self.assertFalse(adequate.is_low_stock())

        self.assertEqual(at_threshold.total_value(), 49.95)
        self.assertTrue(at_threshold.is_low_stock())

        self.assertEqual(zero_stock.total_value(), 0.0)
        self.assertTrue(zero_stock.is_low_stock())

    def test_to_dict_and_from_dict_round_trip(self) -> None:
        original = Product("el-200", "USB-C Hub", "Networking", 7, 34.95, 4)
        payload = original.to_dict()
        self.assertEqual(
            payload,
            {
                "sku": "EL-200",
                "name": "USB-C Hub",
                "category": "Networking",
                "quantity": 7,
                "unit_price": 34.95,
                "reorder_level": 4,
            },
        )
        restored = Product.from_dict(payload)
        self.assertEqual(restored, original)

    def test_from_dict_default_reorder_and_errors(self) -> None:
        restored = Product.from_dict(
            {
                "sku": "of-10",
                "name": "A4 Paper",
                "category": "Office Supplies",
                "quantity": 20,
                "unit_price": 4.5,
            }
        )
        self.assertEqual(restored.reorder_level, 5)

        with self.assertRaises(ValueError):
            Product.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]

        with self.assertRaises(ValueError):
            Product.from_dict({"sku": "X1", "name": "Missing Fields"})

    def test_empty_or_non_string_fields_raise_value_error(self) -> None:
        invalid_text_cases = [
            ("", "Item", "Cat"),
            ("   ", "Item", "Cat"),
            ("SKU1", "", "Cat"),
            ("SKU1", "   ", "Cat"),
            ("SKU1", "Item", ""),
            ("SKU1", "Item", "   "),
            (123, "Item", "Cat"),
            ("SKU1", None, "Cat"),
            ("SKU1", "Item", 456),
        ]
        for sku, name, category in invalid_text_cases:
            with self.subTest(sku=sku, name=name, category=category):
                with self.assertRaises(ValueError):
                    Product(sku, name, category, 1, 10.0)  # type: ignore[arg-type]

    def test_negative_numbers_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            Product("S1", "Item", "Cat", -1, 10.0, 5)
        with self.assertRaises(ValueError):
            Product("S1", "Item", "Cat", 1, -0.01, 5)
        with self.assertRaises(ValueError):
            Product("S1", "Item", "Cat", 1, 10.0, -1)

    def test_boolean_numeric_values_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Product("S1", "Item", "Cat", True, 10.0, 5)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Product("S1", "Item", "Cat", 5, False, 5)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Product("S1", "Item", "Cat", 5, 10.0, True)  # type: ignore[arg-type]

    def test_non_finite_and_invalid_numeric_types_are_rejected(self) -> None:
        for bad_price in (math.nan, math.inf, -math.inf, "9.99", None):
            with self.subTest(bad_price=bad_price):
                with self.assertRaises(ValueError):
                    Product("S1", "Item", "Cat", 5, bad_price, 5)  # type: ignore[arg-type]

        for bad_int in (2.5, "5", None):
            with self.subTest(bad_int=bad_int):
                with self.assertRaises(ValueError):
                    Product("S1", "Item", "Cat", bad_int, 10.0, 5)  # type: ignore[arg-type]
                with self.assertRaises(ValueError):
                    Product("S1", "Item", "Cat", 5, 10.0, bad_int)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
