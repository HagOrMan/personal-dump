import argparse
from contextlib import closing
import os
import sqlite3

current_directory = os.path.dirname(os.path.abspath(__file__))
db_folder = os.path.join(current_directory, "..", "data")

def read_all_rows(db_name: str, table_name: str):
    db_path = os.path.join(db_folder, f"{db_name}.db")
    with closing(sqlite3.connect(db_path)) as connection:
        with closing(connection.cursor()) as cursor:
            rows = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
            print(rows)

def parse_args():
    parser = argparse.ArgumentParser("Database Query", description="Easily query sqlite db")
    parser.add_argument("-db", "--db-name", type=str, required=True, help="Name of the database to query")
    parser.add_argument("-tbl", "--table-name", type=str, required=True, help="Name of the table to query")
    return parser.parse_args()

def main():
    args = parse_args()
    db_name: str = args.db_name
    table_name: str = args.table_name
    read_all_rows(db_name, table_name)

if __name__ == '__main__':
    main()
