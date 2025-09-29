#!/usr/bin/env python3
"""
csv_to_sqlite.py

Usage:
  python3 csv_to_sqlite.py <db_path> <csv_path>

Description:
  - Reads a CSV file with a header row of valid SQL column names (no spaces/escaping).
  - Creates (or replaces) a SQLite table named after the CSV file's basename (without extension).
  - All columns are created as TEXT and all values are inserted as-is (text).
  - Works on Windows, Mac, and Linux with Python 3.

Example:
  rm -f data.db
  python3 csv_to_sqlite.py data.db zip_county.csv
  python3 csv_to_sqlite.py data.db county_health_rankings.csv
  sqlite3 data.db ".schema zip_county"
  sqlite3 data.db "select count(*) from zip_county;"

Notes:
  - Behavior on invalid CSV is undefined per spec.
  - Column names are used as-is and not quoted, assuming they are valid SQL identifiers.
"""

import csv
import os
import sqlite3
import sys
from pathlib import Path
from typing import List, Iterable


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def derive_table_name(csv_path: str) -> str:
    # Use the CSV filename stem as the table name (no quotes, as per spec)
    return Path(csv_path).stem


def read_csv_header_and_rows(csv_path: str) -> Iterable[List[str]]:
    """
    Yields rows from the CSV where the first yielded item is the header list.
    Uses csv.Sniffer to guess dialect, falling back to default if sniff fails.
    """
    # Use utf-8-sig to transparently drop BOM if present.
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(65536)
        f.seek(0)
        dialect = None
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            pass  # fall back to defaults
        reader = csv.reader(f, dialect=dialect) if dialect else csv.reader(f)

        # Expect at least a header row
        header = next(reader)
        yield header
        for row in reader:
            yield row


def normalize_row(row: List[str], width: int) -> List[str]:
    if len(row) < width:
        row = row + [""] * (width - len(row))
    elif len(row) > width:
        row = row[:width]
    return row


def create_table(conn: sqlite3.Connection, table: str, columns: List[str]) -> None:
    # Drop and recreate to match the incoming CSV exactly
    conn.execute(f"DROP TABLE IF EXISTS {table}")

    # Build a CREATE TABLE with unquoted identifiers and TEXT type
    cols_sql = ", ".join(f"{col} TEXT" for col in columns)
    conn.execute(f"CREATE TABLE {table} ({cols_sql})")


def insert_rows(conn: sqlite3.Connection, table: str, columns: List[str], rows: Iterable[List[str]], batch_size: int = 1000) -> None:
    placeholders = ", ".join(["?"] * len(columns))
    sql = f"INSERT INTO {table} VALUES ({placeholders})"

    batch: List[List[str]] = []
    for r in rows:
        batch.append(normalize_row(r, len(columns)))
        if len(batch) >= batch_size:
            conn.executemany(sql, batch)
            batch.clear()
    if batch:
        conn.executemany(sql, batch)


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        eprint("Usage: python3 csv_to_sqlite.py <db_path> <csv_path>")
        return 1

    db_path, csv_path = argv[1], argv[2]

    if not os.path.exists(csv_path):
        eprint(f"CSV not found: {csv_path}")
        return 1

    table = derive_table_name(csv_path)

    try:
        gen = read_csv_header_and_rows(csv_path)
        header = next(gen)
        # Normalize header cells: strip whitespace
        columns = [h.strip() for h in header]
        if not columns or any(c == "" for c in columns):
            eprint("Invalid CSV header: empty column names.")
            return 1

        # Connect and import within a single transaction for performance
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            create_table(conn, table, columns)
            insert_rows(conn, table, columns, gen)
            # Transaction automatically committed on exiting context manager

    except StopIteration:
        eprint("CSV appears to be empty (no header row).")
        return 1
    except sqlite3.Error as e:
        eprint(f"SQLite error: {e}")
        return 1
    except Exception as e:
        eprint(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
