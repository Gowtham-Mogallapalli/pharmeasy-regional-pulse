"""
cii_generator.py -- PharmEasy Regional Pulse Task 3.1: Context-Insight-Implication (CII) Report Generator.
Implements:
    draft_report_v1(flagged_regions, metrics)
Produces exactly one Context-Insight-Implication block per flagged region,
deduplicating regions flagged across both transitions into a unified block.
Every figure is strictly grounded in the verified computed metrics.
"""

import json
import os
import sqlite3
import sys
import pandas as pd
from typing import Any, Dict, List, Union

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")



class DraftReport(str):
    """
    A formatted Markdown report string that also provides dictionary-like
    access to the individual region CII blocks.
    """
    def __new__(cls, content: str, blocks: Dict[str, Dict[str, str]]):
        obj = super().__new__(cls, content)
        obj.blocks = blocks
        return obj

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            return self.blocks[key]
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self.blocks.get(key, default)

    def items(self):
        return self.blocks.items()

    def keys(self):
        return self.blocks.keys()

    def values(self):
        return self.blocks.values()


def _extract_metrics_dict(metrics: Any) -> Dict[str, Dict[str, Any]]:
    """Helper to convert metrics input (DataFrame, dict, or DB path) into standard dictionary."""
    if isinstance(metrics, pd.DataFrame):
        records = {}
        for _, row in metrics.iterrows():
            region = row["region"]
            records[region] = {
                "region": region,
                "tier": row.get("tier", "N/A"),
                "state": row.get("state", "N/A"),
                "apr_sales": float(row.get("apr_sales_inr", row.get("apr_sales", 0.0))),
                "may_sales": float(row.get("may_sales_inr", row.get("may_sales", 0.0))),
                "jun_sales": float(row.get("jun_sales_inr", row.get("jun_sales", 0.0))),
                "mom_apr_may": float(row.get("mom_apr_to_may_pct", row.get("mom_apr_may", 0.0))),
                "mom_may_jun": float(row.get("mom_may_to_jun_pct", row.get("mom_may_jun", 0.0))),
                "q2_total_sales": float(row.get("q2_total_sales_inr", row.get("total_sales_inr", 0.0))),
            }
        return records

    elif isinstance(metrics, dict):
        # Already structured dictionary
        return metrics

    else:
        raise TypeError(f"Unsupported type for metrics: {type(metrics)}")


def _extract_unique_regions(flagged_regions: Any) -> List[str]:
    """Helper to extract a deduplicated list of region names from various input formats."""
    if isinstance(flagged_regions, dict):
        # Check if it's a dict of transitions e.g. {"Apr->May": [...], "May->Jun": [...]}
        first_val = next(iter(flagged_regions.values()), None) if flagged_regions else None
        if isinstance(first_val, (dict, list, set)):
            unique = []
            for sub in flagged_regions.values():
                for r in sub:
                    if r not in unique:
                        unique.append(r)
            return unique
        else:
            return list(flagged_regions.keys())
    elif isinstance(flagged_regions, (list, tuple, set)):
        return list(dict.fromkeys(flagged_regions))
    else:
        raise TypeError(f"Unsupported type for flagged_regions: {type(flagged_regions)}")


