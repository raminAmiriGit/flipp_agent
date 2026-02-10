"""
Generate synthetic grocery flyer PDFs for Flipp-style information extraction.

Creates:
1. Table-style flyers: product tables with name, price, discount, category, validity.
2. Catalog-style flyers: product cards with placeholder "image" boxes, name, price.

Output: PDFs in flipp_agent/data/flyers/ (table and catalog subfolders).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
# SCRIPT_DIR = Path(__file__).resolve().parent
from pathlib import Path
import sys

# Add project root for config (Databricks notebook-safe)
SCRIPT_DIR = Path.cwd()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "flyers"
TABLE_DIR = OUTPUT_DIR / "table_style"
CATALOG_DIR = OUTPUT_DIR / "catalog_style"

# Synthetic flyer definitions (inspired by real grocery circulars)
FLYER_META = [
    {
        "retailer": "Metro Plus",
        "title": "EVERYTHING YOU NEED FOR THE BIG GAME",
        "valid_from": "February 5, 2026",
        "valid_to": "February 11, 2026",
    },
    {
        "retailer": "FreshCo Weekly",
        "title": "WEEKLY SAVINGS",
        "valid_from": "February 6, 2026",
        "valid_to": "February 12, 2026",
    },
    {
        "retailer": "No Frills",
        "title": "FLYER DEALS",
        "valid_from": "February 7, 2026",
        "valid_to": "February 13, 2026",
    },
]

# Product rows: (product_name, brand, price_display, was_price, category, unit, attributes)
PRODUCTS = [
    ("Marinated Chicken Wings", "Adonis", "$5.99/lb", "$7.49/lb", "Meat & Poultry", "per lb", "Halal, Original Recipe"),
    ("Chicken Wings 908g", "Maple Lodge Zabiha Halal", "$14.99", "$17.99", "Meat & Poultry", "908 g", "Halal, selected varieties"),
    ("Börek Twist Meat Phyllo Pie", "Börek", "$14.99", "$18.49", "Frozen", "908 g", "Halal"),
    ("French Fries", "Selection", "$4.99", "$6.49", "Frozen", "2 kg", "selected varieties"),
    ("Sliced Breads or Buns", "Villaggio", "2/$6", "2/$8", "Bakery", "650-675 g", "6 ct"),
    ("Supreme Frankfurters", "Zabiha Halal", "$6.99", "$8.49", "Deli", "900 g", "Halal, Juicy or Spicy"),
    ("Beef Burger", "Al Safa", "$12.49", "$14.99", "Meat & Poultry", "800 g", "Halal"),
    ("Condiment Pack", "Heinz", "$7.49", "$9.99", "Pantry", "3x375 ml", "Mustard, Relish, Ketchup"),
    ("Pita Chips", "Adonis", "$3.49", "$4.29", "Snacks", "225 g", "selected varieties"),
    ("Dips Hummus", "Adonis", "$3.99", "$4.99", "Dairy & Deli", "250 g", "selected varieties"),
    ("Tostitos Chips or Dips", "Tostitos", "2/$9", "2/$11", "Snacks", "215-295 g", "selected varieties"),
    ("Lay's Chips", "Lay's", "2/$8", "2/$10", "Snacks", "177-235 g", "selected varieties"),
    ("Appetizers", "Irrésistible", "$5.99", "$7.49", "Frozen", "228-493 g", "selected varieties"),
    ("Guacamole Tortilla Chips", "Guacachip", "$4.99", "$5.99", "Snacks", "284 g", "selected varieties"),
    ("Chips", "Selection", "$1.49", "—", "Snacks", "200 g", "Everyday Low Price"),
    ("Jarritos Soft Drink", "Jarritos", "$1.99", "$2.49", "Beverages", "370 ml", "selected varieties"),
]

# Example question/guideline pairs for Knowledge Assistant (one JSON per flyer)
FLYER_QA_EXAMPLES = [
    {
        "question": "What chicken or poultry deals are in the flyer?",
        "guideline": "Answer should list chicken wings, marinated chicken, beef burger, or other meat/poultry items with prices and cite this flyer.",
    },
    {
        "question": "I'm hosting a barbecue for 10 people — what are the best deals?",
        "guideline": "Recommend wings, burgers, buns, condiments, chips, and drinks from the flyer with prices and validity dates.",
    },
    {
        "question": "Are there any halal meat deals?",
        "guideline": "Mention Halal products (e.g. chicken wings, beef burger, frankfurters) with retailer and price.",
    },
    {
        "question": "What snacks and chips are on sale?",
        "guideline": "List chips, dips, hummus, and snack deals with prices and cite the flyer.",
    },
]


def _discount_percent(price_display: str, was_price: str) -> str:
    """Compute discount % for display (simplified)."""
    if was_price == "—" or not was_price:
        return "—"
    # Strip $ and parse first number
    def p(s: str) -> float:
        s = s.replace("$", "").replace("/", " ").strip()
        return float(s.split()[0]) if s else 0.0
    try:
        curr, old = p(price_display), p(was_price)
        if old <= 0:
            return "—"
        pct = (1 - curr / old) * 100
        return f"{int(round(pct))}%"
    except Exception:
        return "—"


def build_table_flyer(meta: dict, output_path: Path) -> None:
    """Generate one table-style flyer PDF."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(meta["title"], styles["Title"]))
    story.append(Paragraph(meta["retailer"], styles["Heading2"]))
    story.append(
        Paragraph(
            f"Valid: {meta['valid_from']} – {meta['valid_to']}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    # Table header
    headers = ["Product", "Brand", "Price", "Was", "Discount", "Category", "Unit", "Notes"]
    rows = [headers]

    for prod in PRODUCTS:
        name, brand, price, was, cat, unit, attrs = prod
        discount = _discount_percent(price, was)
        rows.append([name, brand, price, was, discount, cat, unit, attrs])

    t = Table(rows, colWidths=[1.4*inch, 1.0*inch, 0.65*inch, 0.55*inch, 0.5*inch, 0.9*inch, 0.6*inch, 1.25*inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (2, 0), (4, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ]
        )
    )
    story.append(t)
    doc.build(story)


def build_catalog_flyer(meta: dict, output_path: Path) -> None:
    """Generate one catalog-style flyer with product cards (placeholder image boxes)."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.4 * inch,
        leftMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(meta["title"], styles["Title"]))
    story.append(Paragraph(meta["retailer"], styles["Heading2"]))
    story.append(
        Paragraph(
            f"Valid: {meta['valid_from']} – {meta['valid_to']}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Product cards: 4 per row, each card = [placeholder box, name, price]
    card_w = 1.65 * inch
    box_h = 0.75 * inch

    row_data = []
    for i, prod in enumerate(PRODUCTS):
        name, brand, price, _was, _cat, unit, _attrs = prod
        # Placeholder "image" = colored rectangle with brand label
        label = f"[{brand}]"
        card_table = Table(
            [
                [Paragraph(f'<para align="center">{label}</para>', styles["Normal"])],
                [Paragraph(name[:40] + ("..." if len(name) > 40 else ""), styles["Normal"])],
                [Paragraph(f'<b>{price}</b>', styles["Normal"])],
            ],
            colWidths=[card_w],
            rowHeights=[box_h, 0.35 * inch, 0.25 * inch],
        )
        card_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#D0E8D0")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        row_data.append(card_table)
        if len(row_data) == 4:
            story.append(Table([row_data], colWidths=[card_w] * 4))
            story.append(Spacer(1, 0.15 * inch))
            row_data = []

    if row_data:
        while len(row_data) < 4:
            row_data.append(Paragraph("<para> </para>", styles["Normal"]))
        story.append(Table([row_data], colWidths=[card_w] * 4))

    doc.build(story)


def main() -> None:
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(CATALOG_DIR, exist_ok=True)

    for i, meta in enumerate(FLYER_META):
        base = meta["retailer"].replace(" ", "_").lower()
        table_path = TABLE_DIR / f"flyer_{base}_{i}.pdf"
        catalog_path = CATALOG_DIR / f"flyer_{base}_{i}.pdf"
        build_table_flyer(meta, table_path)
        print(f"Wrote table flyer: {table_path}")
        build_catalog_flyer(meta, catalog_path)
        print(f"Wrote catalog flyer: {catalog_path}")

        # Write JSON example file for Knowledge Assistant (same base name, .json)
        for subdir, path in [(TABLE_DIR, table_path), (CATALOG_DIR, catalog_path)]:
            json_path = path.with_suffix(".json")
            doc_meta = {
                "title": meta["title"],
                "retailer": meta["retailer"],
                "valid_from": meta["valid_from"],
                "valid_to": meta["valid_to"],
                "pdf_path": str(path),
                "question": FLYER_QA_EXAMPLES[i % len(FLYER_QA_EXAMPLES)]["question"],
                "guideline": FLYER_QA_EXAMPLES[i % len(FLYER_QA_EXAMPLES)]["guideline"],
            }
            with open(json_path, "w") as f:
                json.dump(doc_meta, f, indent=2)
            print(f"  Wrote example JSON: {json_path}")

    print(f"\nDone. Table-style PDFs: {TABLE_DIR}")
    print(f"Catalog-style PDFs: {CATALOG_DIR}")


if __name__ == "__main__":
    main()
