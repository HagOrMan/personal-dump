import argparse
from contextlib import closing
from datetime import date, datetime
import os
import sqlite3

current_directory = os.path.dirname(os.path.abspath(__file__))
db_folder = os.path.join(current_directory, "..", "data")

CATEGORY_OPTIONS = [
    "Groceries",
    "Eating Out (Stressed)",
    "Eating Out (Social)",
    "Social",
    "Health",
    "Rent",
    "School",
    "Other",
]


def ensure_table_exists(db_path: str, table_name: str):
    with closing(sqlite3.connect(db_path)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    discount REAL DEFAULT 0,
                    discount_percentage REAL DEFAULT 0,
                    note TEXT,
                    date TEXT NOT NULL
                )
            """
            )
            connection.commit()


def insert_receipt(
    db_name: str,
    table_name: str,
    store: str,
    category: str,
    price: float,
    discount: float,
    discount_percentage: float,
    note: str,
    receipt_date: str,
):
    db_path = os.path.join(db_folder, f"{db_name}.db")
    ensure_table_exists(db_path, table_name)

    with closing(sqlite3.connect(db_path)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table_name} (store, category, price, discount, discount_percentage, note, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    store,
                    category,
                    price,
                    discount,
                    discount_percentage,
                    note,
                    receipt_date,
                ),
            )
            connection.commit()
            print(
                f"Receipt added: \n\tStore: {store} \n\tCategory: {category} \n\tPrice: ${price:.2f}"
            )


def validate_category(category: str, note: str):
    if category in CATEGORY_OPTIONS:
        return category, note

    print("\nInvalid category provided!")
    print("Please choose one of the following:")
    for i, option in enumerate(CATEGORY_OPTIONS, start=1):
        print(f"{i}. {option}")

    choice = input(
        "Enter number to select category, or press Enter to fallback to 'Other': "
    ).strip()
    if choice.isdigit() and 1 <= int(choice) <= len(CATEGORY_OPTIONS):
        return CATEGORY_OPTIONS[int(choice) - 1], note
    else:
        # fallback to Other, append category to note
        new_note = (
            (note + f" | Original category: {category}")
            if note
            else f"Original category: {category}"
        )
        return "Other", new_note


def parse_date_arg(date_str: str | None) -> str:
    if not date_str:
        return date.today().isoformat()
    try:
        # validate and return in YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-02).")


def parse_args():
    parser = argparse.ArgumentParser(
        "Receipt Uploader", description="Upload receipts into sqlite db"
    )
    parser.add_argument(
        "-db",
        "--db-name",
        type=str,
        default="secret_finances",
        help="Database name (default: `secret_finances`)",
    )
    parser.add_argument(
        "-tbl",
        "--table-name",
        type=str,
        default="receipts",
        help="Table name (default: `receipts`)",
    )
    parser.add_argument(
        "--price", type=float, required=True, help="Price of the item/receipt"
    )
    parser.add_argument(
        "--discount", type=float, default=0.0, help="Discount applied (default: `0`)"
    )
    parser.add_argument(
        "--discount-percentage",
        type=float,
        default=0.0,
        help="Discount percentage applied (default: `0`)",
    )
    parser.add_argument("--store", type=str, required=True, help="Store name")
    parser.add_argument(
        "--category", type=str, required=True, help="Category of expense"
    )
    parser.add_argument("--note", type=str, default="", help="Optional note")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date of receipt in YYYY-MM-DD format (default: today)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    category, note = validate_category(args.category, args.note)
    receipt_date = parse_date_arg(args.date)

    insert_receipt(
        db_name=args.db_name,
        table_name=args.table_name,
        store=args.store,
        category=category,
        price=args.price,
        discount=args.discount,
        discount_percentage=args.discount_percentage,
        note=note,
        receipt_date=receipt_date,
    )


if __name__ == "__main__":
    main()
