
from pathlib import Path
import json
import sqlite3

import pandas as pd


# Project folders
BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "data" / "raw" / "orders.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

DB_FILE = OUTPUT_DIR / "orders.db"
REJECTED_FILE = OUTPUT_DIR / "rejected_orders.csv"
REPORT_FILE = REPORT_DIR / "quality_report.json"

REQUIRED_COLUMNS = [
    "order_id", "customer", "product", "price", "quantity"
]


def extract_data(file_path):
    """Read the raw CSV file."""
    df = pd.read_csv(file_path, sep=None, engine="python")
    df.columns = df.columns.str.strip()

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")

    return df[REQUIRED_COLUMNS].copy()


def validate_and_transform(df):
    """Separate valid rows from rejected rows."""
    df = df.copy()

    # Convert numeric columns; invalid text becomes missing data.
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["quantity"] = pd.to_numeric(
        df["quantity"], errors="coerce"
    )

    reasons = pd.Series("", index=df.index, dtype="object")

    def add_reason(mask, message):
        reasons.loc[mask] = reasons.loc[mask].apply(
            lambda old: f"{old}; {message}" if old else message
        )

    # Check missing required fields.
    for column in REQUIRED_COLUMNS:
        add_reason(
            df[column].isna(),
            f"Missing {column}"
        )

    # Check invalid business values.
    add_reason(df["price"] < 0, "Negative price")
    add_reason(df["quantity"] <= 0, "Quantity must be positive")

    # Keep the first occurrence of each order ID.
    duplicate = df["order_id"].duplicated(keep="first")
    add_reason(duplicate, "Duplicate order ID")

    rejected = df.loc[reasons != ""].copy()
    rejected["rejection_reason"] = reasons.loc[reasons != ""]

    clean = df.loc[reasons == ""].copy()

    # Store quantities as integers.
    clean["quantity"] = clean["quantity"].astype(int)

    return clean, rejected


def load_data(clean):
    """Load clean records into SQLite."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_FILE) as connection:
        clean.to_sql(
            "orders",
            connection,
            if_exists="replace",
            index=False
        )


def save_outputs(raw, clean, rejected):
    """Save rejected records and a quality report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    rejected.to_csv(REJECTED_FILE, index=False)

    report = {
        "input_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "missing_values_by_column": {
            key: int(value)
            for key, value in raw.isna().sum().items()
        },
        "duplicate_order_ids": int(
            raw["order_id"].duplicated().sum()
        ),
        "negative_prices": int(
            (pd.to_numeric(raw["price"], errors="coerce") < 0).sum()
        ),
        "invalid_quantities": int(
            (pd.to_numeric(raw["quantity"], errors="coerce") <= 0).sum()
        )
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print("\n--- PIPELINE REPORT ---")
    print(json.dumps(report, indent=4))
    print(f"\nDatabase: {DB_FILE}")
    print(f"Rejected rows: {REJECTED_FILE}")
    print(f"Quality report: {REPORT_FILE}")


def run_pipeline(file_path=RAW_FILE):
    """Run the complete ETL pipeline."""
    raw = extract_data(file_path)
    clean, rejected = validate_and_transform(raw)

    load_data(clean)
    save_outputs(raw, clean, rejected)

    return clean, rejected


if __name__ == "__main__":
    run_pipeline()
