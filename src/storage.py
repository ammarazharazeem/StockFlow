# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""JSON file persistence utilities for StockFlow inventory data."""

from __future__ import annotations

import json
from pathlib import Path

from src.models import Product


def load_products(filepath: Path | str) -> list[Product]:
    """Load and validate products from a JSON file.

    Args:
        filepath: Path to the JSON inventory file.

    Returns:
        List of Product instances. Returns an empty list if the file does not exist.

    Raises:
        ValueError: If the path is a directory, JSON is corrupted/invalid, or
            any product record fails validation.
    """
    path = Path(filepath)
    if not path.exists():
        return []
    if path.is_dir():
        raise ValueError(f"Inventory path '{path}' is a directory, not a file.")

    try:
        raw_text = path.read_text(encoding="utf-8")
        raw_data = json.loads(raw_text)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"Corrupted or invalid JSON in inventory file '{path}': {exc}"
        ) from exc
    except OSError as exc:
        raise ValueError(f"Unable to read inventory file '{path}': {exc}") from exc

    if not isinstance(raw_data, list):
        raise ValueError(
            f"Inventory file '{path}' must contain a JSON array of products."
        )

    products: list[Product] = []
    for index, item in enumerate(raw_data):
        try:
            products.append(Product.from_dict(item))
        except ValueError as exc:
            raise ValueError(
                f"Invalid product entry at index {index} in '{path}': {exc}"
            ) from exc

    return products


def save_products(filepath: Path | str, products: list[Product]) -> None:
    """Persist a list of products to a JSON file, creating parent directories if needed.

    Args:
        filepath: Destination path for the JSON inventory file.
        products: List of Product instances to serialize.

    Raises:
        ValueError: If an item is not a Product or the file cannot be written.
    """
    path = Path(filepath)
    if path.exists() and path.is_dir():
        raise ValueError(f"Inventory path '{path}' is a directory, not a file.")

    serialized: list[dict] = []
    for product in products:
        if not isinstance(product, Product):
            raise ValueError("All items to save must be Product instances.")
        serialized.append(product.to_dict())

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(serialized, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to write inventory file '{path}': {exc}") from exc


class InventoryStorage:
    """Object-oriented wrapper around JSON inventory persistence."""

    def __init__(self, filepath: Path | str) -> None:
        """Initialize storage bound to a target JSON file path."""
        self.filepath = Path(filepath)

    def load(self) -> list[Product]:
        """Load products from the configured JSON file."""
        return load_products(self.filepath)

    def save(self, products: list[Product]) -> None:
        """Save products to the configured JSON file."""
        save_products(self.filepath, products)
