# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Tkinter GUI front end for StockFlow over the shared InventoryManager."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from src.gui_dialogs import ProductDialog
from src.manager import InventoryManager
from src.models import Product

_SORT_OPTIONS = ("name", "sku", "category", "quantity", "unit_price")


class StockFlowGUI:
    """Desktop Tkinter front end delegating all business logic to InventoryManager."""

    def __init__(
        self,
        root: tk.Tk | None = None,
        manager: InventoryManager | None = None,
        filepath: Path | str | None = None,
    ) -> None:
        """Initialize the StockFlow GUI window, widgets, and inventory state."""
        self.root = root if root is not None else tk.Tk()
        self.manager = (
            manager if manager is not None else InventoryManager(filepath=filepath)
        )

        self.root.title("StockFlow — Inventory & Stock Control")
        self.root.geometry("1040x640")
        self.root.minsize(860, 520)

        self._summary_vars: dict[str, tk.StringVar] = {
            "total_skus": tk.StringVar(value="Total SKUs: 0"),
            "total_units": tk.StringVar(value="Total Units: 0"),
            "total_value": tk.StringVar(value="Total Value: $0.00"),
            "low_stock_count": tk.StringVar(value="Low Stock: 0"),
            "category_count": tk.StringVar(value="Categories: 0"),
        }
        self._search_var = tk.StringVar()
        self._category_var = tk.StringVar(value="All")
        self._sku_lookup_var = tk.StringVar()
        self._sort_key_var = tk.StringVar(value="name")
        self._sort_desc_var = tk.BooleanVar(value=False)
        self._low_stock_only_var = tk.BooleanVar(value=False)
        self._status_var = tk.StringVar(value="Ready.")

        self._build_layout()
        self._bind_events()
        self._load_on_startup()
        self.refresh_view()

    def _build_layout(self) -> None:
        """Build the responsive Tkinter layout using ttk widgets."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        self._build_summary_bar()
        self._build_toolbar()
        self._build_inventory_table()
        self._build_action_bar()
        self._build_status_bar()

    def _build_summary_bar(self) -> None:
        """Create the top bar displaying live inventory analytics."""
        summary_frame = ttk.LabelFrame(
            self.root, text="Inventory Summary", padding=(12, 8)
        )
        summary_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        keys = (
            "total_skus",
            "total_units",
            "total_value",
            "low_stock_count",
            "category_count",
        )
        for col, key in enumerate(keys):
            summary_frame.columnconfigure(col, weight=1)
            label = ttk.Label(
                summary_frame,
                textvariable=self._summary_vars[key],
                font=("TkDefaultFont", 10, "bold"),
            )
            label.grid(row=0, column=col, sticky="w", padx=6)

    def _build_toolbar(self) -> None:
        """Create the search, category filter, SKU lookup, and sort toolbar."""
        toolbar = ttk.LabelFrame(
            self.root, text="Search, Filter & Sort", padding=(12, 8)
        )
        toolbar.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        toolbar.columnconfigure(1, weight=1)
        toolbar.columnconfigure(6, weight=1)

        # Row 0: Keyword search, Category filter, Low-stock toggle, Reset
        ttk.Label(toolbar, text="Search:").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=4
        )
        self._search_entry = ttk.Entry(
            toolbar, textvariable=self._search_var, width=26
        )
        self._search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=4)

        ttk.Label(toolbar, text="Category:").grid(
            row=0, column=2, sticky="w", padx=(0, 6), pady=4
        )
        self._category_combo = ttk.Combobox(
            toolbar,
            textvariable=self._category_var,
            values=("All",),
            state="readonly",
            width=18,
        )
        self._category_combo.grid(
            row=0, column=3, sticky="w", padx=(0, 12), pady=4
        )

        self._low_stock_check = ttk.Checkbutton(
            toolbar,
            text="Low Stock Only",
            variable=self._low_stock_only_var,
            command=self._on_filter_changed,
        )
        self._low_stock_check.grid(
            row=0, column=4, sticky="w", padx=(0, 12), pady=4
        )

        ttk.Button(
            toolbar, text="Reset Filters", command=self.reset_filters
        ).grid(row=0, column=5, sticky="e", pady=4)

        # Row 1: Exact SKU binary lookup & Sort controls
        ttk.Label(toolbar, text="Exact SKU:").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=4
        )
        sku_frame = ttk.Frame(toolbar)
        sku_frame.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=4)
        sku_frame.columnconfigure(0, weight=1)

        self._sku_lookup_entry = ttk.Entry(
            sku_frame, textvariable=self._sku_lookup_var, width=18
        )
        self._sku_lookup_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            sku_frame, text="Find SKU", command=self._on_find_sku
        ).grid(row=0, column=1, sticky="e")

        ttk.Label(toolbar, text="Sort By:").grid(
            row=1, column=2, sticky="w", padx=(0, 6), pady=4
        )
        self._sort_combo = ttk.Combobox(
            toolbar,
            textvariable=self._sort_key_var,
            values=_SORT_OPTIONS,
            state="readonly",
            width=18,
        )
        self._sort_combo.grid(row=1, column=3, sticky="w", padx=(0, 12), pady=4)

        self._sort_desc_check = ttk.Checkbutton(
            toolbar,
            text="Descending",
            variable=self._sort_desc_var,
            command=self._on_filter_changed,
        )
        self._sort_desc_check.grid(
            row=1, column=4, sticky="w", padx=(0, 12), pady=4
        )

    def _build_inventory_table(self) -> None:
        """Create the scrollable ttk.Treeview displaying inventory rows."""
        table_frame = ttk.Frame(self.root, padding=(12, 4))
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = (
            "sku",
            "name",
            "category",
            "quantity",
            "unit_price",
            "total_value",
            "status",
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings = {
            "sku": ("SKU", 110, "w"),
            "name": ("Name", 240, "w"),
            "category": ("Category", 150, "w"),
            "quantity": ("Qty", 80, "e"),
            "unit_price": ("Unit Price", 110, "e"),
            "total_value": ("Total Value", 120, "e"),
            "status": ("Status", 85, "center"),
        }
        for col_id, (text, width, anchor) in headings.items():
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=anchor)

        self.tree.tag_configure(
            "low_stock", background="#FDE8E8", foreground="#9B1C1C"
        )
        self.tree.tag_configure("normal_stock", background="#FFFFFF")

        v_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        h_scroll = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

    def _build_action_bar(self) -> None:
        """Create the CRUD and manual save action buttons."""
        action_frame = ttk.Frame(self.root, padding=(12, 8))
        action_frame.grid(row=3, column=0, sticky="ew")

        ttk.Button(
            action_frame, text="Add Product", command=self._on_add_product
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            action_frame, text="Edit Selected", command=self._on_edit_selected
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            action_frame,
            text="Delete Selected",
            command=self._on_delete_selected,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            action_frame, text="Save Now", command=self._on_save_now
        ).pack(side="right")

    def _build_status_bar(self) -> None:
        """Create the bottom status bar displaying operation feedback."""
        status_frame = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        status_frame.grid(row=4, column=0, sticky="ew")
        ttk.Separator(status_frame, orient="horizontal").pack(
            fill="x", pady=(0, 4)
        )
        ttk.Label(
            status_frame, textvariable=self._status_var, anchor="w"
        ).pack(fill="x")

    def _bind_events(self) -> None:
        """Wire keyboard, selection, and filter control callbacks."""
        self._search_var.trace_add("write", lambda *_args: self._on_filter_changed())
        self._category_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._on_filter_changed()
        )
        self._sort_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._on_filter_changed()
        )
        self._sku_lookup_entry.bind("<Return>", lambda _event: self._on_find_sku())
        self.tree.bind("<Double-1>", lambda _event: self._on_edit_selected())

    def _load_on_startup(self) -> None:
        """Load persisted inventory on startup, warning gracefully on corruption."""
        try:
            loaded = self.manager.load()
            self._status_var.set(
                f"Loaded {len(loaded)} product(s) from '{self.manager.filepath}'."
            )
        except ValueError as exc:
            self._status_var.set("Warning: Failed to load inventory file.")
            messagebox.showwarning(
                "Inventory Load Warning",
                f"Could not load '{self.manager.filepath}':\n{exc}\n\n"
                "Starting with an empty in-memory inventory.",
                parent=self.root,
            )

    def _auto_save(self) -> bool:
        """Persist inventory changes and report any storage errors."""
        try:
            self.manager.save()
            return True
        except ValueError as exc:
            messagebox.showerror("Save Error", str(exc), parent=self.root)
            self._status_var.set(f"Save failed: {exc}")
            return False

    def _update_summary_bar(self) -> None:
        """Refresh top summary metrics from InventoryManager."""
        summary = self.manager.get_summary()
        self._summary_vars["total_skus"].set(
            f"Total SKUs: {summary['total_skus']}"
        )
        self._summary_vars["total_units"].set(
            f"Total Units: {summary['total_units']}"
        )
        self._summary_vars["total_value"].set(
            f"Total Value: ${summary['total_value']:,.2f}"
        )
        self._summary_vars["low_stock_count"].set(
            f"Low Stock: {summary['low_stock_count']}"
        )
        self._summary_vars["category_count"].set(
            f"Categories: {summary['category_count']}"
        )

    def _update_category_options(self) -> None:
        """Synchronize the category dropdown with dynamic categories."""
        categories = ["All", *self.manager.get_categories()]
        self._category_combo.configure(values=categories)
        if self._category_var.get() not in categories:
            self._category_var.set("All")

    def _get_displayed_products(self) -> list[Product]:
        """Retrieve sorted and filtered products strictly via InventoryManager."""
        sort_key = self._sort_key_var.get()
        if sort_key not in _SORT_OPTIONS:
            sort_key = "name"
        reverse = self._sort_desc_var.get()

        products = self.manager.list_products(sort_by=sort_key, reverse=reverse)

        query = self._search_var.get().strip()
        selected_category = self._category_var.get()
        category_arg = None if selected_category == "All" else selected_category

        if query or category_arg is not None:
            matched_skus = {
                product.sku
                for product in self.manager.search_products(
                    query=query, category=category_arg
                )
            }
            products = [p for p in products if p.sku in matched_skus]

        if self._low_stock_only_var.get():
            low_stock_skus = {
                product.sku for product in self.manager.get_low_stock_products()
            }
            products = [p for p in products if p.sku in low_stock_skus]

        return products

    def refresh_table(self) -> list[Product]:
        """Populate the Treeview with the current sorted/filtered product list."""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        products = self._get_displayed_products()
        for product in products:
            is_low = product.is_low_stock()
            status = "LOW" if is_low else "OK"
            tag = "low_stock" if is_low else "normal_stock"
            self.tree.insert(
                "",
                "end",
                iid=product.sku,
                values=(
                    product.sku,
                    product.name,
                    product.category,
                    product.quantity,
                    f"${product.unit_price:,.2f}",
                    f"${product.total_value():,.2f}",
                    status,
                ),
                tags=(tag,),
            )
        return products

    def refresh_view(self) -> None:
        """Refresh category options, summary bar, and inventory table."""
        self._update_category_options()
        self._update_summary_bar()
        self.refresh_table()

    def _on_filter_changed(self) -> None:
        """Re-render the table and update the status bar when filters change."""
        displayed = self.refresh_table()
        if self._low_stock_only_var.get():
            self._status_var.set(
                f"Showing {len(displayed)} low-stock item(s)."
            )
        else:
            self._status_var.set(f"Showing {len(displayed)} product(s).")

    def reset_filters(self) -> None:
        """Clear all search, category, SKU, and low-stock filters."""
        self._search_var.set("")
        self._category_var.set("All")
        self._sku_lookup_var.set("")
        self._low_stock_only_var.set(False)
        self._sort_key_var.set("name")
        self._sort_desc_var.set(False)
        displayed = self.refresh_table()
        self._status_var.set(
            f"Filters reset. Showing {len(displayed)} product(s)."
        )

    def _on_find_sku(self) -> None:
        """Locate and highlight a product using binary search by exact SKU."""
        raw_sku = self._sku_lookup_var.get().strip()
        if not raw_sku:
            self._status_var.set("Enter a SKU to search.")
            return

        product = self.manager.search_by_sku_binary(raw_sku)
        if product is None:
            self._status_var.set(
                f"No product found with SKU '{raw_sku.upper()}'."
            )
            messagebox.showinfo(
                "SKU Lookup",
                f"No product found with SKU '{raw_sku.upper()}'.",
                parent=self.root,
            )
            return

        if not self.tree.exists(product.sku):
            self.reset_filters()

        self.tree.selection_set(product.sku)
        self.tree.focus(product.sku)
        self.tree.see(product.sku)
        self._status_var.set(
            f"Found {product.sku} ({product.name}) via binary search."
        )

    def _get_selected_sku(self) -> str | None:
        """Return the SKU of the currently selected Treeview row, if any."""
        selection = self.tree.selection()
        if not selection:
            return None
        return str(selection[0])

    def _on_add_product(self) -> None:
        """Open the modal Add Product dialog and persist valid additions."""
        dialog = ProductDialog(self.root, title="Add New Product")
        self.root.wait_window(dialog)
        if dialog.result is None:
            return

        try:
            self.manager.add_product(dialog.result)
        except ValueError as exc:
            messagebox.showerror("Add Product Error", str(exc), parent=self.root)
            self._status_var.set(f"Add failed: {exc}")
            return

        saved = self._auto_save()
        self.refresh_view()
        if self.tree.exists(dialog.result.sku):
            self.tree.selection_set(dialog.result.sku)
            self.tree.see(dialog.result.sku)

        suffix = " and saved." if saved else " (unsaved)."
        self._status_var.set(f"Added {dialog.result.sku}{suffix}")

    def _on_edit_selected(self) -> None:
        """Open the modal Edit Product dialog for the selected row."""
        sku = self._get_selected_sku()
        if sku is None:
            messagebox.showinfo(
                "No Selection",
                "Please select a product to edit.",
                parent=self.root,
            )
            return

        existing = self.manager.get_product(sku)
        if existing is None:
            self.refresh_view()
            return

        dialog = ProductDialog(self.root, product=existing)
        self.root.wait_window(dialog)
        if dialog.result is None:
            return

        updated_data = dialog.result
        try:
            self.manager.update_product(
                existing.sku,
                name=updated_data.name,
                category=updated_data.category,
                quantity=updated_data.quantity,
                unit_price=updated_data.unit_price,
                reorder_level=updated_data.reorder_level,
            )
        except (KeyError, ValueError) as exc:
            messagebox.showerror(
                "Update Product Error", str(exc), parent=self.root
            )
            self._status_var.set(f"Update failed: {exc}")
            return

        saved = self._auto_save()
        self.refresh_view()
        if self.tree.exists(existing.sku):
            self.tree.selection_set(existing.sku)
            self.tree.see(existing.sku)

        suffix = " and saved." if saved else " (unsaved)."
        self._status_var.set(f"Updated {existing.sku}{suffix}")

    def _on_delete_selected(self) -> None:
        """Confirm and delete the currently selected product."""
        sku = self._get_selected_sku()
        if sku is None:
            messagebox.showinfo(
                "No Selection",
                "Please select a product to delete.",
                parent=self.root,
            )
            return

        existing = self.manager.get_product(sku)
        if existing is None:
            self.refresh_view()
            return

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Delete product '{existing.sku}' ({existing.name})?",
            parent=self.root,
        )
        if not confirmed:
            self._status_var.set("Deletion cancelled.")
            return

        try:
            self.manager.delete_product(existing.sku)
        except (KeyError, ValueError) as exc:
            messagebox.showerror("Delete Error", str(exc), parent=self.root)
            self._status_var.set(f"Delete failed: {exc}")
            return

        saved = self._auto_save()
        self.refresh_view()
        suffix = " and saved." if saved else " (unsaved)."
        self._status_var.set(f"Deleted {existing.sku}{suffix}")

    def _on_save_now(self) -> None:
        """Manually save current inventory and report confirmation."""
        if self._auto_save():
            self._status_var.set(
                f"Inventory saved to '{self.manager.filepath}'."
            )

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
