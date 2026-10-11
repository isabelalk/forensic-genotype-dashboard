"""Neutralises spreadsheet formula injection in exported CSVs (CWE-1236)."""

import pandas as pd

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def neutralize_value(value):
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def neutralize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy whose string cells and column labels cannot start a formula."""
    if df.empty and len(df.columns) == 0:
        return df
    safe = df.map(neutralize_value)
    safe.columns = [neutralize_value(column) if isinstance(column, str) else column for column in df.columns]
    return safe
