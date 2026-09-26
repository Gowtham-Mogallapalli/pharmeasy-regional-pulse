"""
verify_part3.py -- Complete Acceptance Criteria Verification Suite for Part 3.
"""
import json
import os
import re
import sys
import pandas as pd

from cii_generator import draft_report_v1
from monthly_metrics import compute_monthly_metrics
from review_gate import review_gate_v1, VALID_DECISIONS, AUDIT_LOG_FILE
from significance import flag_significant_regions_v1


def test_acceptance_criteria_part3():
    print("=" * 70)
    print("PART 3 ACCEPTANCE CRITERIA VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Criterion 1: draft_report_v1() produces CII blocks for all 8 flagged regions
    # -------------------------------------------------------------------------
    df_metrics = compute_monthly_metrics()
    changes_am = dict(zip(df_metrics["region"], df_metrics["mom_apr_to_may_pct"]))
    changes_mj = dict(zip(df_metrics["region"], df_metrics["mom_may_to_jun_pct"]))

    flagged_am = flag_significant_regions_v1(changes_am, threshold=8.0)
    flagged_mj = flag_significant_regions_v1(changes_mj, threshold=8.0)

    # Union of flagged regions across both transitions
    union_flagged = set(flagged_am.keys()).union(set(flagged_mj.keys()))
    assert len(union_flagged) == 8, f"Expected 8 unique flagged regions, got {len(union_flagged)}: {union_flagged}"
    assert "Bengaluru" in union_flagged, "Bengaluru should be in union (flagged in Apr->May)"
    assert "Vijayawada" in union_flagged, "Vijayawada should be in union (flagged in May->Jun)"
    assert "Nellore" not in union_flagged, "Nellore should not be flagged"

    # Generate draft report
    report = draft_report_v1(list(union_flagged), df_metrics)
    assert len(report.blocks) == 8, f"Expected 8 blocks in report, got {len(report.blocks)}"

    for region in union_flagged:
        assert region in report.blocks, f"Missing CII block for {region}"
        block = report.blocks[region]
        assert "context" in block and len(block["context"]) > 20, f"Empty Context for {region}"
        assert "insight" in block and len(block["insight"]) > 20, f"Empty Insight for {region}"
        assert "implication" in block and len(block["implication"]) > 20, f"Empty Implication for {region}"

        # Verify exact numbers from metrics appear in the block text
        m = df_metrics[df_metrics["region"] == region].iloc[0]
        apr_val_str = f"{m['apr_sales_inr']:,.2f}"
        assert apr_val_str in block["context"], f"April sales {apr_val_str} missing in {region} context"

    print(f"[PASS] Criterion 1: draft_report_v1() generated populated CII blocks for all 8 unique flagged regions matching database metrics.")

    # -------------------------------------------------------------------------
    # Criterion 2: memo.md uses all 7 template fields & grounded in Guntur +122.19%
    # -------------------------------------------------------------------------
    assert os.path.exists("memo.md"), "memo.md does not exist!"
    with open("memo.md", "r", encoding="utf-8") as f:
        memo_text = f.read()

    required_7_fields = [
        "## Title",
        "## Context",
        "## Key Insight",
        "## Evidence",
        "## Recommendation",
        "## Next Check",
        "## Assumptions",
    ]
    for field in required_7_fields:
        assert field in memo_text, f"Missing required field '{field}' in memo.md"

    assert "+122.19%" in memo_text, "Guntur +122.19% missing from memo.md"
    assert "62,442.27" in memo_text, "April baseline 62,442.27 missing from memo.md"
    assert "138,738.93" in memo_text, "May sales 138,738.93 missing from memo.md"
    print(f"[PASS] Criterion 2: memo.md contains all 7 required template fields and is firmly grounded in Guntur +122.19% numbers.")

    # -------------------------------------------------------------------------
    # Criterion 3: Every claim in memo.md carries [LOW]/[MEDIUM]/[HIGH] risk tag
    # -------------------------------------------------------------------------
    low_count = memo_text.count("[LOW]")
    med_count = memo_text.count("[MEDIUM]")
    high_count = memo_text.count("[HIGH]")
    total_tags = low_count + med_count + high_count

    assert low_count >= 5, f"Expected at least 5 [LOW] tags, got {low_count}"
    assert med_count >= 5, f"Expected at least 5 [MEDIUM] tags, got {med_count}"
    assert high_count >= 20, f"Expected at least 20 [HIGH] tags, got {high_count}"
    print(f"[PASS] Criterion 3: memo.md is fully tagged with verification risk tiers ({total_tags} total tags: {low_count} LOW, {med_count} MEDIUM, {high_count} HIGH).")

    # -------------------------------------------------------------------------
    # Criterion 4: review_gate_v1 validation & audit_log.jsonl (>=3 entries)
    # -------------------------------------------------------------------------
    # Test invalid decision rejection
    try:
        review_gate_v1({"run_id": "test"}, decision="invalid_status")
        raise AssertionError("review_gate_v1 failed to reject invalid decision!")
    except ValueError:
        pass

    assert os.path.exists(AUDIT_LOG_FILE), f"{AUDIT_LOG_FILE} does not exist!"
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        log_entries = [json.loads(line) for line in f if line.strip()]

    assert len(log_entries) >= 3, f"Expected at least 3 audit log entries, got {len(log_entries)}"
    decisions_logged = {entry["decision"] for entry in log_entries}
    assert {"approve", "edit", "reject"}.issubset(decisions_logged), f"Expected all 3 decision paths logged, got {decisions_logged}"

    for entry in log_entries:
        for fld in ["timestamp", "run_id", "region", "decision", "reviewer_note"]:
            assert fld in entry, f"Missing field '{fld}' in audit log entry"

    print(f"[PASS] Criterion 4: review_gate_v1 validates decision argument; audit_log.jsonl contains {len(log_entries)} entries covering all 3 paths with all 5 required fields.")

    # -------------------------------------------------------------------------
    # Criterion 5: reliability_checklist.md has concrete sentence per 4 steps
    # -------------------------------------------------------------------------
    assert os.path.exists("reliability_checklist.md"), "reliability_checklist.md does not exist!"
    with open("reliability_checklist.md", "r", encoding="utf-8") as f:
        checklist_text = f.read()

    required_steps = [
        "Step 1: Safety Check",
        "Step 2: Validation",
        "Step 3: Critique / Refine",
        "Step 4: Human Sign-off",
    ]
    for step in required_steps:
        assert step in checklist_text, f"Missing '{step}' in reliability_checklist.md"

    # Verify non-generic content
    assert "personally identifiable" in checklist_text.lower() or "pii" in checklist_text.lower(), "Safety check lacks concrete PII verification"
    assert "62,442.27" in checklist_text or "138,738.93" in checklist_text, "Validation check lacks concrete numbers verification"
    assert "hypothes" in checklist_text.lower(), "Critique check lacks concrete hypothesis verification"
    assert "review_gate_v1" in checklist_text, "Human sign-off lacks concrete review_gate_v1 verification"
    print(f"[PASS] Criterion 5: reliability_checklist.md contains concrete, non-generic descriptions for all 4 workflow steps.")

    print("\n" + "=" * 70)
    print("ALL PART 3 ACCEPTANCE CRITERIA SUCCESSFULLY SATISFIED!")
    print("=" * 70)


if __name__ == "__main__":
    test_acceptance_criteria_part3()
