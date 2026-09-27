"""
clean_data.py -- PharmEasy Regional Pulse Data Cleaning Pipeline.
Implements Task 1.2:
1. Remove exact duplicate rows (all 8 columns identical). Log the count removed.
2. Normalize the region column: strip leading/trailing whitespace and title-case it.
3. Impute missing category using a product->category lookup table from non-missing rows.
4. Impute missing profit_inr using category mean profit margins (profit_inr / sales_inr).
5. Save the result as orders_clean.csv.
"""

import logging
import os
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def clean_orders_data(
    raw_csv_path: str = "pharmeasy_orders_raw.csv",
    regions_master_path: str = "regions_master.csv",
    output_clean_path: str = "orders_clean.csv",
) -> pd.DataFrame:
    """Loads raw orders dataset and applies the 5-step cleaning pipeline in exact sequence."""
    if not os.path.exists(raw_csv_path) or not os.path.exists(regions_master_path):
        logger.info("Raw dataset not found. Generating deterministically via generate_dataset.py...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "generate_dataset.py"])

    logger.info("Loading raw dataset from '%s'...", raw_csv_path)
    df = pd.read_csv(raw_csv_path)
    logger.info("Initial raw dataset shape: %s rows, %s columns", df.shape[0], df.shape[1])

    # -------------------------------------------------------------
    # Step 1: Remove exact duplicate rows (all 8 columns identical)
    # -------------------------------------------------------------
    duplicate_mask = df.duplicated(keep="first")
    num_duplicates = int(duplicate_mask.sum())
    df_clean = df[~duplicate_mask].copy()
    logger.info(
        "Step 1 - Removed %d exact duplicate rows (remaining rows: %d).",
        num_duplicates,
        len(df_clean),
    )

    # -------------------------------------------------------------
    # Step 2: Normalize the region column
    # -------------------------------------------------------------
    raw_unique_regions = df_clean["region"].dropna().unique().tolist()
    logger.info("Step 2 - Raw unique regions (%d variants): %s", len(raw_unique_regions), raw_unique_regions)

    # Strip leading/trailing whitespace and title-case
    df_clean["region"] = df_clean["region"].astype(str).str.strip().str.title()
    normalized_regions = sorted(df_clean["region"].unique().tolist())
    logger.info("Step 2 - Normalized unique regions (%d active): %s", len(normalized_regions), normalized_regions)

    # Validate against regions_master.csv if available
    if os.path.exists(regions_master_path):
        regions_master_df = pd.read_csv(regions_master_path)
        canonical_regions = set(regions_master_df["region"].tolist())
        diff = set(normalized_regions) - canonical_regions
        if diff:
            logger.warning("Step 2 - Regions found not in master list: %s", diff)
        else:
            logger.info("Step 2 - All normalized regions successfully collapsed onto canonical regions in '%s'.", regions_master_path)

    # -------------------------------------------------------------
    # Step 3: Impute missing category using product->category lookup
    # -------------------------------------------------------------
    # Identify non-missing category rows
    valid_cat_mask = df_clean["category"].notna() & (df_clean["category"].astype(str).str.strip() != "")
    non_missing_cat_df = df_clean[valid_cat_mask]

    # Build product -> category deterministic lookup table
    prod_to_cat = (
        non_missing_cat_df.groupby("product")["category"]
        .first()
        .to_dict()
    )
    logger.info("Step 3 - Built product->category lookup table with %d unique products.", len(prod_to_cat))

    missing_cat_mask = ~valid_cat_mask
    num_missing_cat = int(missing_cat_mask.sum())
    logger.info("Step 3 - Missing category count before imputation: %d", num_missing_cat)

    # Impute missing category
    df_clean.loc[missing_cat_mask, "category"] = df_clean.loc[missing_cat_mask, "product"].map(prod_to_cat)
    remaining_missing_cat = int(df_clean["category"].isna().sum())
    logger.info("Step 3 - Imputed %d category values (remaining missing: %d).", num_missing_cat, remaining_missing_cat)

    # -------------------------------------------------------------
    # Step 4: Impute missing profit_inr using category mean profit margins
    # -------------------------------------------------------------
    df_clean["sales_inr"] = pd.to_numeric(df_clean["sales_inr"], errors="coerce")
    df_clean["profit_inr"] = pd.to_numeric(df_clean["profit_inr"], errors="coerce")

    # Compute row-level profit margin (profit_inr / sales_inr) on non-missing rows
    valid_profit_mask = df_clean["profit_inr"].notna()
    missing_profit_mask = ~valid_profit_mask
    num_missing_profit = int(missing_profit_mask.sum())
    logger.info("Step 4 - Missing profit_inr count before imputation: %d", num_missing_profit)

    valid_profit_df = df_clean[valid_profit_mask].copy()
    valid_profit_df["margin"] = valid_profit_df["profit_inr"] / valid_profit_df["sales_inr"]

    # Compute mean margin for each category
    category_mean_margins = valid_profit_df.groupby("category")["margin"].mean()
    logger.info("Step 4 - Category mean profit margins across non-missing rows:")
    for cat, margin in category_mean_margins.items():
        logger.info("         * %s: %.6f (%.2f%%)", cat, margin, margin * 100)

    # Impute missing profit_inr: sales_inr * category_mean_margin, rounded to 2 decimals
    missing_indices = df_clean[missing_profit_mask].index
    imputed_profits = (
        df_clean.loc[missing_indices, "sales_inr"]
        * df_clean.loc[missing_indices, "category"].map(category_mean_margins)
    ).round(2)
    df_clean.loc[missing_indices, "profit_inr"] = imputed_profits

    remaining_missing_profit = int(df_clean["profit_inr"].isna().sum())
    logger.info("Step 4 - Imputed %d profit values (remaining missing: %d).", num_missing_profit, remaining_missing_profit)

    # Ensure quantity is integer type
    df_clean["quantity"] = df_clean["quantity"].astype(int)

    # -------------------------------------------------------------
    # Step 5: Save result to orders_clean.csv
    # -------------------------------------------------------------
    if output_clean_path:
        df_clean.to_csv(output_clean_path, index=False)
        logger.info("Step 5 - Cleaned dataset saved to '%s' (%d rows, %d columns).", output_clean_path, len(df_clean), len(df_clean.columns))

    logger.info("Data cleaning pipeline completed successfully.")
    return df_clean


def validate_schema(df: pd.DataFrame, required_columns: list[str]) -> dict:
    """
    Validates that every required column is present in the DataFrame.

    Returns:
        dict: {
            "status": "validated" or "blocked_schema",
            "row_count": int,
            "missing_columns": list[str]
        }
    """
    present_cols = set(df.columns)
    missing = [c for c in required_columns if c not in present_cols]
    return {
        "status": "validated" if not missing else "blocked_schema",
        "row_count": len(df),
        "missing_columns": missing,
    }


if __name__ == "__main__":
    clean_orders_data()

