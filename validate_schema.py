"""
validate_schema.py -- PharmEasy Regional Pulse Schema Validation.
Implements Task 1.3:
validate_schema(df, required_columns) function that checks every required
column is present and returns:
- status: "validated" or "blocked_schema"
- row_count: number of rows in the DataFrame
- missing_columns: list of missing columns (empty if all present)
"""

import logging
import pandas as pd
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "region",
    "category",
    "product",
    "quantity",
    "sales_inr",
    "profit_inr",
]


def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """
    Validates that all required columns are present in df.

    Returns:
        dict: {
            "status": "validated" or "blocked_schema",
            "row_count": int,
            "missing_columns": list[str]
        }
    """
    present_columns = set(df.columns)
    missing = [col for col in required_columns if col not in present_columns]
    status = "validated" if not missing else "blocked_schema"

    return {
        "status": status,
        "row_count": len(df),
        "missing_columns": missing,
    }


def run_demonstration():
    logger.info("Task 1.3: Running schema validation demonstration...")
    
    # 1. Load cleaned data
    clean_csv_path = "orders_clean.csv"
    logger.info("Loading cleaned dataset from '%s'...", clean_csv_path)
    df_clean = pd.read_csv(clean_csv_path)

    # 2. Run against valid cleaned data
    logger.info("--- Test Case 1: Valid Cleaned Data ---")
    result_valid = validate_schema(df_clean, REQUIRED_COLUMNS)
    print("\n[Test 1: Valid Cleaned Data Result]")
    print(result_valid)
    logger.info("Result: %s", result_valid)

    # 3. Run against deliberately broken copy (e.g. drop 'profit_inr')
    logger.info("\n--- Test Case 2: Broken Data (Dropping 'profit_inr' column) ---")
    df_broken = df_clean.drop(columns=["profit_inr"]).copy()
    result_broken = validate_schema(df_broken, REQUIRED_COLUMNS)
    print("\n[Test 2: Deliberately Broken Copy Result]")
    print(result_broken)
    logger.info("Result: %s", result_broken)

    # 4. Demonstrate multiple missing columns (optional robustness check)
    logger.info("\n--- Test Case 3: Broken Data (Dropping 'sales_inr' and 'category') ---")
    df_broken_multi = df_clean.drop(columns=["sales_inr", "category"]).copy()
    result_broken_multi = validate_schema(df_broken_multi, REQUIRED_COLUMNS)
    print("\n[Test 3: Multiple Missing Columns Result]")
    print(result_broken_multi)
    logger.info("Result: %s", result_broken_multi)


if __name__ == "__main__":
    run_demonstration()
