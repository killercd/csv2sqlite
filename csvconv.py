#!/usr/bin/env python3
"""Convert CSV files to SQLite databases and SQLite tables to CSV files."""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
from pathlib import Path
from typing import Sequence


def quote_identifier(identifier: str) -> str:
    if not identifier:
        raise ValueError("Identifier cannot be empty")
    return '"' + identifier.replace('"', '""') + '"'


def default_table_name(csv_path: str) -> str:
    return Path(csv_path).stem


def read_csv_header(csv_path: str) -> list[str]:
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV file is empty") from exc

    if not header:
        raise ValueError("CSV header is empty")
    if any(column == "" for column in header):
        raise ValueError("CSV header contains an empty column name")
    if len(set(header)) != len(header):
        raise ValueError("CSV header contains duplicate column names")
    return header


def csv_to_sqlite(csv_path: str, database_path: str, append: bool, table: str | None) -> None:
    if not append and os.path.exists(database_path):
        os.remove(database_path)

    table_name = table or default_table_name(csv_path)
    header = read_csv_header(csv_path)
    quoted_table = quote_identifier(table_name)
    quoted_columns = [quote_identifier(column) for column in header]
    placeholders = ", ".join("?" for _ in header)

    with sqlite3.connect(database_path) as connection:
        column_defs = ", ".join(f"{column} TEXT" for column in quoted_columns)
        connection.execute(f"CREATE TABLE {quoted_table} ({column_defs})")

        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = ([row[column] for column in header] for row in reader)
            connection.executemany(
                f"INSERT INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES ({placeholders})",
                rows,
            )


def list_tables(connection: sqlite3.Connection) -> list[str]:
    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY rowid
        """
    )
    return [row[0] for row in cursor.fetchall()]


def resolve_table(connection: sqlite3.Connection, table: str | None) -> str:
    if table:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        if not exists:
            raise ValueError(f"Table not found: {table}")
        return table

    tables = list_tables(connection)
    if not tables:
        raise ValueError("SQLite database does not contain any user tables")
    return tables[0]


def escape_newlines(value: object) -> object:
    if not isinstance(value, str):
        return value
    return value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def sqlite_to_csv(database_path: str, csv_path: str, table: str | None) -> None:
    with sqlite3.connect(database_path) as connection:
        table_name = resolve_table(connection, table)
        quoted_table = quote_identifier(table_name)
        cursor = connection.execute(f"SELECT * FROM {quoted_table}")
        columns = [description[0] for description in cursor.description or []]

        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)
            writer.writerows(tuple(escape_newlines(value) for value in row) for row in cursor)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csvconv.py",
        description="Convert CSV files to SQLite databases and SQLite tables to CSV files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    csv2sqlite = subparsers.add_parser(
        "csv2sqlite",
        help="Convert a CSV file to a SQLite database.",
    )
    csv2sqlite.add_argument("csv_file", help="Input CSV file.")
    csv2sqlite.add_argument("database", help="Output SQLite database.")
    csv2sqlite.add_argument(
        "--append",
        action="store_true",
        help="Append a new table without overwriting the database file.",
    )
    csv2sqlite.add_argument(
        "--table",
        help="SQLite table name. Defaults to the CSV file name without extension.",
    )

    sqlite2csv = subparsers.add_parser(
        "sqlite2csv",
        help="Convert a SQLite table to a CSV file.",
    )
    sqlite2csv.add_argument("database", help="Input SQLite database.")
    sqlite2csv.add_argument("csv_file", help="Output CSV file.")
    sqlite2csv.add_argument(
        "--table",
        help="SQLite table name. Defaults to the first user table found.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "csv2sqlite":
            csv_to_sqlite(args.csv_file, args.database, args.append, args.table)
        elif args.command == "sqlite2csv":
            sqlite_to_csv(args.database, args.csv_file, args.table)
        else:
            parser.error(f"Unknown command: {args.command}")
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
