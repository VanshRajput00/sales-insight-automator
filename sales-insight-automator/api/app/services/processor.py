# Lead Engineer Note: processor.py is a pure-function module — it takes bytes,
# returns a dict. Zero FastAPI imports, zero AI imports. This means it can be
# unit-tested in complete isolation and reused by any future service
# (a scheduled job, a CLI tool, etc.) without dragging in the web framework.

import pandas as pd
from io import BytesIO
from typing import TypedDict


class SalesStats(TypedDict):
    total_revenue: float
    total_units_sold: int
    top_category: str
    top_category_revenue: float
    row_count: int
    summary_string: str


# Column name aliases — handles common real-world CSV inconsistencies
# e.g. "Revenue", "revenue", "Total Revenue", "sale_amount" all map correctly
REVENUE_ALIASES = ["revenue", "total revenue", "sale_amount", "sales", "amount", "price"]
UNITS_ALIASES   = ["units", "units sold", "quantity", "qty", "count"]
CATEGORY_ALIASES = ["category", "product_category", "segment", "type", "product type"]


def _find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    """Case-insensitive column resolver. Returns the first match or None."""
    normalized = {col.strip().lower(): col for col in df.columns}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    return None


def process_sales_csv(file_bytes: bytes) -> SalesStats:
    """
    Reads a CSV from raw bytes and returns a structured stats dict.

    Raises:
        ValueError: If the CSV is missing required columns or is malformed.
        pd.errors.ParserError: If the bytes are not valid CSV.
    """
    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except pd.errors.ParserError as e:
        raise ValueError(f"CSV parsing failed — file may be corrupted: {e}")

    if df.empty:
        raise ValueError("The uploaded CSV contains no data rows.")

    # --- Column Resolution ---
    revenue_col  = _find_column(df, REVENUE_ALIASES)
    units_col    = _find_column(df, UNITS_ALIASES)
    category_col = _find_column(df, CATEGORY_ALIASES)

    if not revenue_col:
        raise ValueError(
            f"No revenue column found. Expected one of: {REVENUE_ALIASES}. "
            f"Got columns: {df.columns.tolist()}"
        )

    # --- Numeric Coercion ---
    # Lead Engineer Note: coerce turns unparseable values (e.g. "$1,200") into NaN
    # rather than crashing. We then drop NaN rows and warn via the stats.
    df[revenue_col] = pd.to_numeric(
        df[revenue_col].astype(str).str.replace(r"[\$,]", "", regex=True),
        errors="coerce"
    )
    valid_df = df.dropna(subset=[revenue_col])
    dropped_rows = len(df) - len(valid_df)

    total_revenue = round(float(valid_df[revenue_col].sum()), 2)

    # --- Units Sold ---
    total_units = 0
    if units_col:
        valid_df[units_col] = pd.to_numeric(valid_df[units_col], errors="coerce")
        total_units = int(valid_df[units_col].sum(skipna=True))

    # --- Top Category ---
    top_category      = "N/A"
    top_cat_revenue   = 0.0
    if category_col:
        cat_group     = valid_df.groupby(category_col)[revenue_col].sum()
        top_category  = str(cat_group.idxmax())
        top_cat_revenue = round(float(cat_group.max()), 2)

    # --- Human-Readable Summary for AI Prompt ---
    summary_lines = [
        f"Q1 2026 Sales Data Summary ({len(valid_df)} records analyzed):",
        f"- Total Revenue: ${total_revenue:,.2f}",
        f"- Total Units Sold: {total_units:,}" if units_col else "- Units Sold: Data not available",
        f"- Top Performing Category: {top_category} (${top_cat_revenue:,.2f})" if category_col else "- Category breakdown: Not available",
    ]
    if dropped_rows > 0:
        summary_lines.append(f"- ⚠️  {dropped_rows} rows had unparseable revenue values and were excluded.")

    return SalesStats(
        total_revenue=total_revenue,
        total_units_sold=total_units,
        top_category=top_category,
        top_category_revenue=top_cat_revenue,
        row_count=len(valid_df),
        summary_string="\n".join(summary_lines),
    )
