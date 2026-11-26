# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Domain data models for the StockFlow inventory management system."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass
class Product:
    """Represents an inventory item with validated attributes and stock helpers."""

    sku: str
    name: str
    category: str
    quantity: int
    unit_price: float
    reorder_level: int = 5

    def __post_init__(self) -> None:
        """Normalize text fields and validate all product attributes."""
        self.validate()

    def validate(self) -> None:
        """Validate field types, non-empty strings, and non-negative numeric bounds."""
        self.sku = self._validate_non_empty_str(self.sku, "SKU").upper()
        self.name = self._validate_non_empty_str(self.name, "Product name")
        self.category = self._validate_non_empty_str(self.category, "Category")

        self.quantity = self._validate_non_negative_int(self.quantity, "Quantity")
        self.unit_price = self._validate_non_negative_float(self.unit_price, "Unit price")
        self.reorder_level = self._validate_non_negative_int(
            self.reorder_level, "Reorder level"
        )

    @staticmethod
    def _validate_non_empty_str(value: Any, field_name: str) -> str:
        """Ensure a value is a non-empty string after stripping whitespace."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field_name} cannot be empty or whitespace.")
        return cleaned

    @staticmethod
    def _validate_non_negative_int(value: Any, field_name: str) -> int:
        """Ensure a value is a non-negative integer, explicitly rejecting booleans."""
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer.")
        if value < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return value

    @staticmethod
    def _validate_non_negative_float(value: Any, field_name: str) -> float:
        """Ensure a value is a finite non-negative number, rejecting booleans."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number.")
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise ValueError(f"{field_name} must be a finite number.")
        if numeric_value < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return numeric_value

    def total_value(self) -> float:
        """Calculate the total stock value for this product."""
        return round(self.quantity * self.unit_price, 2)

    def is_low_stock(self) -> bool:
        """Return True when quantity is at or below the reorder threshold."""
        return self.quantity <= self.reorder_level

    def to_dict(self) -> dict[str, Any]:
        """Serialize the product into a JSON-compatible dictionary."""
        return {
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "reorder_level": self.reorder_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Product:
        """Construct a validated Product instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Product data must be a dictionary.")

        required_fields = ("sku", "name", "category", "quantity", "unit_price")
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(
                f"Missing required product field(s): {', '.join(missing)}."
            )

        return cls(
            sku=data["sku"],
            name=data["name"],
            category=data["category"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            reorder_level=data.get("reorder_level", 5),
        )
