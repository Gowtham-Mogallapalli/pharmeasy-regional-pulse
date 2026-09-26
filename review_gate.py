"""
review_gate.py -- PharmEasy Regional Pulse Task 3.4: Review-Gate Tool & Audit Logging.
Implements:
    review_gate_v1(report, decision, reviewer_note="")
    - Validates decision in {"approve", "edit", "reject"}
    - Returns updated dictionary recording decision and downstream/external use permission
    - Appends an audit log line to audit_log.jsonl with:
      [timestamp, run_id, region, decision, reviewer_note]
    - Includes test harness exercising all 3 decision paths and invalid input handling
"""

import datetime
import json
import logging
import os
import uuid
from typing import Any, Dict, Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

VALID_DECISIONS = {"approve", "edit", "reject"}
AUDIT_LOG_FILE = "audit_log.jsonl"


def review_gate_v1(
    report: Union[Dict[str, Any], str],
    decision: str,
    reviewer_note: str = "",
    audit_log_path: str = AUDIT_LOG_FILE,
) -> Dict[str, Any]:
    """
    Validates reviewer decision and updates the report record while appending an audit log.

    Args:
        report: Dictionary (or string) containing the report content and metadata.
        decision: One of {"approve", "edit", "reject"}.
        reviewer_note: Optional qualitative feedback or instructions from the human reviewer.
        audit_log_path: Path to the JSONL audit log file (default: audit_log.jsonl).

    Returns:
        dict: Updated report record with decision and downstream allowance flag.

    Raises:
        ValueError: If decision is not in {"approve", "edit", "reject"}.
    """
    decision_clean = str(decision).strip().lower()
    if decision_clean not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid decision '{decision}'. Decision must be one of {sorted(VALID_DECISIONS)}."
        )

    # Convert report to dictionary representation
    if isinstance(report, dict):
        report_data = dict(report)
    elif isinstance(report, str):
        report_data = {"content": report}
    else:
        report_data = {"data": str(report)}

    # Extract metadata or assign defaults
    run_id = str(report_data.get("run_id", f"run_{uuid.uuid4().hex[:8]}"))
    region = str(report_data.get("region", "Guntur"))
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Determine downstream permission: strictly "approve" enables downstream dissemination
    downstream_allowed = (decision_clean == "approve")

    # Update report record
    updated_report = {
        **report_data,
        "run_id": run_id,
        "region": region,
        "decision": decision_clean,
        "downstream_allowed": downstream_allowed,
        "external_use_allowed": downstream_allowed,
        "reviewer_note": reviewer_note,
        "reviewed_at": timestamp,
    }

    # Prepare audit log record with the exact 5 required fields:
    # [timestamp, run_id, region, decision, reviewer_note]
    audit_entry = {
        "timestamp": timestamp,
        "run_id": run_id,
        "region": region,
        "decision": decision_clean,
        "reviewer_note": reviewer_note,
    }

    # Append audit log line atomically
    with open(audit_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry) + "\n")

    logger.info(
        "Logged review decision '%s' for run_id '%s' (region: '%s') to '%s'. Downstream allowed: %s",
        decision_clean,
        run_id,
        region,
        audit_log_path,
        downstream_allowed,
    )

    return updated_report


