import os
import re
import warnings

import pandas as pd


def sanitize_column_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^0-9a-z]+", "_", name).strip("_")
    if not name:
        name = "column"
    if name[0].isdigit():
        name = "col_" + name
    return name


def sanitize_columns(df):
    new_cols, seen = [], {}
    for col in df.columns:
        base = sanitize_column_name(col)
        if base in seen:
            seen[base] += 1
            new_cols.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 0
            new_cols.append(base)
    renamed = {old: new for old, new in zip(df.columns, new_cols) if str(old) != new}
    df = df.copy()
    df.columns = new_cols
    return df, renamed


def get_excel_sheets(file):
    if hasattr(file, "seek"):
        file.seek(0)
    sheets = pd.ExcelFile(file).sheet_names
    if hasattr(file, "seek"):
        file.seek(0)
    return sheets


def _read_raw(file, filename, sheet_name):
    lower = filename.lower()
    if hasattr(file, "seek"):
        file.seek(0)
    if lower.endswith(".csv"):
        try:
            return pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            if hasattr(file, "seek"):
                file.seek(0)
            return pd.read_csv(file, encoding="latin1")
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(file, sheet_name=sheet_name)
    raise ValueError("Unsupported file type. Please upload a .csv, .xlsx or .xls file.")


def _parse_dates(series):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parsed = pd.to_datetime(series, errors="coerce")
    non_null = series.notna().sum()
    ratio = parsed.notna().sum() / non_null if non_null else 0
    return parsed, ratio


def clean_dataframe(df):
    log = []
    stats = {"duplicates_removed": 0, "empty_rows_removed": 0}

    df, renamed = sanitize_columns(df)
    if renamed:
        old, new = next(iter(renamed.items()))
        log.append(f"Renamed {len(renamed)} column(s) to SQL-safe snake_case names (example: '{old}' -> '{new}').")

    changed = 0
    for col in df.select_dtypes(include="object").columns:
        stripped = df[col].map(lambda v: v.strip() if isinstance(v, str) else v)
        changed += int((stripped.fillna("") != df[col].fillna("")).sum())
        df[col] = stripped
    if changed:
        log.append(f"Trimmed extra spaces in {changed:,} text cell(s).")

    before = len(df)
    df = df.dropna(how="all")
    stats["empty_rows_removed"] = before - len(df)
    if stats["empty_rows_removed"]:
        log.append(f"Removed {stats['empty_rows_removed']:,} completely empty row(s).")

    before = len(df)
    df = df.drop_duplicates()
    stats["duplicates_removed"] = before - len(df)
    if stats["duplicates_removed"]:
        log.append(f"Removed {stats['duplicates_removed']:,} duplicate row(s).")

    for col in df.columns:
        if df[col].dtype == "object" and ("date" in col or "time" in col):
            parsed, ratio = _parse_dates(df[col])
            if ratio >= 0.8:
                df[col] = parsed
                log.append(f"Converted '{col}' to a proper date/time column.")

    missing_cols = int((df.isnull().sum() > 0).sum())
    if missing_cols:
        log.append(f"Missing values found in {missing_cols} column(s). They were kept as NULL (not filled in).")
    if not log:
        log.append("No cleaning was needed. The data was already clean.")

    return df.reset_index(drop=True), log, stats


def load_dataframe(file, sheet_name=0):
    filename = os.path.basename(str(getattr(file, "name", None) or file))
    raw = _read_raw(file, filename, sheet_name)
    df, log, stats = clean_dataframe(raw)
    log.insert(0, f"Loaded '{filename}': {raw.shape[0]:,} rows x {raw.shape[1]} columns.")
    return df, log, stats


def profile_report(df, stats=None):
    stats = stats or {}
    rows, cols = df.shape
    missing_cells = int(df.isnull().sum().sum())
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    datetime_cols = df.select_dtypes(include="datetime").columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols and c not in datetime_cols]
    column_table = pd.DataFrame({
        "column": df.columns,
        "type": [str(t) for t in df.dtypes],
        "missing": df.isnull().sum().values,
        "missing_%": (df.isnull().mean().values * 100).round(2),
        "unique": [df[c].nunique() for c in df.columns],
    })
    return {
        "rows": rows,
        "columns": cols,
        "missing_cells": missing_cells,
        "missing_pct": round(100 * missing_cells / (rows * cols), 2) if rows * cols else 0,
        "duplicates_removed": stats.get("duplicates_removed", 0),
        "numeric_cols": numeric_cols,
        "datetime_cols": datetime_cols,
        "categorical_cols": categorical_cols,
        "column_table": column_table,
    }


if __name__ == "__main__":
    df, log, stats = load_dataframe("datasets/superstore.csv")
    for line in log:
        print("-", line)
    print(df.head())
    print(profile_report(df, stats)["column_table"])