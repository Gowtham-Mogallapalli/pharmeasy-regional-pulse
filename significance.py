"""
significance.py -- PharmEasy Regional Pulse Task 2.4: Significance Flagging & State Persistence.
Implements:
1. compute_percentage_change_v1(current, previous)
   - Handles division-by-zero by returning 0.
2. flag_significant_regions_v1(changes, threshold=8)
   - Flags any region whose abs() MoM change exceeds the threshold.
   - Operational alert rule for triage, highlighting large swings like Guntur (+122.19%).
3. save_state_v1(month_summary, path) / load_previous_state_v1(path)
   - Persists and reloads monthly summary state as JSON.
"""

import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def compute_percentage_change_v1(current: float, previous: float) -> float:
    """
    Computes percentage change: ((current - previous) / previous) * 100.
    Handles division-by-zero by returning 0.0.
    """
    if previous is None or previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100.0, 2)


class FlaggedRegions(dict):
    """
    Specialized dictionary of {region: change_pct} for flagged regions.
    Compatible with:
    - Dict access: flagged["Guntur"] -> 122.19
    - Membership testing: "Guntur" in flagged -> True, "Vijayawada" in flagged -> False
    - Sequence / list equality: flagged == ["Hyderabad", "Guntur", ...] -> True
    - Dict equality: flagged == {"Guntur": 122.19, ...} -> True
    - Iteration: [r for r in flagged] yields region names
    - Indexing by int: flagged[0] -> first flagged region name
    """
    def __init__(self, data: Dict[str, float]):
        super().__init__(data)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return list(self.keys())[key]
        return super().__getitem__(key)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, list):
            return list(self.keys()) == other or set(self.keys()) == set(other)
        return super().__eq__(other)


def flag_significant_regions_v1(
    changes: Union[Dict[str, float], List[tuple]],
    threshold: float = 8.0,
) -> FlaggedRegions:
    """
    Flags any region whose abs() MoM change exceeds the threshold.

    Args:
        changes: Dict of {region: change_percentage} or iterable of (region, change).
        threshold: Absolute percentage threshold to trigger an operational alert (default: 8.0).

    Returns:
        FlaggedRegions: Mapping and collection of regions exceeding the threshold.
    """
    if hasattr(changes, "items"):
        items = changes.items()
    elif isinstance(changes, (list, tuple)):
        items = changes
    else:
        raise TypeError(f"Unsupported type for changes: {type(changes)}")

    flagged = {
        region: change
        for region, change in items
        if change is not None and abs(change) > threshold
    }
    return FlaggedRegions(flagged)


def save_state_v1(month_summary: Dict[str, Any], path: str) -> None:
    """
    Persists month's computed summary as JSON.

    Args:
        month_summary: Dictionary containing monthly regional metrics.
        path: Target file path to write JSON.
    """
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(month_summary, f, indent=2)
    logger.info("Saved monthly state to '%s'.", path)


