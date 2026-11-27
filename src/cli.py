# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Menu-driven command-line interface for StockFlow."""

from __future__ import annotations

from pathlib import Path

from src.cli_utils import (
    format_products_table,
    prompt_confirm,
    prompt_float,
    prompt_int,
    prompt_non_empty,
)
from src.manager import InventoryManager
from src.models import Product

_VALID_SORT_KEYS = ("name", "sku", "category", "quantity", "unit_price")


class StockFlowCLI:
    """Interactive text-based UI delegating all inventory operations to InventoryManager."""

    def __init__(
        self,
        manager: InventoryManager | None = None,
        filepath: Path | str | None = None,
    ) -> None:
        """Initialize the CLI with an existing or newly created InventoryManager."""
        self.manager = (
            manager if manager is not None else InventoryManager(filepath=filepath)
        )

    def run(self) -> None:
        """Load inventory and run the interactive menu loop until exit."""
        print("=== StockFlow Inventory & Stock Control ===")
        self._load_on_startup()

        actions = {
            "1": self._handle_view_all,
            "2": self._handle_add_product,
            "3": self._handle_search_products,
            "4": self._handle_update_product,
            "5": self._handle_delete_product,
            "6": self._handle_low_stock_alerts,
            "7": self._handle_view_summary,
        }

        try:
            while True:
                self._print_menu()
                choice = input("Select an option (1-8): ").strip()

                if choice == "8":
                    self._handle_save_and_exit()
                    break

                handler = actions.get(choice)
                if handler is None:
                    print("Invalid menu choice. Please select a number between 1 and 8.")
                    continue

                handler()
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting StockFlow CLI without unsaved changes.")
        except EOFError:
            print("\nEnd of input reached. Exiting StockFlow CLI.")

    def _load_on_startup(self) -> None:
        """Attempt to load persisted inventory data with graceful error handling."""
        try:
            products = self.manager.load()
            print(
                f"Loaded {len(products)} product(s) from '{self.manager.filepath}'."
            )
        except ValueError as exc:
            print(f"Warning: Failed to load inventory file: {exc}")
            print("Starting with an empty in-memory inventory.")

    def _auto_save(self) -> None:
        """Persist changes after mutating inventory operations."""
        try:
            self.manager.save()
        except ValueError as exc:
            print(f"Warning: Unable to save inventory changes: {exc}")

    @staticmethod
    def _print_menu() -> None:
        """Display the main StockFlow CLI menu options."""
        print("\n--- Main Menu ---")
        print("1. View all products")
        print("2. Add a new product")
        print("3. Search products")
        print("4. Update an existing product")
        print("5. Delete a product")
        print("6. View low-stock alerts")
        print("7. View inventory summary & analytics")
        print("8. Save & Exit")

    @staticmethod
    def _prompt_sort_options() -> tuple[str, bool]:
        """Prompt the user for a valid sort field and ascending/descending order."""
        keys_display = ", ".join(_VALID_SORT_KEYS)
        while True:
            sort_key = (
                input(f"Sort by ({keys_display}) [name]: ").strip().lower()
                or "name"
            )
            if sort_key in _VALID_SORT_KEYS:
                break
            print(f"Invalid sort key '{sort_key}'. Choose from: {keys_display}.")

        while True:
            order = input("Order (asc/desc) [asc]: ").strip().lower() or "asc"
            if order in {"asc", "a"}:
                return sort_key, False
            if order in {"desc", "d"}:
                return sort_key, True
            print("Invalid order. Please enter 'asc' or 'desc'.")

    def _handle_view_all(self) -> None:
        """Display all inventory items sorted by the user's chosen criteria."""
        sort_key, reverse = self._prompt_sort_options()
        products = self.manager.list_products(sort_by=sort_key, reverse=reverse)
        print()
        print(format_products_table(products))

    def _handle_add_product(self) -> None:
        """Collect validated fields and add a new product to inventory."""
        print("\n--- Add New Product ---")
        sku = prompt_non_empty("SKU")
        name = prompt_non_empty("Product Name")
        category = prompt_non_empty("Category")
        quantity = prompt_int("Quantity", min_value=0)
        unit_price = prompt_float("Unit Price", min_value=0.0)
        reorder_level = prompt_int("Reorder Level", min_value=0, default=5)

        try:
            product = Product(
                sku=sku,
                name=name,
                category=category,
                quantity=quantity,
                unit_price=unit_price,
                reorder_level=reorder_level,
            )
            self.manager.add_product(product)
        except ValueError as exc:
            print(f"Error adding product: {exc}")
            return

        self._auto_save()
        print(f"Added product '{product.sku}' ({product.name}).")

    def _handle_search_products(self) -> None:
        """Search inventory either by binary SKU lookup or keyword/category filter."""
        print("\n--- Search Products ---")
        print("a) Exact SKU lookup (Binary Search)")
        print("b) Keyword & optional category filter")

        while True:
            mode = input("Choose search mode (a/b): ").strip().lower()
            if mode in {"a", "b"}:
                break
            print("Invalid option. Please enter 'a' or 'b'.")

        if mode == "a":
            sku = prompt_non_empty("Enter SKU")
            product = self.manager.search_by_sku_binary(sku)
            if product is None:
                print(f"No product found with SKU '{sku.strip().upper()}'.")
                return
            print()
            print(format_products_table([product]))
            return

        query = input("Search keyword (leave blank for all): ").strip()
        category_input = input("Exact category filter (optional): ").strip()
        category = category_input if category_input else None
        results = self.manager.search_products(query=query, category=category)
        print()
        print(format_products_table(results))

    def _handle_update_product(self) -> None:
        """Update an existing product while allowing Enter to keep current values."""
        print("\n--- Update Product ---")
        sku = prompt_non_empty("Enter SKU to update")
        existing = self.manager.get_product(sku)
        if existing is None:
            print(f"Product with SKU '{sku.strip().upper()}' not found.")
            return

        print("\nCurrent product details (press Enter to keep existing value):")
        print(format_products_table([existing]))

        name = prompt_non_empty("Product Name", default=existing.name)
        category = prompt_non_empty("Category", default=existing.category)
        quantity = prompt_int("Quantity", min_value=0, default=existing.quantity)
        unit_price = prompt_float(
            "Unit Price", min_value=0.0, default=existing.unit_price
        )
        reorder_level = prompt_int(
            "Reorder Level", min_value=0, default=existing.reorder_level
        )

        try:
            updated = self.manager.update_product(
                existing.sku,
                name=name,
                category=category,
                quantity=quantity,
                unit_price=unit_price,
                reorder_level=reorder_level,
            )
        except (KeyError, ValueError) as exc:
            print(f"Error updating product: {exc}")
            return

        self._auto_save()
        print(f"Updated product '{updated.sku}':")
        print(format_products_table([updated]))

    def _handle_delete_product(self) -> None:
        """Display product details and delete after explicit confirmation."""
        print("\n--- Delete Product ---")
        sku = prompt_non_empty("Enter SKU to delete")
        existing = self.manager.get_product(sku)
        if existing is None:
            print(f"Product with SKU '{sku.strip().upper()}' not found.")
            return

        print()
        print(format_products_table([existing]))
        if not prompt_confirm(
            f"Are you sure you want to delete '{existing.sku}' ({existing.name})?"
        ):
            print("Deletion cancelled.")
            return

        try:
            removed = self.manager.delete_product(existing.sku)
        except (KeyError, ValueError) as exc:
            print(f"Error deleting product: {exc}")
            return

        self._auto_save()
        print(f"Deleted product '{removed.sku}' ({removed.name}).")

    def _handle_low_stock_alerts(self) -> None:
        """Display all products at or below their reorder level."""
        print("\n--- Low-Stock Alerts ---")
        low_stock = self.manager.get_low_stock_products()
        if not low_stock:
            print("No low-stock alerts. All products are adequately stocked.")
            return
        print(f"{len(low_stock)} product(s) require attention:")
        print(format_products_table(low_stock))

    def _handle_view_summary(self) -> None:
        """Display aggregate inventory statistics and active categories."""
        summary = self.manager.get_summary()
        categories = self.manager.get_categories()
        categories_text = ", ".join(categories) if categories else "None"

        print("\n--- Inventory Summary & Analytics ---")
        print(f"Total SKUs      : {summary['total_skus']}")
        print(f"Total Units     : {summary['total_units']}")
        print(f"Total Value     : £{summary['total_value']:,.2f}")
        print(f"Low-Stock Count : {summary['low_stock_count']}")
        print(f"Category Count  : {summary['category_count']}")
        print(f"Categories      : {categories_text}")

    def _handle_save_and_exit(self) -> None:
        """Persist inventory to disk and exit cleanly."""
        try:
            self.manager.save()
            print(f"Inventory saved to '{self.manager.filepath}'. Goodbye!")
        except ValueError as exc:
            print(f"Error saving inventory: {exc}")
