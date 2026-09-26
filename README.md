# PharmEasy Regional Pulse — Capstone Project (Q2 FY2026)

## 📌 Executive Cover Note

### 1. Headline Finding
> **Between April and May 2026, Guntur experienced an exceptional +122.19% revenue surge (+₹76,296.66 to reach ₹1,38,738.93 across 77 orders) driven 74.79% by high-ticket Wellness & Nutrition (+175.09%) and Medical Devices (+245.25%), before experiencing an immediate -28.11% normalization in June.**

### 2. The 4 Evaluation-Ready Artifacts
* **Streamlit Dashboard ([`app.py`](app.py))**: Live data exploration platform providing interactive 3-level filtering (Overview $\to$ Category $\to$ Detail) and 2D Plotly charts with zero baseline truncation.
* **CII Executive Narrative (Embedded in [`app.py`](app.py) & generated via [`draft_report.py`](draft_report.py))**: Synthesizes what the data means into Context–Insight–Implication blocks grounded strictly in verified SQL metrics.
* **One-Page Executive Recommendation Memo ([`memo.md`](memo.md))**: Structured 7-field action plan for executive leadership recommending dynamic safety-stock recalibration while rejecting premature permanent warehouse leasing.
* **Presentation Storyline & Pushback Q&A ([`presentation_storyline.md`](presentation_storyline.md))**: Live defense document reframing findings for Executive (SCR) and Regional Manager (OCD) audiences with a 4-part Direct Acknowledgement pushback Q&A.

### 3. Recommended Review Order
To review this capstone project as an integrated package, consume the artifacts in the following sequence:
1. **Interactive Dashboard ([`app.py`](app.py))**: Explore the macro network trends, regional rankings, and verify the distinct order-count KPIs.
2. **CII Narrative (Top of [`app.py`](app.py) / [`draft_report_cii.md`](draft_report_cii.md))**: Absorb the multi-month trajectory and operational context across all 8 flagged regions.
3. **Executive Recommendation Memo ([`memo.md`](memo.md))**: Inspect the deep-dive evidence, risk-tier tags (`[LOW]`, `[MEDIUM]`, `[HIGH]`), and capacity recommendations for Guntur.
4. **Presentation Storyline ([`presentation_storyline.md`](presentation_storyline.md))**: Review the dual-audience messaging frameworks and the 3-step pushback defense methodology.

### 4. Single Unverified Assumption Flagged Upfront
> **Institutional Procurement Hypothesis**: *The sudden appearance of bulk orders in specialized hardware (Nebulizers at ₹14,301.72 and Pulse Oximeters at ₹10,987.47, both with zero sales in April) is hypothesized to stem from local clinical practices, diagnostic labs, or institutional buyers batch-ordering equipment rather than spontaneous retail consumer demand — an assumption requiring field account reconciliation by July 20, 2026.*

---

## 🚀 Environment Setup & Reproduction Instructions

### 1. Prerequisites
- Python 3.10+ (or [`uv`](https://github.com/astral-sh/uv))
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Gowtham-Mogallapalli/pharmeasy-regional-pulse.git
cd pharmeasy-regional-pulse

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# or: .\.venv\Scripts\Activate.ps1 (On Windows PowerShell)

# Install required dependencies
pip install -r requirements.txt
```

### 3. Step-by-Step Reproduction Pipeline

#### Step 1: Generate Dataset (Deterministic seed = 2026)
```bash
python generate_dataset.py
```
*Outputs: `pharmeasy_orders_raw.csv` (2,159 rows) and `regions_master.csv` (10 rows).*

#### Step 2: Clean Dataset & Validate Schema
```bash
python clean_data.py
```
*Outputs: `orders_clean.csv` (2,100 deduplicated rows, imputed categories and profit margins, 0 nulls).*

#### Step 3: Build SQLite Database
```bash
python build_db.py
```
*Outputs: `pharmeasy.db` with indexed `regions_master` (10 rows) and `orders_clean` (2,100 rows).*

#### Step 4: Execute SQL Join Validation & Metrics Suite
```bash
python queries.py
```
*Validates the zero-match region `Kurnool` survival, proves `COUNT(*)` vs `COUNT(fk)` pitfall, and prints MoM metrics.*

#### Step 5: Run Review-Gate Test Harness
```bash
python review_gate.py
```
*Exercises approve/edit/reject paths and generates `audit_log.jsonl`.*

#### Step 6: Launch Streamlit Dashboard
```bash
streamlit run app.py
```
*Starts local web server at `http://localhost:8501` requiring zero external API keys or network access.*

---

## 📂 Repository File Index

| File | Purpose | Capstone Part |
| :--- | :--- | :---: |
| [`generate_dataset.py`](generate_dataset.py) | Deterministic synthetic dataset builder (seed 2026) | Part 1 |
| [`clean_data.py`](clean_data.py) | 5-step data cleaning pipeline + `validate_schema()` | Part 1 |
| [`data_quality_report.md`](data_quality_report.md) | Maps cleaning fixes to 7 Data Quality dimensions | Part 1 |
| [`build_db.py`](build_db.py) | Builds local SQLite database `pharmeasy.db` | Part 2 |
| [`queries.py`](queries.py) | JOIN validation + metrics SQL with printed outputs | Part 2 |
| [`metrics_engine.py`](metrics_engine.py) | Significance flagging (`threshold=8`) + JSON state persistence | Part 2 |
| [`draft_report.py`](draft_report.py) | Context-Insight-Implication (`draft_report_v1`) generator | Part 3 |
| [`memo.md`](memo.md) | 7-field executive recommendation memo on Guntur (+122.19%) with inline risk tiers | Part 3 |
| [`review_gate.py`](review_gate.py) | Human review-gate tool (`review_gate_v1`) + 3-path test harness | Part 3 |
| [`audit_log.jsonl`](audit_log.jsonl) | Immutable audit log generated by review-gate test harness | Part 3 |
| [`reliability_checklist.md`](reliability_checklist.md) | 4-step reliability workflow checklist | Part 3 |
| [`app.py`](app.py) | 3-level Streamlit dashboard + Plotly charts (6 anti-patterns obeyed) | Part 4 |
| [`presentation_storyline.md`](presentation_storyline.md) | SCR and OCD audience reframings + 4 pushback Q&As | Part 4 |
| [`README.md`](README.md) | Setup instructions + 4-artifact evaluation-ready cover note | Part 4 |
