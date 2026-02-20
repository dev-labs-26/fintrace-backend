"""
CSV/Excel Parser Service
─────────────────────────
Validates and parses uploaded CSV or Excel files into a Pandas DataFrame.
Supports multiple formats: CSV, TSV, Excel (.xlsx, .xls)

Expected columns:
    transaction_id  – string
    sender_id       – string (or from_account, source_id)
    receiver_id     – string (or to_account, destination_id)
    amount          – float  (must be positive)
    timestamp       – YYYY-MM-DD HH:MM:SS (or various date formats)

Optional columns:
    transaction_type – string (transfer, payment, withdrawal, etc.)
    currency         – string (USD, EUR, etc.)
    description      – string
    location         – string
"""

from __future__ import annotations

import io
from typing import IO

import pandas as pd
from fastapi import HTTPException


REQUIRED_COLUMNS = {
    "transaction_id",
    "sender_id",
    "receiver_id",
    "amount",
    "timestamp",
}

# Column name aliases for flexibility
COLUMN_ALIASES = {
    "sender_id": ["from_account", "source_id", "sender", "from_id", "payer_id"],
    "receiver_id": ["to_account", "destination_id", "receiver", "to_id", "payee_id"],
    "transaction_id": ["txn_id", "tx_id", "id", "transaction_number"],
    "amount": ["value", "transaction_amount", "sum"],
    "timestamp": ["date", "datetime", "transaction_date", "time", "created_at"],
}

# Supported timestamp formats
TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
]


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to match expected schema using aliases."""
    df.columns = df.columns.str.strip().str.lower()
    
    # Map aliases to standard names
    column_mapping = {}
    for standard_name, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            if col in aliases or col == standard_name:
                column_mapping[col] = standard_name
                break
    
    df = df.rename(columns=column_mapping)
    return df


def parse_timestamp(series: pd.Series) -> pd.Series:
    """Try multiple timestamp formats."""
    for fmt in TIMESTAMP_FORMATS:
        try:
            return pd.to_datetime(series, format=fmt, errors="coerce")
        except:
            continue
    
    # Fallback to pandas auto-detection
    return pd.to_datetime(series, errors="coerce", infer_datetime_format=True)


def parse_csv(file: IO[bytes], filename: str = "file.csv") -> pd.DataFrame:
    """
    Read and validate a CSV or Excel file-like object.

    Parameters
    ----------
    file : IO[bytes]
        File-like object containing transaction data
    filename : str
        Original filename to determine file type

    Returns
    -------
    pd.DataFrame
        Cleaned and typed DataFrame ready for graph construction.

    Raises
    ------
    HTTPException(400)
        On any format / content problem.
    """
    # ── Read raw bytes ────────────────────────────────────────────────────────
    try:
        content = file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot read uploaded file: {exc}")

    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Determine file type and parse ─────────────────────────────────────────
    filename_lower = filename.lower()
    
    try:
        if filename_lower.endswith(('.xlsx', '.xls')):
            # Parse Excel file
            df = pd.read_excel(
                io.BytesIO(content),
                dtype={
                    "transaction_id": str,
                    "sender_id": str,
                    "receiver_id": str,
                },
            )
        elif filename_lower.endswith('.tsv') or '\t' in content.decode('utf-8', errors='ignore')[:1000]:
            # Parse TSV file
            df = pd.read_csv(
                io.BytesIO(content),
                sep='\t',
                dtype={
                    "transaction_id": str,
                    "sender_id": str,
                    "receiver_id": str,
                },
                low_memory=False,
            )
        else:
            # Parse CSV file (default)
            df = pd.read_csv(
                io.BytesIO(content),
                dtype={
                    "transaction_id": str,
                    "sender_id": str,
                    "receiver_id": str,
                },
                low_memory=False,
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"File parsing error: {exc}")

    # ── Normalize column names ────────────────────────────────────────────────
    df = normalize_column_names(df)

    # ── Column validation ─────────────────────────────────────────────────────
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        available_cols = list(df.columns)
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {sorted(missing)}. Available columns: {available_cols}",
        )

    # ── Row count check ───────────────────────────────────────────────────────
    if df.empty:
        raise HTTPException(status_code=400, detail="File contains no data rows.")

    # ── Type coercion & cleaning ──────────────────────────────────────────────
    # String fields – strip whitespace, drop blanks
    for col in ("transaction_id", "sender_id", "receiver_id"):
        df[col] = df[col].astype(str).str.strip()
        blank_mask = df[col] == ""
        if blank_mask.any():
            raise HTTPException(
                status_code=400,
                detail=f"Column '{col}' contains empty values in rows: "
                       f"{df.index[blank_mask].tolist()[:10]}",
            )

    # Amount – must be a positive float
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    bad_amount = df["amount"].isna() | (df["amount"] <= 0)
    if bad_amount.any():
        raise HTTPException(
            status_code=400,
            detail=f"Column 'amount' contains invalid or non-positive values in "
                   f"{bad_amount.sum()} row(s).",
        )

    # Timestamp – parse with multiple format support
    df["timestamp"] = parse_timestamp(df["timestamp"])
    bad_ts = df["timestamp"].isna()
    if bad_ts.any():
        raise HTTPException(
            status_code=400,
            detail=f"Column 'timestamp' has {bad_ts.sum()} unparseable value(s). "
                   f"Supported formats: YYYY-MM-DD HH:MM:SS, DD/MM/YYYY, etc.",
        )

    # ── Deduplication ─────────────────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates(subset=["transaction_id"])
    if len(df) < before:
        pass  # silently drop duplicates; they would corrupt the graph

    df = df.reset_index(drop=True)
    return df
