# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Modal Tkinter dialog for adding and editing StockFlow inventory products."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.models import Product


class ProductDialog(tk.Toplevel):
    """Modal dialog for entering and validating Product attributes."""

    def __init__(
        self,
        parent: tk.Misc,
        product: Product | None = None,
        title: str | None = None,
    ) -> None:
        """Initialize the Add/Edit Product modal dialog.

        Args:
            parent: Parent Tkinter widget.
            product: Existing Product to edit, or None when adding a new product.
            title: Optional custom window title.
        """
        super().__init__(parent)
        self._is_edit = product is not None
        self.result: Product | None = None

        resolved_title = title or (
            f"Edit Product — {product.sku}" if product else "Add New Product"
        )
        self.title(resolved_title)
        self.resizable(False, False)
        self.transient(parent)

        self._sku_var = tk.StringVar(value=product.sku if product else "")
        self._name_var = tk.StringVar(value=product.name if product else "")
        self._category_var = tk.StringVar(
            value=product.category if product else ""
        )
        self._quantity_var = tk.StringVar(
            value=str(product.quantity) if product else ""
        )
        self._unit_price_var = tk.StringVar(
            value=f"{product.unit_price:.2f}" if product else ""
        )
        self._reorder_var = tk.StringVar(
            value=str(product.reorder_level) if product else "5"
        )

        self._build_form()
        self.bind("<Return>", self._on_submit)
        self.bind("<Escape>", self._on_cancel)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.grab_set()
        self._focus_initial_field()

    def _build_form(self) -> None:
        """Construct the labeled form inputs and action buttons."""
        container = ttk.Frame(self, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        fields: list[tuple[str, tk.StringVar, bool]] = [
            ("SKU:", self._sku_var, self._is_edit),
            ("Product Name:", self._name_var, False),
            ("Category:", self._category_var, False),
            ("Quantity:", self._quantity_var, False),
            ("Unit Price ($):", self._unit_price_var, False),
            ("Reorder Level:", self._reorder_var, False),
        ]

        self._entries: dict[str, ttk.Entry] = {}
        for row_idx, (label_text, variable, readonly) in enumerate(fields):
            ttk.Label(container, text=label_text).grid(
                row=row_idx, column=0, sticky="w", padx=(0, 12), pady=5
            )
            entry = ttk.Entry(container, textvariable=variable, width=32)
            if readonly:
                entry.configure(state="readonly")
            entry.grid(row=row_idx, column=1, sticky="ew", pady=5)
            self._entries[label_text] = entry

        button_frame = ttk.Frame(container)
        button_frame.grid(
            row=len(fields), column=0, columnspan=2, sticky="e", pady=(14, 0)
        )

        save_label = "Save Changes" if self._is_edit else "Add Product"
        ttk.Button(
            button_frame, text="Cancel", command=self._on_cancel
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            button_frame, text=save_label, command=self._on_submit
        ).pack(side="right")

    def _focus_initial_field(self) -> None:
        """Focus the first editable input field in the dialog."""
        target_key = "Product Name:" if self._is_edit else "SKU:"
        self._entries[target_key].focus_set()

    def _on_submit(self, _event: tk.Event | None = None) -> None:
        """Validate form values, construct a Product, and close on success."""
        sku = self._sku_var.get().strip()
        name = self._name_var.get().strip()
        category = self._category_var.get().strip()
        quantity_raw = self._quantity_var.get().strip()
        unit_price_raw = self._unit_price_var.get().strip()
        reorder_raw = self._reorder_var.get().strip()

        if not sku:
            messagebox.showerror(
                "Validation Error", "SKU cannot be empty.", parent=self
            )
            return
        if not name:
            messagebox.showerror(
                "Validation Error",
                "Product Name cannot be empty.",
                parent=self,
            )
            return
        if not category:
            messagebox.showerror(
                "Validation Error", "Category cannot be empty.", parent=self
            )
            return

        try:
            quantity = int(quantity_raw)
        except ValueError:
            messagebox.showerror(
                "Validation Error",
                "Quantity must be a valid whole number.",
                parent=self,
            )
            return

        try:
            unit_price = float(unit_price_raw)
        except ValueError:
            messagebox.showerror(
                "Validation Error",
                "Unit Price must be a valid number.",
                parent=self,
            )
            return

        try:
            reorder_level = int(reorder_raw)
        except ValueError:
            messagebox.showerror(
                "Validation Error",
                "Reorder Level must be a valid whole number.",
                parent=self,
            )
            return

        try:
            self.result = Product(
                sku=sku,
                name=name,
                category=category,
                quantity=quantity,
                unit_price=unit_price,
                reorder_level=reorder_level,
            )
        except ValueError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return

        self.destroy()

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        """Cancel the dialog without storing a result."""
        self.result = None
        self.destroy()
