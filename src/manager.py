# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Core inventory management service coordinating models, algorithms, and storage."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.algorithms import binary_search_by_sku, filter_products, merge_sort_products
from src.models import Product
from src.storage import InventoryStorage

DEFAULT_INVENTORY_PATH = Path("data") / "inventory.json"
_UPDATABLE_FIELDS = frozenset(
    {"sku", "name", "category", "quantity", "unit_price", "reorder_level"}
)


class InventoryManager:
    """Manages inventory products with O(1) SKU lookup, category tracking, and persistence."""

    def __init__(
        self,
        filepath: Path | str | None = None,
        auto_load: bool = False,
    ) -> None:
        """Initialize the inventory manager with an optional storage path.

        Args:
            filepath: Optional JSON storage path; defaults to ``data/inventory.json``.
            auto_load: When True, immediately load existing data from ``filepath``.
        """
        resolved_path = (
            Path(filepath) if filepath is not None else DEFAULT_INVENTORY_PATH
        )
        self._storage = InventoryStorage(resolved_path)
        self._products: dict[str, Product] = {}
        self._categories: set[str] = set()

        if auto_load:
            self.load()

    @property
    def filepath(self) -> Path:
        """Return the configured JSON storage path."""
        return self._storage.filepath

    def _rebuild_categories(self) -> None:
        """Synchronize the tracked category set with current products."""
        self._categories = {product.category for product in self._products.values()}

    @staticmethod
    def _normalize_sku(sku: Any) -> str:
        """Validate and normalize a SKU string for dictionary lookup."""
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string.")
        normalized = sku.strip().upper()
        if not normalized:
            raise ValueError("SKU cannot be empty or whitespace.")
        return normalized

    def load(self) -> list[Product]:
        """Load products from disk, replacing current in-memory inventory.

        Returns:
            List of loaded Product instances.

        Raises:
            ValueError: If storage contains invalid JSON, invalid records, or
                duplicate SKUs.
        """
        loaded_products = self._storage.load()
        new_products: dict[str, Product] = {}
        for product in loaded_products:
            if product.sku in new_products:
                raise ValueError(
                    f"Duplicate SKU '{product.sku}' found in inventory file."
                )
            new_products[product.sku] = product

        self._products = new_products
        self._rebuild_categories()
        return list(self._products.values())

    def save(self) -> None:
        """Persist current inventory products sorted by SKU to disk."""
        ordered_products = self.list_products(sort_by="sku")
        self._storage.save(ordered_products)

    def add_product(self, product: Product) -> None:
        """Add a new product to the inventory.

        Raises:
            ValueError: If ``product`` is not a Product or its SKU already exists.
        """
        if not isinstance(product, Product):
            raise ValueError("Expected a Product instance.")
        if product.sku in self._products:
            raise ValueError(
                f"Product with SKU '{product.sku}' already exists."
            )

        self._products[product.sku] = product
        self._categories.add(product.category)

    def get_product(self, sku: str) -> Product | None:
        """Retrieve a product by SKU in O(1) time, or return None if missing."""
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string.")
        normalized = sku.strip().upper()
        if not normalized:
            return None
        return self._products.get(normalized)

    def update_product(self, sku: str, **updates: Any) -> Product:
        """Update fields of an existing product after validating the new state.

        Raises:
            KeyError: If no product matches ``sku``.
            ValueError: If an unknown field is passed, validation fails, or a
                renamed SKU collides with an existing product.
        """
        normalized_sku = self._normalize_sku(sku)
        if normalized_sku not in self._products:
            raise KeyError(f"Product with SKU '{normalized_sku}' not found.")

        unknown_fields = set(updates.keys()) - _UPDATABLE_FIELDS
        if unknown_fields:
            unknown_list = ", ".join(sorted(unknown_fields))
            raise ValueError(f"Unsupported update field(s): {unknown_list}.")

        existing = self._products[normalized_sku]
        candidate_data = existing.to_dict()
        candidate_data.update(updates)
        updated_product = Product.from_dict(candidate_data)

        if (
            updated_product.sku != normalized_sku
            and updated_product.sku in self._products
        ):
            raise ValueError(
                f"Product with SKU '{updated_product.sku}' already exists."
            )

        if updated_product.sku != normalized_sku:
            del self._products[normalized_sku]
        self._products[updated_product.sku] = updated_product
        self._rebuild_categories()
        return updated_product

    def delete_product(self, sku: str) -> Product:
        """Remove and return a product by SKU, updating tracked categories.

        Raises:
            KeyError: If no product matches ``sku``.
        """
        normalized_sku = self._normalize_sku(sku)
        if normalized_sku not in self._products:
            raise KeyError(f"Product with SKU '{normalized_sku}' not found.")

        removed = self._products.pop(normalized_sku)
        self._rebuild_categories()
        return removed

    def list_products(
        self,
        sort_by: str = "name",
        reverse: bool = False,
    ) -> list[Product]:
        """Return all products sorted using custom merge sort."""
        return merge_sort_products(
            list(self._products.values()),
            key=sort_by,
            reverse=reverse,
        )

    def search_by_sku_binary(self, sku: str) -> Product | None:
        """Sort inventory by SKU and locate a product via binary search."""
        sorted_by_sku = merge_sort_products(
            list(self._products.values()),
            key="sku",
        )
        return binary_search_by_sku(sorted_by_sku, sku)

    def search_products(
        self,
        query: str = "",
        category: str | None = None,
    ) -> list[Product]:
        """Search products by partial query and optional exact category filter."""
        return filter_products(
            list(self._products.values()),
            query=query,
            category=category,
        )

    def get_low_stock_products(self) -> list[Product]:
        """Return all products at or below their reorder level, sorted by quantity."""
        sorted_products = self.list_products(sort_by="quantity")
        return [product for product in sorted_products if product.is_low_stock()]

    def get_categories(self) -> list[str]:
        """Return a sorted list of unique product categories currently in stock."""
        return sorted(self._categories, key=str.lower)

    def get_summary(self) -> dict[str, int | float]:
        """Compute aggregate inventory metrics across all stocked products."""
        products = list(self._products.values())
        total_units = sum(product.quantity for product in products)
        total_value = round(
            sum(product.quantity * product.unit_price for product in products), 2
        )
        low_stock_count = sum(
            1 for product in products if product.is_low_stock()
        )
        return {
            "total_skus": len(products),
            "total_units": total_units,
            "total_value": total_value,
            "low_stock_count": low_stock_count,
            "category_count": len(self._categories),
        }