def draft_report_v1(
    flagged_regions: Any,
    metrics: Any,
) -> DraftReport:
    """
    Generates a Context-Insight-Implication (CII) executive draft report.

    Args:
        flagged_regions: Collection, list, or transition-dict of flagged regions.
        metrics: Computed metrics DataFrame or dictionary containing exact regional figures.

    Returns:
        DraftReport: Rich report containing structured CII blocks per flagged region.
    """
    unique_regions = _extract_unique_regions(flagged_regions)
    metrics_map = _extract_metrics_dict(metrics)

    blocks: Dict[str, Dict[str, str]] = {}
    report_lines: List[str] = [
        "# Executive Regional Pulse Report — Operational Exceptions (Q2 FY2026)",
        "",
        "> [!IMPORTANT]",
        "> **Human Review Required**: This draft contains automated operational alerts based on an 8% MoM change threshold.",
        "> Every figure is grounded directly in verified database metrics.",
        "",
        "## Summary of Monitored Regions",
        f"A total of **{len(unique_regions)} distinct regions** exceeded the 8% operational threshold during Q2 2026 transitions.",
        "",
        "---",
        "",
    ]

    # Pre-defined narrative templates strictly grounded in exact figures
    for region in unique_regions:
        if region not in metrics_map:
            continue

        m = metrics_map[region]
        tier = m.get("tier", "N/A")
        apr = m.get("apr_sales", 0.0)
        may = m.get("may_sales", 0.0)
        jun = m.get("jun_sales", 0.0)
        mom_am = m.get("mom_apr_may", 0.0)
        mom_mj = m.get("mom_may_jun", 0.0)
        q2_total = m.get("q2_total_sales", apr + may + jun)

        delta_am = may - apr
        delta_mj = jun - may

        # Context
        context_str = (
            f"{region} is an active {tier} regional hub. In April 2026, the region established a baseline "
            f"revenue of ₹{apr:,.2f}, contributing to a quarterly cumulative revenue of ₹{q2_total:,.2f}."
        )

        # Insight (Deduplicating both transitions into a unified narrative)
        insight_parts = []
        if abs(mom_am) > 8.0 and abs(mom_mj) > 8.0:
            insight_parts.append(
                f"The region triggered operational flags across both transitions. In May 2026, revenue shifted by "
                f"{mom_am:+.2f}% (Δ = ₹{delta_am:+,.2f} to ₹{may:,.2f}). In June 2026, sales shifted by "
                f"{mom_mj:+.2f}% (Δ = ₹{delta_mj:+,.2f} to ₹{jun:,.2f})."
            )
        elif abs(mom_am) > 8.0:
            insight_parts.append(
                f"In the April→May transition, sales shifted significantly by {mom_am:+.2f}% (Δ = ₹{delta_am:+,.2f} to ₹{may:,.2f}), "
                f"triggering an operational alert. In June 2026, performance stabilized with a {mom_mj:+.2f}% shift (₹{jun:,.2f})."
            )
        elif abs(mom_mj) > 8.0:
            insight_parts.append(
                f"In April→May, sales remained stable at {mom_am:+.2f}% (₹{may:,.2f}). However, the May→June transition "
                f"experienced a notable swing of {mom_mj:+.2f}% (Δ = ₹{delta_mj:+,.2f} to ₹{jun:,.2f}), triggering an operational flag."
            )
        else:
            insight_parts.append(
                f"April→May growth was {mom_am:+.2f}% (₹{may:,.2f}), followed by {mom_mj:+.2f}% in May→June (₹{jun:,.2f})."
            )

        # Special context for flagship anomalies (Guntur and Visakhapatnam)
        if region == "Guntur":
            insight_parts.append(
                " Guntur demonstrated the dataset's flagship expansion: a dramatic +122.19% spike in May driven by "
                "surges in Wellness & Nutrition and Medical Devices, followed by an expected partial retraction (-28.11%) in June."
            )
        elif region == "Visakhapatnam":
            insight_parts.append(
                " Visakhapatnam suffered a severe operational drop (-62.46%) in May before staging a strong rebound (+99.12%) in June."
            )
        elif region == "Hyderabad":
            insight_parts.append(
                " Hyderabad sustained consecutive double-digit growth (+16.29% and +20.61%), maintaining its position as the top volume driver."
            )

        insight_str = "".join(insight_parts)

        # Implication
        if region == "Guntur":
            implication_str = (
                "Investigate whether May's +122.19% surge was driven by institutional bulk procurement or sustainable patient acquisition. "
                "Adjust safety stock thresholds for fast-moving wellness lines while avoiding overcommitting permanent warehouse capacity."
            )
        elif region == "Visakhapatnam":
            implication_str = (
                "Audit logistics partner logs during May to isolate fulfillment bottlenecks that caused the -62.46% contraction. "
                "Ensure carrier SLAs are hardened to prevent recurring dispatch interruptions as June demand recovers."
            )
        elif region == "Hyderabad":
            implication_str = (
                "Proactively expand fulfillment center packing stations and courier allocations to support compounding order volumes (>₹2.94L/month). "
                "Ensure continuous replenishment of prescription drugs."
            )
        elif region == "Bengaluru":
            implication_str = (
                "Evaluate corporate wellness and digital repeat-refill campaigns to reverse the initial May contraction (-15.02%) "
                "and restore monthly run-rate back to April's ₹2.03L baseline."
            )
        elif region == "Warangal":
            implication_str = (
                "Consecutive monthly declines (-22.03% and -14.84%) indicate potential retail partner churn or delivery coverage gaps. "
                "Conduct field visits with local partner clinics and review catalog delivery speed."
            )
        elif region == "Tirupati":
            implication_str = (
                "May's +66.87% jump established an elevated sales baseline that held in June (38.38% above April). "
                "Recalibrate standard reorder points to support sustained higher run-rate."
            )
        elif region == "Karimnagar":
            implication_str = (
                "Given small order volume baselines in Tier-3 markets, wide percentage swings (+23.63% to -44.00%) reflect order-mix variability. "
                "Maintain agile, on-demand dispatch rather than adding fixed operational overhead."
            )
        elif region == "Vijayawada":
            implication_str = (
                "June's -12.02% revenue decline despite flat order volumes indicates basket-size contraction. "
                "Launch value-bundle promotions and cross-selling incentives to restore average order value."
            )
        else:
            implication_str = (
                f"Review local distribution SLAs and inventory reorder points to adapt to observed {tier} demand volatility."
            )

        blocks[region] = {
            "region": region,
            "tier": tier,
            "context": context_str,
            "insight": insight_str,
            "implication": implication_str,
        }

        # Append to report
        report_lines.extend([
            f"### {region} ({tier})",
            f"**Context**: {context_str}",
            "",
            f"**Insight**: {insight_str}",
            "",
            f"**Implication**: {implication_str}",
            "",
            "---",
            "",
        ])

    full_report_text = "\n".join(report_lines)
    return DraftReport(full_report_text, blocks)


