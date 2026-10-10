#!/usr/bin/env python3
"""Run portfolio SQL examples read-only against the generated SQLite database."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def query_results(database=None, sql_file=None):
    database = Path(database) if database else ROOT / "data" / "processed" / "inventory.sqlite3"
    sql_file = Path(sql_file) if sql_file else ROOT / "sql" / "analysis.sql"
    statements, buffer = [], ""
    for line in sql_file.read_text(encoding="utf-8").splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statements.append(buffer)
            buffer = ""
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return [[dict(row) for row in connection.execute(statement).fetchall()] for statement in statements]


if __name__ == "__main__":
    for index, rows in enumerate(query_results(), 1):
        print(json.dumps({"query": index, "rows": rows}, indent=2))
