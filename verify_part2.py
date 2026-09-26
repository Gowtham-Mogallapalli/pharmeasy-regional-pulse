"""
verify_part2.py -- Complete Acceptance Criteria Verification Suite for Part 2.
"""
import json
import os
import sqlite3
import subprocess
import sys
import pandas as pd
from significance import (
    compute_percentage_change_v1,
    flag_significant_regions_v1,
    save_state_v1,
    load_previous_state_v1,
)


def test_acceptance_criteria_part2():
    print("=" * 70)
    print("PART 2 ACCEPTANCE CRITERIA VERIFICATION SUITE")
    print("=" * 70)

    db_path = "pharmeasy.db"
    assert os.path.exists(db_path), f"Database {db_path} does not exist!"
    conn = sqlite3.connect(db_path)

    # -------------------------------------------------------------------------
    # Criterion 1: Table row counts in pharmeasy.db
    # -------------------------------------------------------------------------
    regions_count = conn.execute("SELECT COUNT(*) FROM regions_master;").fetchone()[0]
    orders_count = conn.execute("SELECT COUNT(*) FROM orders_clean;").fetchone()[0]
    assert regions_count == 10, f"Expected 10 regions, got {regions_count}"
    assert orders_count == 2100, f"Expected 2100 orders, got {orders_count}"
    print(f"[PASS] Criterion 1: pharmeasy.db has regions_master ({regions_count} rows) and orders_clean ({orders_count} rows).")

    # -------------------------------------------------------------------------
    # Criterion 2: LEFT JOIN vs INNER JOIN row counts
    # -------------------------------------------------------------------------
    left_join_count = conn.execute("""
        SELECT COUNT(*) FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region;
    """).fetchone()[0]
    inner_join_count = conn.execute("""
        SELECT COUNT(*) FROM regions_master r INNER JOIN orders_clean o ON r.region = o.region;
    """).fetchone()[0]
    delta = left_join_count - inner_join_count
    assert left_join_count == 2101, f"Expected 2101 for LEFT JOIN, got {left_join_count}"
    assert inner_join_count == 2100, f"Expected 2100 for INNER JOIN, got {inner_join_count}"
    assert delta == 1, f"Expected delta of 1 row, got {delta}"

    # Verify that the 1 row is Kurnool
    unmatched_region = conn.execute("""
        SELECT r.region FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region WHERE o.order_id IS NULL;
    """).fetchone()[0]
    assert unmatched_region == "Kurnool", f"Expected Kurnool, got {unmatched_region}"
    print(f"[PASS] Criterion 2: LEFT JOIN = {left_join_count}, INNER JOIN = {inner_join_count} (Delta = {delta}, Kurnool's null row).")

    # -------------------------------------------------------------------------
    # Criterion 3: Duplicate-key check (order_id uniqueness)
    # -------------------------------------------------------------------------
    dup_keys = conn.execute("""
        SELECT order_id, COUNT(*) FROM orders_clean GROUP BY order_id HAVING COUNT(*) > 1;
    """).fetchall()
    assert len(dup_keys) == 0, f"Expected 0 duplicate order_ids, got {len(dup_keys)}"
    print(f"[PASS] Criterion 3: Duplicate-key check returned 0 rows (no duplicate order_ids).")

    # -------------------------------------------------------------------------
    # Criterion 4: COUNT(*) vs COUNT(order_id) for Kurnool
    # -------------------------------------------------------------------------
    kurnool_counts = conn.execute("""
        SELECT COUNT(*), COUNT(o.order_id)
        FROM regions_master r
        LEFT JOIN orders_clean o ON r.region = o.region
        WHERE r.region = 'Kurnool';
    """).fetchone()
    count_star, count_fk = kurnool_counts
    assert count_star == 1, f"Expected COUNT(*) = 1 for Kurnool, got {count_star}"
    assert count_fk == 0, f"Expected COUNT(order_id) = 0 for Kurnool, got {count_fk}"
    print(f"[PASS] Criterion 4: For Kurnool: COUNT(*) = {count_star} (wrong unmatched count) vs COUNT(order_id) = {count_fk} (correct).")

    # -------------------------------------------------------------------------
    # Compute MoM changes from database
    # -------------------------------------------------------------------------
    monthly_sales_query = """
    SELECT 
        r.region,
        ROUND(COALESCE(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '2026-04' THEN o.sales_inr ELSE 0 END), 0.0), 2) AS apr_sales,
        ROUND(COALESCE(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '2026-05' THEN o.sales_inr ELSE 0 END), 0.0), 2) AS may_sales,
        ROUND(COALESCE(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '2026-06' THEN o.sales_inr ELSE 0 END), 0.0), 2) AS jun_sales
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    WHERE r.region != 'Kurnool'
    GROUP BY r.region;
    """
    rows = conn.execute(monthly_sales_query).fetchall()
    
    apr_to_may_changes = {}
    may_to_jun_changes = {}
    for region, apr, may, jun in rows:
        apr_to_may_changes[region] = compute_percentage_change_v1(may, apr)
        may_to_jun_changes[region] = compute_percentage_change_v1(jun, may)

    # -------------------------------------------------------------------------
    # Criterion 5: April -> May significance flagging (threshold=8)
    # -------------------------------------------------------------------------
    flagged_apr_may = flag_significant_regions_v1(apr_to_may_changes, threshold=8)
    expected_apr_may_flagged = {
        "Hyderabad", "Warangal", "Visakhapatnam", "Guntur", "Tirupati", "Karimnagar", "Bengaluru"
    }
    actual_apr_may_flagged = set(flagged_apr_may.keys())
    assert actual_apr_may_flagged == expected_apr_may_flagged, (
        f"April->May mismatch!\nExpected: {expected_apr_may_flagged}\nGot: {actual_apr_may_flagged}"
    )
    assert "Vijayawada" not in actual_apr_may_flagged, "Vijayawada should NOT be flagged in Apr->May"
    assert "Nellore" not in actual_apr_may_flagged, "Nellore should NOT be flagged in Apr->May"
    print(f"[PASS] Criterion 5: April->May flagged exactly 7 regions: {sorted(actual_apr_may_flagged)}; Vijayawada and Nellore unflagged.")

    # -------------------------------------------------------------------------
    # Criterion 6: May -> June significance flagging (threshold=8)
    # -------------------------------------------------------------------------
    flagged_may_jun = flag_significant_regions_v1(may_to_jun_changes, threshold=8)
    expected_may_jun_flagged = {
        "Hyderabad", "Warangal", "Vijayawada", "Visakhapatnam", "Guntur", "Tirupati", "Karimnagar"
    }
    actual_may_jun_flagged = set(flagged_may_jun.keys())
    assert actual_may_jun_flagged == expected_may_jun_flagged, (
        f"May->June mismatch!\nExpected: {expected_may_jun_flagged}\nGot: {actual_may_jun_flagged}"
    )
    assert "Nellore" not in actual_may_jun_flagged, "Nellore should NOT be flagged in May->Jun"
    assert "Bengaluru" not in actual_may_jun_flagged, "Bengaluru should NOT be flagged in May->Jun"
    print(f"[PASS] Criterion 6: May->June flagged exactly 7 regions: {sorted(actual_may_jun_flagged)}; Nellore and Bengaluru unflagged.")

    # -------------------------------------------------------------------------
    # Criterion 7: Nellore is never flagged in either transition (stable baseline)
    # -------------------------------------------------------------------------
    assert "Nellore" not in actual_apr_may_flagged, "Nellore was flagged in April->May!"
    assert "Nellore" not in actual_may_jun_flagged, "Nellore was flagged in May->June!"
    print(f"[PASS] Criterion 7: Nellore is unflagged in BOTH transitions (+{apr_to_may_changes['Nellore']:.2f}% and +{may_to_jun_changes['Nellore']:.2f}%), acting as stable baseline.")

    # -------------------------------------------------------------------------
    # Criterion 8: State persistence round-trips correctly in a fresh Python process
    # -------------------------------------------------------------------------
    test_state_file = "test_roundtrip_state.json"
    sample_summary = {
        "month": "2026-04",
        "regional_sales": {r: apr for r, apr, _, _ in rows},
        "total_sales": round(sum(apr for _, apr, _, _ in rows), 2),
    }
    save_state_v1(sample_summary, test_state_file)

    # Launch a completely fresh Python subprocess to load the state and verify equality
    subprocess_code = f"""
import json, sys
from significance import load_previous_state_v1
loaded = load_previous_state_v1("{test_state_file}")
original = {json.dumps(sample_summary)}
assert loaded == original, f"Mismatch: {{loaded}} != {{original}}"
print("SUBPROCESS_SUCCESS")
"""
    result = subprocess.run(
        [sys.executable, "-c", subprocess_code],
        capture_output=True,
        text=True,
    )
    assert "SUBPROCESS_SUCCESS" in result.stdout, f"Subprocess roundtrip failed: {result.stderr}"

    # Clean up test file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)

    print(f"[PASS] Criterion 8: State persistence round-trips byte-for-byte in a fresh Python process.")

    conn.close()
    print("\n" + "=" * 70)
    print("ALL PART 2 ACCEPTANCE CRITERIA SUCCESSFULLY SATISFIED!")
    print("=" * 70)


if __name__ == "__main__":
    test_acceptance_criteria_part2()
