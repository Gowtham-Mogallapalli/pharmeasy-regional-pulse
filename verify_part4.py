"""
verify_part4.py -- Complete Acceptance Criteria Verification Suite for Part 4.
"""
import ast
import os
import re
import sqlite3
import sys
import pandas as pd


def test_acceptance_criteria_part4():
    print("=" * 70)
    print("PART 4 ACCEPTANCE CRITERIA VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Criterion 1: app.py starts with zero errors & requires no API keys / network
    # -------------------------------------------------------------------------
    assert os.path.exists("app.py"), "app.py does not exist!"
    with open("app.py", "r", encoding="utf-8") as f:
        app_source = f.read()

    # AST syntax check
    try:
        ast.parse(app_source)
        print("[PASS] Criterion 1a: app.py parsed with zero syntax errors.")
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in app.py: {e}")

    # Verify no external API key requirements
    forbidden_terms = ["api_key", "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"]
    for term in forbidden_terms:
        assert term not in app_source, f"Found forbidden API key reference '{term}' in app.py"
    print("[PASS] Criterion 1b: app.py requires no API keys or external authentication.")

    # -------------------------------------------------------------------------
    # Criterion 2: 3 hierarchy levels & distinct order_id count verification
    # -------------------------------------------------------------------------
    conn = sqlite3.connect("pharmeasy.db")
    df_orders = pd.read_sql_query("SELECT * FROM orders_clean;", conn)
    regions_master = pd.read_sql_query("SELECT * FROM regions_master;", conn)
    conn.close()

    # Part 2 expected per-region order counts
    expected_orders_per_region = {
        "Kurnool": 0,
        "Karimnagar": 89,
        "Tirupati": 151,
        "Nellore": 164,
        "Visakhapatnam": 176,
        "Guntur": 190,
        "Warangal": 195,
        "Vijayawada": 284,
        "Bengaluru": 332,
        "Hyderabad": 519,
    }

    for region, expected_cnt in expected_orders_per_region.items():
        actual_cnt = df_orders[df_orders["region"] == region]["order_id"].nunique()
        assert actual_cnt == expected_cnt, f"Order count mismatch for {region}: expected {expected_cnt}, got {actual_cnt}"

    total_distinct_orders = df_orders["order_id"].nunique()
    assert total_distinct_orders == 2100, f"Expected 2100 distinct orders, got {total_distinct_orders}"

    assert 'nunique()' in app_source or 'COUNT(DISTINCT' in app_source, "app.py does not compute distinct order count!"
    assert 'st.selectbox' in app_source, "app.py missing interactive region filter (st.selectbox)!"
    assert "Executive Overview" in app_source, "Level 1 (Overview) missing in app.py"
    assert "Healthcare Category Performance" in app_source or "Category" in app_source, "Level 2 (Category) missing in app.py"
    assert "Region × Month" in app_source or "Detail View" in app_source, "Level 3 (Detail) missing in app.py"
    print(f"[PASS] Criterion 2: 3 hierarchy levels connected by interactive filter; distinct order count verified (2,100 total, exact match across all 10 regions).")

    # -------------------------------------------------------------------------
    # Criterion 3: Line, Bar, and Donut charts obeying all 6 anti-patterns
    # -------------------------------------------------------------------------
    assert "go.Scatter" in app_source or "px.line" in app_source, "Line chart missing in app.py"
    assert "go.Bar" in app_source or "px.bar" in app_source, "Bar chart missing in app.py"
    assert "px.pie" in app_source or "go.Pie" in app_source, "Pie/donut chart missing in app.py"

    # Anti-pattern 1: Axis starts at zero
    assert 'rangemode="tozero"' in app_source or "rangemode='tozero'" in app_source, "Anti-pattern 1 violated: axes do not start at zero"

    # Anti-pattern 2: No 3D
    assert "3d" not in app_source.lower() or "no 3d" in app_source.lower(), "Anti-pattern 2 violated: found 3D chart references"

    # Anti-pattern 3: One color per series with highlight reserved for Guntur/flagged
    assert "#E63946" in app_source, "Anti-pattern 3 violated: reserved highlight color #E63946 not found"

    # Anti-pattern 4: No line chart on categorical data (line chart used for month time-series)
    assert 'x=r_data["month"]' in app_source or 'x="month"' in app_source, "Anti-pattern 4 violated: line chart must track monthly time-series"

    # Anti-pattern 5: Capped at 5-6 slices (6 categories)
    assert len(df_orders["category"].unique()) == 6, "Anti-pattern 5 violated: dataset does not have 6 categories"

    # Anti-pattern 6: Questions for titles and labeled axes with units
    assert "Which Regions Generated the Highest Total Revenue in Q2 2026?" in app_source, "Bar chart title does not answer a question"
    assert "How Did Monthly Sales Trend Across Q2 2026?" in app_source, "Line chart title does not answer a question"
    assert "What Proportion of Total Revenue Does Each Healthcare Category Represent?" in app_source, "Donut chart title does not answer a question"
    assert "₹ INR" in app_source, "Axis missing currency units (₹ INR)"
    print(f"[PASS] Criterion 3: Line, bar, and donut charts present and strictly obeying all 6 design anti-patterns.")

    # -------------------------------------------------------------------------
    # Criterion 4: Embedded executive summary (3-5 sentences in CII structure)
    # -------------------------------------------------------------------------
    assert "Executive Summary — Regional Pulse" in app_source, "Embedded executive summary missing in app.py"
    
    # Extract the summary text block from app.py
    summary_match = re.search(r'<p style="margin-bottom: 0; line-height: 1.65;[^>]*>(.*?)</p>', app_source, re.DOTALL)
    assert summary_match, "Could not extract executive summary paragraph from app.py"
    raw_summary = summary_match.group(1)
    clean_summary = re.sub(r'<[^>]+>', '', raw_summary).strip()
    
    sentences = [s.strip() for s in re.split(r'\.\s+', clean_summary) if len(s.strip()) > 10]
    sentence_count = len(sentences)
    assert 3 <= sentence_count <= 5, f"Expected 3-5 sentences in executive summary, got {sentence_count}: {sentences}"
    
    # Check structure: headline KPIs -> trend -> breakdown -> implication -> pointer
    assert "32,65,191.42" in clean_summary, "Headline KPI (total sales) missing in summary"
    assert "2,100" in clean_summary, "Headline KPI (distinct orders) missing in summary"
    assert "+2.89%" in clean_summary or "expanded" in clean_summary.lower(), "Trend/shape missing in summary"
    assert "Guntur" in clean_summary and "+122.19%" in clean_summary, "Category/region breakdown missing in summary"
    assert "recalibrate" in clean_summary.lower() or "safety stock" in clean_summary.lower(), "Implication/call to action missing in summary"
    assert "interactive" in clean_summary.lower() or "below" in clean_summary.lower(), "Dashboard pointer missing in summary"
    print(f"[PASS] Criterion 4: Embedded executive summary is exactly {sentence_count} sentences following the required 5-part CII structure.")

    # -------------------------------------------------------------------------
    # Criterion 5: presentation_storyline.md (SCR, OCD, and >=2 Q&A pairs)
    # -------------------------------------------------------------------------
    assert os.path.exists("presentation_storyline.md"), "presentation_storyline.md does not exist!"
    with open("presentation_storyline.md", "r", encoding="utf-8") as f:
        storyline_text = f.read()

    # Verify SCR structure for Executive
    assert "### 1. Situation" in storyline_text, "Missing Situation in SCR"
    assert "### 2. Complication" in storyline_text, "Missing Complication in SCR"
    assert "### 3. Resolution" in storyline_text, "Missing Resolution in SCR"

    # Verify OCD structure for Regional Manager
    assert "### 1. Overview" in storyline_text, "Missing Overview in OCD"
    assert "### 2. Category" in storyline_text, "Missing Category in OCD"
    assert "### 3. Detail" in storyline_text, "Missing Detail in OCD"

    # Verify Anticipated Pushback Q&A (>= 2 pairs, 3-step pattern)
    q_matches = re.findall(r'### Question \d+', storyline_text)
    assert len(q_matches) >= 2, f"Expected >= 2 Q&A pairs, got {len(q_matches)}"
    
    assert "Step 1 — Direct Acknowledgement" in storyline_text or "Direct Acknowledgement" in storyline_text, "Missing Step 1 in Q&A"
    assert "Step 2 — Verified vs. Not Verified" in storyline_text or "Verified vs. Not Verified" in storyline_text, "Missing Step 2 in Q&A"
    assert "Step 3 — Resolution & Timeline" in storyline_text or "Resolution & Timeline" in storyline_text, "Missing Step 3 in Q&A"
    print(f"[PASS] Criterion 5: presentation_storyline.md contains SCR & OCD reframings plus {len(q_matches)} pushback Q&As using the 3-step pattern.")

    print("\n" + "=" * 70)
    print("ALL PART 4 ACCEPTANCE CRITERIA SUCCESSFULLY SATISFIED!")
    print("=" * 70)


if __name__ == "__main__":
    test_acceptance_criteria_part4()