def run_test_harness(audit_log_path: str = AUDIT_LOG_FILE):
    """
    Exercises all 3 decision paths ("approve", "edit", "reject") and an invalid decision.
    Prints before/after states and verifies audit_log.jsonl entries.
    """
    print("=" * 80)
    print("TASK 3.4: REVIEW-GATE TOOL & AUDIT LOG TEST HARNESS")
    print("=" * 80)

    # Reset test audit log for clean demonstration
    if os.path.exists(audit_log_path):
        os.remove(audit_log_path)
    logger.info("Cleared previous '%s' for clean test harness run.", audit_log_path)

    # Sample base reports representing Guntur recommendation draft
    base_report_1 = {
        "run_id": "RUN-2026-05-GUNTUR-001",
        "region": "Guntur",
        "title": "Guntur Regional Pulse Surge Memo",
        "status": "pending_human_review",
    }
    base_report_2 = {
        "run_id": "RUN-2026-05-GUNTUR-002",
        "region": "Guntur",
        "title": "Guntur Warehouse Capacity Expansion Draft",
        "status": "pending_human_review",
    }
    base_report_3 = {
        "run_id": "RUN-2026-05-GUNTUR-003",
        "region": "Guntur",
        "title": "Guntur Long-Term Lease Agreement Proposal",
        "status": "pending_human_review",
    }

    # -------------------------------------------------------------------------
    # Path 1: "approve"
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- TEST CASE 1: APPROVE PATH ---")
    print(f"BEFORE STATE:\n{json.dumps(base_report_1, indent=2)}")

    res_approve = review_gate_v1(
        report=base_report_1,
        decision="approve",
        reviewer_note="Verified all figures against pharmeasy.db; numbers and CII logic approved for regional distribution.",
        audit_log_path=audit_log_path,
    )
    print(f"\nAFTER STATE:\n{json.dumps(res_approve, indent=2)}")
    assert res_approve["decision"] == "approve"
    assert res_approve["downstream_allowed"] is True
    print("\nResult: Decision recorded as 'approve' with downstream_allowed = True.")

    # -------------------------------------------------------------------------
    # Path 2: "edit"
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- TEST CASE 2: EDIT PATH ---")
    print(f"BEFORE STATE:\n{json.dumps(base_report_2, indent=2)}")

    res_edit = review_gate_v1(
        report=base_report_2,
        decision="edit",
        reviewer_note="Clarify in Assumptions that bulk institutional buying is an unverified hypothesis; do not publish yet.",
        audit_log_path=audit_log_path,
    )
    print(f"\nAFTER STATE:\n{json.dumps(res_edit, indent=2)}")
    assert res_edit["decision"] == "edit"
    assert res_edit["downstream_allowed"] is False
    print("\nResult: Decision recorded as 'edit' with downstream_allowed = False (held for revision).")

    # -------------------------------------------------------------------------
    # Path 3: "reject"
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- TEST CASE 3: REJECT PATH ---")
    print(f"BEFORE STATE:\n{json.dumps(base_report_3, indent=2)}")

    res_reject = review_gate_v1(
        report=base_report_3,
        decision="reject",
        reviewer_note="Rejected proposal to sign permanent warehouse lease based solely on May peak; June -28% pullback invalidates thesis.",
        audit_log_path=audit_log_path,
    )
    print(f"\nAFTER STATE:\n{json.dumps(res_reject, indent=2)}")
    assert res_reject["decision"] == "reject"
    assert res_reject["downstream_allowed"] is False
    print("\nResult: Decision recorded as 'reject' with downstream_allowed = False (blocked permanently).")

    # -------------------------------------------------------------------------
    # Path 4: Input Validation (Invalid Decision)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- TEST CASE 4: INPUT VALIDATION (INVALID DECISION) ---")
    try:
        review_gate_v1(
            report={"run_id": "RUN-ERR", "region": "Guntur"},
            decision="publish_now",  # Invalid
            reviewer_note="Testing invalid decision",
            audit_log_path=audit_log_path,
        )
        raise AssertionError("Expected ValueError was not raised!")
    except ValueError as e:
        print(f"Successfully caught expected ValueError: {e}")

    # -------------------------------------------------------------------------
    # Inspect audit_log.jsonl
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"--- VERIFYING AUDIT LOG FILE: '{audit_log_path}' ---")
    assert os.path.exists(audit_log_path), f"Audit log '{audit_log_path}' was not created!"
    
    with open(audit_log_path, "r", encoding="utf-8") as f:
        log_lines = [json.loads(line) for line in f if line.strip()]

    print(f"Total audit log entries recorded: {len(log_lines)}")
    assert len(log_lines) == 3, f"Expected 3 logged entries, got {len(log_lines)}"

    required_fields = ["timestamp", "run_id", "region", "decision", "reviewer_note"]
    for idx, entry in enumerate(log_lines, 1):
        print(f"\nAudit Log Entry #{idx}:")
        print(json.dumps(entry, indent=2))
        for field in required_fields:
            assert field in entry, f"Missing required field '{field}' in log entry #{idx}"

    print("\n" + "=" * 80)
    print("ALL TASK 3.4 REVIEW-GATE & AUDIT LOG TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_test_harness()
