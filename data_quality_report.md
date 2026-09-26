# PharmEasy Regional Pulse — Data Quality Report (Task 1.4)

## 1. Executive Summary

This report provides a formal evaluation of the data quality transformations executed during **Task 1.2** and **Task 1.3** on the raw orders dataset (`pharmeasy_orders_raw.csv`). Each cleaning operation and validation check is mapped directly to the core industry-standard **Data Quality Dimensions**: *Uniqueness, Consistency, Completeness, Accuracy, Validity, Timeliness, and Relevance*.

---

## 2. Mapping of Cleaning Pipeline Fixes to Data Quality Dimensions

| Step | Cleaning Action (Task 1.2 & 1.3) | Primary Dimension | Secondary Dimension | Impact & Metric |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Exact Duplicate Removal**<br>Removed identical rows across all 8 columns | **Uniqueness** | **Accuracy** | Eliminated **59 duplicate records**, preventing inflated sales and order volume metrics (2,159 $\to$ 2,100 rows). |
| **2** | **Region Standardization**<br>Stripped whitespace and applied title-casing | **Consistency** | **Validity** | Collapsed **16 raw string variants** down to the **9 active canonical regions** matching `regions_master.csv`. |
| **3** | **Product $\to$ Category Lookup Imputation**<br>Built deterministic lookup table from non-missing rows | **Completeness** | **Accuracy** | Imputed all **48 missing category values** without row loss, achieving 100% product-category taxonomy correctness. |
| **4** | **Category-Specific Margin Profit Imputation**<br>Calculated category mean margin $(\frac{\text{profit}}{\text{sales}})$ | **Completeness** | **Accuracy & Validity** | Imputed all **94 missing `profit_inr` values** preserving realistic operational margins ($14.79\% - 15.28\%$). |
| **5** | **Schema & Constraint Validation (Task 1.3)**<br>`validate_schema()` checking required fields | **Validity** | **Relevance** | Guaranteed structural integrity, non-null guarantees, and contract compliance before analytical consumption. |

---

## 3. Detailed Dimension Breakdown

### 3.1 Uniqueness
* **Definition**: Every real-world event or transaction is represented exactly once; no duplicate records exist.
* **Problem Addressed**: Synthetic data generation introduced 59 duplicated order records where every column (`order_id`, `order_date`, `region`, `category`, `product`, `quantity`, `sales_inr`, `profit_inr`) matched an existing transaction.
* **Fix**: Filtered out redundant rows using complete row hashing (`df.duplicated(keep="first")`).
* **Result**: Row count reduced from **2,159 to 2,100**, ensuring analytical aggregations (total revenue, order counts) are not artificially inflated.

### 3.2 Consistency
* **Definition**: Data across records, systems, and references adhere to identical formats, definitions, and syntax.
* **Problem Addressed**: Regional names contained erratic casing and whitespace anomalies (e.g., `' hyderabad'`, `'HYDERABAD '`, `'bengaluru '`, `' BENGALURU'`, `'vijayawada'`, `' VIJAYAWADA'`). Grouping by raw `region` fragmented city metrics across multiple distinct buckets.
* **Fix**: Cleaned values with `.str.strip().str.title()`.
* **Result**: Reconciled 16 raw string permutations into exactly 9 standardized, active regional identifiers that seamlessly join with `regions_master.csv`.

### 3.3 Completeness
* **Definition**: The extent to which expected data values are populated without missing, null, or blank entries.
* **Problem Addressed**: 
  * 48 records had empty `category` strings (`""`).
  * 94 records had missing `profit_inr` values (`NaN`).
* **Fix**:
  1. *Category*: Imputed missing categories deterministically using a `product -> category` mapping constructed from non-missing rows.
  2. *Profit*: Imputed missing profits by computing the mean margin per product category across non-missing rows and applying $\text{sales\_inr} \times \text{category\_mean\_margin}$.
* **Result**: Achieved **100% data completeness** across all 2,100 rows with zero row drops.

### 3.4 Accuracy
* **Definition**: The degree to which data correctly describes the real-world object or phenomenon it represents.
* **Problem Addressed**: Dropping missing records or imputing with naive constant values (e.g., setting missing profit to 0 or using an overall dataset median) would introduce systemic distortion into category-level margin comparisons.
* **Fix**: 
  * The product-to-category taxonomy is deterministic (each product belongs to exactly one healthcare category), ensuring 100% ground-truth accuracy.
  * Category-level margin stratification recognizes that Medical Devices (15.28%) and Prescription Medicines (15.15%) have different margin structures than Personal Care (14.79%) or Lab Tests (14.83%).
* **Result**: Imputed financial numbers reflect domain-accurate profitability profiles rounded to standard monetary precision (2 decimal places).

### 3.5 Validity
* **Definition**: Conformance of values to business rules, expected formats, domain ranges, and schema definitions.
* **Problem Addressed**: Unchecked inputs could contain unexpected data types, out-of-boundary numbers, or schema drift (e.g. missing columns).
* **Fix**: 
  * Implemented `validate_schema()` to strictly verify the presence of all 8 core columns and flag `"blocked_schema"` upon schema violation.
  * Verified that normalized regions belong to the official master list in `regions_master.csv`.
  * Cast `quantity` to integer and financial amounts to floating-point numbers.
* **Result**: Complete schema and referential integrity adherence.

### 3.6 Timeliness
* **Definition**: Availability of data within the required operational or analytical timeframe.
* **Evaluation**: The orders dataset covers the continuous target quarter (April 1, 2026 through June 30, 2026) without gaps, ensuring recent and synchronized temporal analysis for regional pulse monitoring.

### 3.7 Relevance
* **Definition**: Alignment of collected data attributes with business objectives and decision-making utility.
* **Evaluation**: Each of the 8 retained attributes directly supports regional demand forecasting, category profit contribution, and fulfillment performance without redundant metadata clutter.

---

## 4. Before-and-After Quality Scorecard

| Metric | Raw Dataset (`pharmeasy_orders_raw.csv`) | Cleaned Dataset (`orders_clean.csv`) |
| :--- | :--- | :--- |
| **Total Rows** | 2,159 | 2,100 |
| **Duplicate Rows** | 59 | **0 (100% Unique)** |
| **Unique Region Strings** | 16 variants | **9 canonical regions** |
| **Missing Categories** | 48 rows | **0 (100% Complete)** |
| **Missing Profit Values** | 94 rows | **0 (100% Complete)** |
| **Null Count (All Columns)** | 142 total missing entries | **0 nulls** |
| **Schema Validation Status** | Validated (8/8 columns) | **Validated (8/8 columns)** |