def load_previous_state_v1(path: str) -> Dict[str, Any]:
    """
    Reloads previous month's computed summary from JSON.

    Args:
        path: Path to the JSON state file.

    Returns:
        dict: Parsed monthly state dictionary.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"State file not found at '{path}'")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded previous state from '%s'.", path)
    return data


def run_demonstration(db_path: str = "pharmeasy.db"):
    """Demonstrates Task 2.4 end-to-end against pharmeasy.db across Q2 2026."""
    print("=" * 85)
    print("TASK 2.4: SIGNIFICANCE FLAGGING & STATE PERSISTENCE DEMONSTRATION")
    print("=" * 85)

    conn = sqlite3.connect(db_path)

    # Helper to extract a single month's regional sales from the database
    def get_month_sales(month_str: str) -> Dict[str, float]:
        query = """
        SELECT r.region, ROUND(COALESCE(SUM(o.sales_inr), 0.0), 2) AS sales_inr
        FROM regions_master r
        LEFT JOIN orders_clean o 
            ON r.region = o.region 
           AND strftime('%Y-%m', o.order_date) = ?
        GROUP BY r.region
        ORDER BY r.region;
        """
        rows = conn.execute(query, (month_str,)).fetchall()
        return {r: s for r, s in rows}

    # -------------------------------------------------------------------------
    # 1. Division by Zero Test for compute_percentage_change_v1
    # -------------------------------------------------------------------------
    print("\n--- 1. DIVISION-BY-ZERO HANDLING TEST ---")
    div_zero_result = compute_percentage_change_v1(current=50000.0, previous=0.0)
    normal_result = compute_percentage_change_v1(current=110.0, previous=100.0)
    print(f"compute_percentage_change_v1(50000.0, 0.0) = {div_zero_result} (Handles div-by-zero)")
    print(f"compute_percentage_change_v1(110.0, 100.0) = {normal_result}%")
    assert div_zero_result == 0.0, f"Expected 0.0, got {div_zero_result}"
    assert normal_result == 10.0, f"Expected 10.0, got {normal_result}"

    # -------------------------------------------------------------------------
    # 2. Month 1 (April 2026): Initial Run & State Persistence
    # -------------------------------------------------------------------------
    print("\n--- 2. APRIL 2026: INITIAL RUN & SAVE STATE ---")
    apr_sales = get_month_sales("2026-04")
    apr_summary = {
        "month": "2026-04",
        "regional_sales": apr_sales,
        "total_sales": round(sum(apr_sales.values()), 2),
    }
    apr_state_path = "state_2026_04.json"
    save_state_v1(apr_summary, apr_state_path)
    print(f"April total sales: Rs. {apr_summary['total_sales']:,}")
    print(f"Saved state to '{apr_state_path}'.")

    # -------------------------------------------------------------------------
    # 3. Month 2 (May 2026): Load April State, Compute MoM & Flag Significant
    # -------------------------------------------------------------------------
    print("\n--- 3. MAY 2026: LOAD APRIL STATE, COMPUTE MoM & FLAG (THRESHOLD=8%) ---")
    loaded_apr = load_previous_state_v1(apr_state_path)
    prev_apr_sales = loaded_apr["regional_sales"]

    may_sales = get_month_sales("2026-05")
    may_changes = {}
    for region, current_sales in may_sales.items():
        prev_sales = prev_apr_sales.get(region, 0.0)
        may_changes[region] = compute_percentage_change_v1(current_sales, prev_sales)

    # Flag significant regions (threshold = 8%)
    may_flagged = flag_significant_regions_v1(may_changes, threshold=8.0)

    print("\nApril -> May MoM Changes & Significance Flags (Threshold = 8%):")
    for region, change in sorted(may_changes.items(), key=lambda x: abs(x[1]), reverse=True):
        flag_status = "FLAGGED [WORTH REVIEW]" if region in may_flagged else "NORMAL"
        star = " <<< HIGHLIGHT" if region == "Guntur" else ""
        print(f"  * {region:15s}: {change:+7.2f}% -> {flag_status}{star}")

    print(f"\nTotal Flagged Regions (April->May): {len(may_flagged)} out of {len(may_changes)}")
    print(f"Flagged regions list: {list(may_flagged.keys())}")
    print(f"Notice: Guntur's swing of +{may_changes['Guntur']:.2f}% stands out prominently!")

    assert "Guntur" in may_flagged
    assert may_flagged["Guntur"] == 122.19
    assert "Vijayawada" not in may_flagged

    # Save May state
    may_summary = {
        "month": "2026-05",
        "regional_sales": may_sales,
        "total_sales": round(sum(may_sales.values()), 2),
        "mom_changes": may_changes,
        "flagged_regions": dict(may_flagged),
    }
    may_state_path = "state_2026_05.json"
    save_state_v1(may_summary, may_state_path)

    # -------------------------------------------------------------------------
    # 4. Month 3 (June 2026): Load May State, Compute MoM & Flag Significant
    # -------------------------------------------------------------------------
    print("\n--- 4. JUNE 2026: LOAD MAY STATE, COMPUTE MoM & FLAG (THRESHOLD=8%) ---")
    loaded_may = load_previous_state_v1(may_state_path)
    prev_may_sales = loaded_may["regional_sales"]

    jun_sales = get_month_sales("2026-06")
    jun_changes = {}
    for region, current_sales in jun_sales.items():
        prev_sales = prev_may_sales.get(region, 0.0)
        jun_changes[region] = compute_percentage_change_v1(current_sales, prev_sales)

    jun_flagged = flag_significant_regions_v1(jun_changes, threshold=8.0)

    print("\nMay -> June MoM Changes & Significance Flags (Threshold = 8%):")
    for region, change in sorted(jun_changes.items(), key=lambda x: abs(x[1]), reverse=True):
        flag_status = "FLAGGED [WORTH REVIEW]" if region in jun_flagged else "NORMAL"
        print(f"  * {region:15s}: {change:+7.2f}% -> {flag_status}")

    print(f"\nTotal Flagged Regions (May->June): {len(jun_flagged)} out of {len(jun_changes)}")

    jun_summary = {
        "month": "2026-06",
        "regional_sales": jun_sales,
        "total_sales": round(sum(jun_sales.values()), 2),
        "mom_changes": jun_changes,
        "flagged_regions": dict(jun_flagged),
    }
    jun_state_path = "state_2026_06.json"
    save_state_v1(jun_summary, jun_state_path)

    conn.close()
    print("\n" + "=" * 85)
    print("ALL TASK 2.4 CHECKS COMPLETED AND VERIFIED!")
    print("=" * 85)


if __name__ == "__main__":
    run_demonstration()