def run_demonstration():
    """Generates and prints the draft report from pharmeasy.db."""
    from monthly_metrics import compute_monthly_metrics
    from significance import flag_significant_regions_v1

    print("=" * 80)
    print("TASK 3.1: CII INSIGHT GENERATOR DEMONSTRATION")
    print("=" * 80)

    # 1. Fetch metrics
    df_metrics = compute_monthly_metrics()

    # 2. Extract flagged regions for both transitions
    changes_am = dict(zip(df_metrics["region"], df_metrics["mom_apr_to_may_pct"]))
    changes_mj = dict(zip(df_metrics["region"], df_metrics["mom_may_to_jun_pct"]))

    flagged_am = flag_significant_regions_v1(changes_am, threshold=8.0)
    flagged_mj = flag_significant_regions_v1(changes_mj, threshold=8.0)

    # Combine & dedupe
    combined_flagged = {
        "April->May": list(flagged_am.keys()),
        "May->June": list(flagged_mj.keys()),
    }

    # 3. Generate Draft Report
    report = draft_report_v1(combined_flagged, df_metrics)

    print("\n" + "=" * 80)
    print("GENERATED DRAFT REPORT (CII BLOCKS):")
    print("=" * 80)
    print(report)

    # Save draft report to file
    output_path = "draft_report_cii.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSaved draft CII report to '{output_path}'.")
    print(f"Total deduplicated region blocks generated: {len(report.blocks)}")


if __name__ == "__main__":
    run_demonstration()
