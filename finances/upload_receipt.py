from contextlib import closing
from datetime import date, datetime
from gooey import Gooey, GooeyParser
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


def ensure_disbursement_table_exists(db_path: str, table_name: str):
    with closing(sqlite3.connect(db_path)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date_received TEXT NOT NULL,
                    reason TEXT,
                    refunded_from_receipt INTEGER,
                    FOREIGN KEY(refunded_from_receipt) REFERENCES receipts(id)
                )
                """
            )
            connection.commit()


def insert_disbursement(
    db_name: str,
    table_name: str,
    entity: str,
    amount: float,
    date_received: str,
    reason: str,
    refunded_from_receipt: int | None,
):
    db_path = os.path.join(db_folder, f"{db_name}.db")
    ensure_disbursement_table_exists(db_path, table_name)

    with closing(sqlite3.connect(db_path)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table_name} (entity, amount, date_received, reason, refunded_from_receipt)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entity, amount, date_received, reason, refunded_from_receipt),
            )
            connection.commit()
            print(
                f"Disbursement added: \n\tEntity: {entity} \n\tAmount: ${amount:.2f} \n\tDate Received: {date_received}"
            )


def ensure_receipts_table_exists(db_path: str, table_name: str):
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
    ensure_receipts_table_exists(db_path, table_name)

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


def parse_date_arg(date_str: str | None) -> str:
    if not date_str:
        return date.today().isoformat()
    try:
        # validate and return in YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-02).")


@Gooey(program_name="Receipt & Disbursement Uploader", default_tab="Receipt")
def parse_args():
    parser = GooeyParser(description="Upload receipts or disbursements into sqlite db")

    subparsers = parser.add_subparsers(help="Choose what to upload", dest="mode")

    # ----------------- Receipt Tab -----------------
    receipt_parser: GooeyParser = subparsers.add_parser(
        "Receipt", help="Upload a receipt"
    )
    receipt_group = receipt_parser.add_argument_group(
        "Receipt Information", "All the info needed about your receipt"
    )
    receipt_group.add_argument(
        "Store",
        type=str,
        help="Name of Organization the receipt is from",
    )
    receipt_group.add_argument(
        "Category",
        choices=CATEGORY_OPTIONS,
        type=str,
        help="Category of expense",
    )
    receipt_group.add_argument(
        "Price",
        type=float,
        help="Price of the item/receipt",
    )
    receipt_group.add_argument(
        "Discount",
        type=float,
        default=0.0,
        help="Discount applied in dollars (default: `0`)",
    )
    receipt_group.add_argument(
        dest="discount_percentage",
        type=float,
        default=0.0,
        help="Discount percentage applied in percent (default: `0`)",
    )
    receipt_group.add_argument(
        "--Note",
        type=str,
        default="",
        help="Optional note to help describe the receipt",
    )
    receipt_group.add_argument(
        "Date",
        default=date.today().isoformat(),
        help="Date of receipt in YYYY-MM-DD format (default: today)",
        widget="DateChooser",
    )

    database_group_receipts = receipt_parser.add_argument_group(
        "Database Options", "Customize where the data goes"
    )
    database_group_receipts.add_argument(
        dest="db_name",
        type=str,
        default="secret_finances",
        help="Name of database to store receipts in (default: `secret_finances`)",
    )
    database_group_receipts.add_argument(
        dest="table_name",
        type=str,
        default="receipts",
        help="Name of table to store receipts in (default: `receipts`)",
    )

    # ----------------- Disbursement Tab -----------------
    disb_parser: GooeyParser = subparsers.add_parser(
        "Disbursement", help="Upload a disbursement"
    )
    disb_group = disb_parser.add_argument_group("Disbursement Information")
    disb_group.add_argument(
        "Entity", type=str, help="Entity the disbursement came from"
    )
    disb_group.add_argument("Amount", type=float, help="Amount received in dollars")
    disb_group.add_argument(
        "Date_received",
        default=date.today().isoformat(),
        help="Date received in YYYY-MM-DD format (default: today)",
        widget="DateChooser",
    )
    disb_group.add_argument(
        "--Reason", type=str, default="", help="Optional reason for disbursement"
    )
    disb_group.add_argument(
        "--Refunded_from_receipt",
        type=int,
        default=None,
        help="Optional receipt ID if this disbursement is a refund",
    )

    database_group_disb = disb_parser.add_argument_group(
        "Database Options", "Customize where the data goes"
    )
    database_group_disb.add_argument(
        dest="db_name",
        type=str,
        default="secret_finances",
        help="Name of database to store disbursements in (default: `secret_finances`)",
    )
    database_group_disb.add_argument(
        dest="table_name",
        type=str,
        default="disbursements",
        help="Name of table to store disbursements in (default: `disbursements`)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.mode == "Receipt":
        receipt_date = parse_date_arg(args.Date)
        insert_receipt(
            db_name=args.db_name,
            table_name=args.table_name,
            store=args.Store,
            category=args.Category,
            price=args.Price,
            discount=args.Discount,
            discount_percentage=args.discount_percentage,
            note=args.Note,
            receipt_date=receipt_date,
        )

    elif args.mode == "Disbursement":
        disb_date = parse_date_arg(args.Date_received)
        insert_disbursement(
            db_name=args.db_name,
            table_name=args.table_name,
            entity=args.Entity,
            amount=args.Amount,
            date_received=disb_date,
            reason=args.Reason,
            refunded_from_receipt=args.Refunded_from_receipt,
        )

    else:
        raise ValueError("Please choose either 'Receipt' or 'Disbursement' tab")


if __name__ == "__main__":
    main()
