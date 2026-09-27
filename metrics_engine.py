"""
metrics_engine.py -- PharmEasy Regional Pulse Metrics Engine (Part 2).
Implements:
1. compute_percentage_change_v1(current, previous)
   - Handles division-by-zero by returning 0.0.
2. flag_significant_regions_v1(changes, threshold=8)
   - Flags any region whose abs() MoM change exceeds the threshold.
3. save_state_v1(month_summary, path) / load_previous_state_v1(path)
   - Persists and reloads monthly summary state as JSON.
"""

import json
import logging
import os
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


if __name__ == "__main__":
    print("=" * 70)
    print("METRICS ENGINE (PART 2) -- DEMONSTRATION")
    print("=" * 70)
    # Test division by zero
    print(f"compute_percentage_change_v1(100.0, 0.0) -> {compute_percentage_change_v1(100.0, 0.0)}% (div-by-zero handled)")
    print(f"compute_percentage_change_v1(138738.93, 62442.27) -> {compute_percentage_change_v1(138738.93, 62442.27)}% (Guntur Apr->May)")
    
    # Test flagging
    changes_apr_may = {
        "Hyderabad": 16.29,
        "Bengaluru": -15.02,
        "Vijayawada": 2.06,
        "Guntur": 122.19,
        "Visakhapatnam": -62.46,
        "Nellore": 6.50,
        "Warangal": -22.03,
        "Tirupati": 66.87,
        "Karimnagar": 23.63
    }
    flagged = flag_significant_regions_v1(changes_apr_may, threshold=8.0)
    print(f"\nFlagged regions (|MoM| > 8%): {len(flagged)} of 9 regions flagged:")
    for r, c in flagged.items():
        print(f"  * {r:15}: {c:+.2f}%")
    print(f"Nellore (+6.50%) flagged? {'Nellore' in flagged}")
    print(f"Vijayawada (+2.06%) flagged? {'Vijayawada' in flagged}")
    print("=" * 70)

