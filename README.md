# StockFlow — Inventory & Stock Control System

**Module:** CSC-44102  
**Language:** Python 3.10+ (Standard Library Only)

## Overview

**StockFlow** is a modular Inventory & Stock Control System built in Python with zero third-party runtime dependencies. It pairs a decoupled, thoroughly validated core business logic layer with two interchangeable user interfaces:

- A **menu-driven Command-Line Interface (CLI)** for terminal workflows.
- A **modern Tkinter Graphical User Interface (GUI)** styled with `ttk` (`clam` theme), KPI summary cards, live search/filtering, and colour-coded low-stock highlights.

Both front ends strictly delegate all validation, sorting, searching, analytics, and JSON persistence to the shared `InventoryManager` core.

---

## Key Features

- **Full Product CRUD with Strict Validation:** Create, view, update, and delete inventory items (`sku`, `name`, `category`, `quantity`, `unit_price`, `reorder_level`) with automatic SKU normalisation (stripped + uppercased) and defensive type/bounds checks (rejecting empty text, negative values, booleans, and non-finite numbers).
- **Custom Sorting & Search Algorithms:**
  - **Custom Merge Sort** across `name`, `sku`, `category`, `quantity`, and `unit_price` in ascending or descending order without calling Python's built-in `.sort()` or `sorted()`.
  - **Custom Binary Search** for case-insensitive exact SKU lookup on SKU-sorted inventory.
  - **Multi-field Filtering** supporting partial keyword matching across SKU, name, and category, combined with optional exact category filtering.
- **Low-Stock Alerts & Live Analytics:** Automatically flags items where `quantity <= reorder_level` (`LOW` vs `OK`) and computes total SKUs, total units, total inventory value (£), low-stock count, and active category count.
- **Resilient JSON Persistence:** Auto-loads from and saves to `data/inventory.json` (or a custom `--data` path) with clean `indent=2` formatting, automatic parent directory creation, and graceful handling of missing or corrupted files.
- **Consistent GBP (£) Formatting:** Unified UK currency formatting across CLI tables, CLI summaries, GUI KPI cards, GUI tables, and modal dialogs.

---

## System Architecture

Both interfaces act solely as presentation layers over the shared `InventoryManager` service, ensuring zero duplication of business logic, algorithms, or storage handling:

```text
+-------------------------------+       +-------------------------------+
|       CLI Entry Point         |       |       GUI Entry Point         |
|          run_cli.py           |       |          run_gui.py           |
+---------------+---------------+       +---------------+---------------+
                |                                       |
                v                                       v
+-------------------------------+       +-------------------------------+
|   src/cli.py (StockFlowCLI)   |       |   src/gui.py (StockFlowGUI)   |
|   src/cli_utils.py            |       |   src/gui_dialogs.py          |
+---------------+---------------+       +---------------+---------------+
                |                                       |
                +-------------------+-------------------+
                                    |
                                    v
             +---------------------------------------------+
             |      src/manager.py (InventoryManager)      |
             |  - dict[str, Product]  (O(1) SKU lookup)    |
             |  - set[str]            (unique categories)  |
             |  - list[Product]       (ordered outputs)    |
             +------+---------------+---------------+------+
                    |               |               |
        +-----------+               |               +-----------+
        v                           v                           v
+---------------+         +-------------------+       +-------------------+
| src/models.py |         | src/algorithms.py |       |  src/storage.py   |
| Product model |         | Merge Sort        |       | InventoryStorage  |
| & validation  |         | Binary Search     |       | JSON read / write |
|               |         | Filter helpers    |       | & error handling  |
+---------------+         +-------------------+       +---------+---------+
                                                                |
                                                                v
                                                      +-------------------+
                                                      | data/inventory.json|
                                                      +-------------------+
```

---

## Data Structures & Algorithms

| Component | Structure / Algorithm | Complexity | Purpose |
| :--- | :--- | :--- | :--- |
| `InventoryManager._products` | `dict[str, Product]` | `O(1)` average lookup / insert / delete | Instant SKU-keyed access and duplicate SKU prevention |
| `InventoryManager._categories` | `set[str]` | `O(1)` average membership / insert | Dynamically tracks unique active categories across updates & deletes |
| `list_products` / views | `list[Product]` | `O(n)` traversal | Ordered, non-mutating snapshots for CLI tables and GUI `Treeview` |
| `merge_sort_products` | Custom recursive Merge Sort | `O(n log n)` time, `O(n)` space | Stable sorting on `sku`, `name`, `category`, `quantity`, or `unit_price` without built-in `.sort()`/`sorted()` |
| `binary_search_by_sku` | Custom iterative Binary Search | `O(log n)` search (on SKU-sorted list) | Exact case-insensitive SKU lookup |
| `filter_products` | Linear multi-field scan | `O(n)` time | Partial case-insensitive search across SKU, name, and category |

---

## Project Structure

```text
StockFlow/
├── data/
│   ├── .gitkeep
│   └── inventory.json              # Sample UK inventory dataset (14 products, 5 categories)
├── docs/
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── models.py                   # Product dataclass, normalization, and strict validation
│   ├── algorithms.py               # Custom Merge Sort, Binary Search, and filtering
│   ├── storage.py                  # JSON persistence (load_products, save_products, InventoryStorage)
│   ├── manager.py                  # InventoryManager coordinating dict/set/list state & analytics
│   ├── cli_utils.py                # Validated CLI prompts and aligned ASCII table formatter
│   ├── cli.py                      # Menu-driven StockFlowCLI front end
│   ├── gui_dialogs.py              # Validated modal ProductDialog (Add/Edit)
│   └── gui.py                      # Modern ttk StockFlowGUI front end
├── tests/
│   ├── __init__.py
│   ├── test_models.py              # Unit tests for Product validation and helpers
│   ├── test_algorithms.py          # Unit tests for Merge Sort, Binary Search, and filtering
│   └── test_storage_and_manager.py # Unit tests for JSON storage and InventoryManager CRUD/analytics
├── .gitignore
├── README.md
├── requirements.txt                # Notes zero external runtime dependencies
├── run_cli.py                      # CLI application entry point
└── run_gui.py                      # Tkinter GUI application entry point
```

---

## Setup & Usage

### Prerequisites
- **Python 3.10+** (tested on Python 3.15) with `tkinter` enabled (included in standard Windows/macOS Python installers; on Linux install `python3-tk` if separated).
- **No external third-party packages required** — StockFlow uses only the Python Standard Library.

Clone the repository and navigate to the project root:

```bash
git clone https://github.com/ammarazharazeem/StockFlow.git
cd StockFlow
```

### Run the CLI Application

```bash
python run_cli.py
```

Optional custom data file path:

```bash
python run_cli.py --data path/to/custom_inventory.json
```

### Run the Tkinter GUI Application

```bash
python run_gui.py
```

Optional custom data file path:

```bash
python run_gui.py --data path/to/custom_inventory.json
```

### Run the Automated Unit Test Suite

```bash
python -m unittest discover -s tests -v
```

---

## Academic Integrity & GenAI Acknowledgement

In accordance with **CSC-44102 Assessment 2** guidelines, Generative AI — **Google Gemini (2026, Google, https://gemini.google.com/)** — was used to review drafts of code, tests, and documentation and to provide feedback during development. Every source and test `.py` file explicitly retains the required header acknowledgement, and all implementation logic, algorithms, and test cases were reviewed and verified against the project specification.
