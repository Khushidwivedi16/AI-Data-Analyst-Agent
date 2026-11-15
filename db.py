import os
import re
import sqlite3
import uuid

import pandas as pd

from config import RUNTIME_DB_DIR, TABLE_NAME

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|attach|detach|pragma|vacuum|reindex)\b",
    re.IGNORECASE,
)


def new_db_path():
    os.makedirs(RUNTIME_DB_DIR, exist_ok=True)
    return f"{RUNTIME_DB_DIR}/{uuid.uuid4().hex}.db"


def save_to_db(df, db_path, table_name=TABLE_NAME):
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()


def get_schema(db_path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        conn.close()
    return "\n\n".join(r[0] for r in rows if r[0])


def validate_read_only(query):
    cleaned = query.strip().rstrip(";").strip()
    if ";" in cleaned:
        raise ValueError("Multiple SQL statements are not allowed.")
    if not re.match(r"^(select|with)\b", cleaned, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    if FORBIDDEN.search(cleaned):
        raise ValueError("The query contains a forbidden keyword.")
    return cleaned


def run_query(db_path, query):
    safe_query = validate_read_only(query)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(safe_query, conn)
    finally:
        conn.close()


def remove_db(db_path):
    if db_path and os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


if __name__ == "__main__":
    from data_loader import load_dataframe

    df, _, _ = load_dataframe("datasets/superstore.csv")
    path = new_db_path()
    save_to_db(df, path)
    print(get_schema(path))
    print(run_query(path, "SELECT COUNT(*) AS total_rows FROM data"))
    try:
        run_query(path, "DROP TABLE data")
    except ValueError as err:
        print("Blocked as expected:", err)
    remove_db(path)