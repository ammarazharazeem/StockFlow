# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Unit tests for JSON persistence and InventoryManager core operations."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.manager import InventoryManager
from src.models import Product
from src.storage import load_products, save_products

_TESTS_DIR = Path(__file__).resolve().parent


class TestStorageAndManager(unittest.TestCase):
    """Verify storage edge cases and InventoryManager CRUD, search, and summary."""

    def test_load_missing_and_corrupted_json(self) -> None:
        with tempfile.TemporaryDirectory(dir=_TESTS_DIR) as tmp_dir:
            root = Path(tmp_dir)
            missing_file = root / "does_not_exist.json"
            self.assertEqual(load_products(missing_file), [])

            corrupted_file = root / "corrupt.json"
            corrupted_file.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_products(corrupted_file)

            non_list_file = root / "non_list.json"
            non_list_file.write_text('{"sku": "A1"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_products(non_list_file)

    def test_save_creates_parent_directories_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory(dir=_TESTS_DIR) as tmp_dir:
            nested_path = Path(tmp_dir) / "nested" / "sub" / "inventory.json"
            items = [
                Product("EL-101", "Monitor", "Electronics", 6, 199.99, 3),
                Product("PR-201", "Mouse", "Peripherals", 2, 19.50, 5),
            ]
            save_products(nested_path, items)
            self.assertTrue(nested_path.exists())

            loaded = load_products(nested_path)
            self.assertEqual(loaded, items)

    def test_manager_crud_categories_search_and_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir=_TESTS_DIR) as tmp_dir:
            storage_path = Path(tmp_dir) / "inventory.json"
            manager = InventoryManager(filepath=storage_path)

            p1 = Product("el-101", "27in Monitor", "Electronics", 6, 200.0, 4)
            p2 = Product("pr-201", "USB Mouse", "Peripherals", 3, 20.0, 5)
            p3 = Product("st-301", "1TB NVMe SSD", "Storage", 0, 75.0, 4)

            manager.add_product(p1)
            manager.add_product(p2)
            manager.add_product(p3)

            # Duplicate SKU rejected
            with self.assertRaises(ValueError):
                manager.add_product(
                    Product("EL-101", "Duplicate", "Electronics", 1, 10.0)
                )

            # O(1) lookup & binary search
            self.assertEqual(manager.get_product("el-101"), p1)
            self.assertIsNone(manager.get_product("MISSING"))
            self.assertEqual(manager.search_by_sku_binary("pr-201"), p2)
            self.assertIsNone(manager.search_by_sku_binary("NO-SUCH-SKU"))

            # Low-stock items (sorted by quantity ascending)
            low_stock = manager.get_low_stock_products()
            self.assertEqual([p.sku for p in low_stock], ["ST-301", "PR-201"])

            # Summary metrics
            self.assertEqual(
                manager.get_summary(),
                {
                    "total_skus": 3,
                    "total_units": 9,
                    "total_value": 1260.0,
                    "low_stock_count": 2,
                    "category_count": 3,
                },
            )
            self.assertEqual(
                manager.get_categories(),
                ["Electronics", "Peripherals", "Storage"],
            )

            # Update product & verify dynamic category set update
            updated = manager.update_product(
                "pr-201", quantity=10, category="Accessories"
            )
            self.assertEqual(updated.quantity, 10)
            self.assertFalse(updated.is_low_stock())
            self.assertEqual(
                manager.get_categories(),
                ["Accessories", "Electronics", "Storage"],
            )

            # Invalid update leaves state intact
            with self.assertRaises(ValueError):
                manager.update_product("PR-201", quantity=-5)
            self.assertEqual(manager.get_product("PR-201").quantity, 10)

            # Missing SKU raises KeyError on update and delete
            with self.assertRaises(KeyError):
                manager.update_product("UNKNOWN", quantity=1)
            with self.assertRaises(KeyError):
                manager.delete_product("UNKNOWN")

            # Delete removes category when no products remain in it
            removed = manager.delete_product("st-301")
            self.assertEqual(removed.sku, "ST-301")
            self.assertEqual(
                manager.get_categories(), ["Accessories", "Electronics"]
            )

            # Save and reload into fresh InventoryManager
            manager.save()
            reloaded_manager = InventoryManager(filepath=storage_path)
            reloaded = reloaded_manager.load()
            self.assertEqual(len(reloaded), 2)
            self.assertEqual(
                reloaded_manager.get_summary(),
                {
                    "total_skus": 2,
                    "total_units": 16,
                    "total_value": 1400.0,
                    "low_stock_count": 0,
                    "category_count": 2,
                },
            )


if __name__ == "__main__":
    unittest.main()
