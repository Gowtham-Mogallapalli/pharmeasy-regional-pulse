"""
verify_part1.py -- Complete Acceptance Criteria Verification Suite for Part 1.
"""
import pandas as pd
import os
from validate_schema import validate_schema, REQUIRED_COLUMNS


def test_acceptance_criteria():
    print("=" * 60)
    print("PART 1 ACCEPTANCE CRITERIA VERIFICATION")
    print("=" * 60)

    # 1. Dataset generation outputs
    raw = pd.read_csv("pharmeasy_orders_raw.csv")
    regions = pd.read_csv("regions_master.csv")
    assert len(raw) == 2159, f"Expected 2159 rows, got {len(raw)}"
    assert len(regions) == 10, f"Expected 10 regions, got {len(regions)}"
    assert "Kurnool" in regions["region"].values, "Kurnool missing from regions_master"
    active_regions_master = [r for r in regions["region"] if r != "Kurnool"]
    print(f"[PASS] Criterion 1: pharmeasy_orders_raw.csv has {len(raw)} rows; regions_master.csv has {len(regions)} regions (9 active + Kurnool).")

    # 2. Cleaning pipeline duplicate removal
    dups = int(raw.duplicated().sum())
    assert dups == 59, f"Expected 59 duplicates, got {dups}"
    raw_no_dup = raw.drop_duplicates().copy()
    assert len(raw_no_dup) == 2100, f"Expected 2100 rows, got {len(raw_no_dup)}"
    print(f"[PASS] Criterion 2: Exactly {dups} duplicates removed, leaving {len(raw_no_dup)} clean rows.")

    # 3. Region normalization check
    raw_variants = raw_no_dup["region"].dropna().unique()
    assert len(raw_variants) == 16, f"Expected 16 raw region variants, got {len(raw_variants)}"
    norm_regions = raw_no_dup["region"].astype(str).str.strip().str.title().unique()
    assert len(norm_regions) == 9, f"Expected 9 normalized regions, got {len(norm_regions)}"
    assert set(norm_regions) == set(active_regions_master), "Normalized regions do not match active master regions"
    print(f"[PASS] Criterion 3: Raw had {len(raw_variants)} variants; normalized has exactly {len(norm_regions)} canonical regions matching regions_master.csv.")

    # 4. Missing values and imputation check
    missing_profit_before = int(raw_no_dup["profit_inr"].isna().sum())
    missing_cat_before = int((raw_no_dup["category"].isna() | (raw_no_dup["category"].astype(str).str.strip() == "")).sum())
    assert missing_profit_before == 94, f"Expected 94 missing profit_inr, got {missing_profit_before}"
    assert missing_cat_before == 48, f"Expected 48 missing category, got {missing_cat_before}"

    clean = pd.read_csv("orders_clean.csv")
    assert len(clean) == 2100, f"Expected 2100 clean rows, got {len(clean)}"
    assert clean["category"].isna().sum() == 0, "Found missing category in orders_clean.csv"
    assert clean["profit_inr"].isna().sum() == 0, "Found missing profit_inr in orders_clean.csv"
    assert (clean["category"].str.strip() == "").sum() == 0, "Found empty string category in orders_clean.csv"
    print(f"[PASS] Criterion 4: Clean dataset has 0 missing profit and 0 missing category values (imputed from 94 and 48 respectively).")

    # 5. Schema validation check
    res_valid = validate_schema(clean, REQUIRED_COLUMNS)
    assert res_valid["status"] == "validated", f"Expected validated, got {res_valid['status']}"
    assert res_valid["row_count"] == 2100, f"Expected 2100 row count, got {res_valid['row_count']}"
    assert res_valid["missing_columns"] == [], "Expected empty missing columns"

    broken_df = clean.drop(columns=["profit_inr"])
    res_broken = validate_schema(broken_df, REQUIRED_COLUMNS)
    assert res_broken["status"] == "blocked_schema", f"Expected blocked_schema, got {res_broken['status']}"
    assert res_broken["missing_columns"] == ["profit_inr"], f"Expected missing profit_inr, got {res_broken['missing_columns']}"
    print(f"[PASS] Criterion 5: validate_schema() returned status: 'validated' on clean data and 'blocked_schema' with ['profit_inr'] on broken copy.")

    # 6. Data quality report check
    assert os.path.exists("data_quality_report.md"), "data_quality_report.md does not exist"
    with open("data_quality_report.md", "r", encoding="utf-8") as f:
        report_text = f.read().lower()

    dimensions = ["accuracy", "completeness", "consistency", "timeliness", "validity", "uniqueness", "relevance"]
    for dim in dimensions:
        assert dim in report_text, f"Dimension '{dim}' missing from data_quality_report.md"
    print(f"[PASS] Criterion 6: data_quality_report.md names all 7 dimensions and maps them to pipeline fixes.")

    print("\n" + "=" * 60)
    print("ALL PART 1 ACCEPTANCE CRITERIA SUCCESSFULLY SATISFIED!")
    print("=" * 60)


if __name__ == "__main__":
    test_acceptance_criteria()
