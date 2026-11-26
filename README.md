# StockFlow — Inventory & Stock Control System

**Module:** CSC-44102  
**Status:** Step 1 — Project Scaffolding & Local Git Setup

## Overview

StockFlow is a Python-based Inventory & Stock Control System designed around a clean, modular architecture. It will provide both a **Command-Line Interface (CLI)** and a **Tkinter Graphical User Interface (GUI)** that share a single, decoupled core business logic and persistence layer.

## Planned Features

- **Product & Inventory Management:** Add, update, remove, and search stock items (SKU, name, category, quantity, unit price, reorder threshold).
- **Stock Movements & Adjustments:** Record stock-in (restock) and stock-out (sales/dispatch) transactions with validation against negative stock.
- **Low-Stock Alerts & Reporting:** Identify items at or below their reorder threshold and generate inventory summary reports.
- **Persistent Storage:** Save and load inventory data cleanly in `data/`.
- **Dual Interfaces:**
  - Interactive **CLI** for terminal workflows.
  - Responsive **Tkinter GUI** for desktop use.
- **Automated Testing:** Unit tests in `tests/` covering core inventory logic and edge cases.

## Project Structure

```text
StockFlow/
├── data/               # Inventory data storage directory (tracked via .gitkeep)
│   └── .gitkeep
├── docs/               # Architecture diagrams and documentation
│   └── .gitkeep
├── src/                # Application source package (core logic, CLI, GUI)
│   └── __init__.py
├── tests/              # Unit and integration tests
│   └── __init__.py
├── .gitignore          # Python, IDE, OS, and test artifact exclusions
├── README.md           # Project overview and documentation
└── requirements.txt    # Dependency notes (Python Standard Library + optional pytest)
```

## Installation

_Placeholder — installation instructions will be added once the application entry points are implemented._

- **Prerequisites:** Python 3.x with `tkinter` enabled.

## Running the CLI

_Placeholder — CLI usage instructions and command examples will be added in a later step._

## Running the GUI

_Placeholder — Tkinter GUI launch instructions will be added in a later step._

## GenAI Acknowledgement

In accordance with **CSC-44102 Assessment 2** guidelines, the initial Git/GitHub repository setup and this `README.md` scaffold were co-created with the assistance of Generative AI (GenAI). All subsequent design, code, and documentation will be reviewed, verified, and documented accordingly.
