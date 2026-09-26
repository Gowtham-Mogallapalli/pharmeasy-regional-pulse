"""
join_validation.py -- PharmEasy Regional Pulse Task 2.2: JOIN Validation Suite.
Executes and prints all required validation checks against pharmeasy.db:
1. Row-count check: LEFT JOIN vs INNER JOIN
2. Duplicate-key check: verify no order_id has COUNT(*) > 1
3. Null check: COUNT(*) vs COUNT(o.order_id) under LEFT JOIN (COUNT(*) pitfall)
4. Per-region order counts via LEFT JOIN + GROUP BY (ordered ascending)
"""

import sqlite3
import pandas as pd

DB_PATH = "pharmeasy.db"


def run_join_validation(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)

    print("=" * 80)
    print("TASK 2.2: JOIN VALIDATION & ZERO-MATCH REGION SURVIVAL PROOF")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Row-count check: LEFT JOIN vs INNER JOIN
    # -------------------------------------------------------------------------
    print("\n--- 1. ROW-COUNT CHECK (LEFT JOIN vs INNER JOIN) ---")
    query_row_count = """
    SELECT 'LEFT JOIN' AS join_type, COUNT(*) AS row_count
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    UNION ALL
    SELECT 'INNER JOIN' AS join_type, COUNT(*) AS row_count
    FROM regions_master r
    INNER JOIN orders_clean o ON r.region = o.region;
    """
    df_row_count = pd.read_sql_query(query_row_count, conn)
    print(df_row_count.to_string(index=False))

    left_rows = df_row_count.loc[df_row_count["join_type"] == "LEFT JOIN", "row_count"].values[0]
    inner_rows = df_row_count.loc[df_row_count["join_type"] == "INNER JOIN", "row_count"].values[0]
    print(f"\nAnalysis: LEFT JOIN produces {left_rows} rows while INNER JOIN produces {inner_rows} rows.")
    print("Difference = +1 row. The unmatched master region ('Kurnool') survives under LEFT JOIN with NULL padding.")
    assert left_rows == 2101, f"Expected 2101 for LEFT JOIN, got {left_rows}"
    assert inner_rows == 2100, f"Expected 2100 for INNER JOIN, got {inner_rows}"

    # -------------------------------------------------------------------------
    # 2. Duplicate-key check: order_id uniqueness
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- 2. DUPLICATE-KEY CHECK (GROUP BY order_id HAVING COUNT(*) > 1) ---")
    query_dup_key = """
    SELECT order_id, COUNT(*) AS count
    FROM orders_clean
    GROUP BY order_id
    HAVING COUNT(*) > 1;
    """
    df_dup_keys = pd.read_sql_query(query_dup_key, conn)
    if len(df_dup_keys) == 0:
        print("Result: 0 rows returned.")
        print("Success: Verified that no order_id appears more than once in 'orders_clean' (100% unique primary keys).")
    else:
        print(f"Warning: Found {len(df_dup_keys)} duplicate order_ids!")
        print(df_dup_keys.to_string(index=False))
    assert len(df_dup_keys) == 0, f"Expected 0 duplicates, got {len(df_dup_keys)}"

    # -------------------------------------------------------------------------
    # 3. Null check: COUNT(*) vs COUNT(o.order_id) under LEFT JOIN
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- 3. NULL CHECK: COUNT(*) vs COUNT(o.order_id) UNDER LEFT JOIN ---")
    print("(Demonstrating the classic COUNT(*) vs COUNT(fk) aggregation pitfall)")
    query_null_check = """
    SELECT 
        r.region,
        r.state,
        r.tier,
        COUNT(*) AS count_star,
        COUNT(o.order_id) AS count_fk,
        (COUNT(*) - COUNT(o.order_id)) AS diff,
        CASE 
            WHEN COUNT(*) != COUNT(o.order_id) THEN 'DISAGREEMENT (COUNT* Pitfall!)'
            ELSE 'MATCH'
        END AS comparison_status
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    GROUP BY r.region, r.state, r.tier
    ORDER BY count_fk ASC;
    """
    df_null_check = pd.read_sql_query(query_null_check, conn)
    print(df_null_check.to_string(index=False))

    kurnool_row = df_null_check[df_null_check["region"] == "Kurnool"].iloc[0]
    print(f"\nPitfall Demonstration:")
    print(f"  * Region: {kurnool_row['region']}")
    print(f"  * COUNT(*): {kurnool_row['count_star']} (WRONG: counts the single NULL-padded joined row)")
    print(f"  * COUNT(o.order_id): {kurnool_row['count_fk']} (CORRECT: correctly ignores NULL values in matching table)")
    assert kurnool_row["count_star"] == 1 and kurnool_row["count_fk"] == 0

    # -------------------------------------------------------------------------
    # 4. Per-region order counts via LEFT JOIN + GROUP BY (ordered ascending)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("--- 4. PER-REGION ORDER COUNTS (LEFT JOIN + GROUP BY, ASCENDING) ---")
    query_regional_orders = """
    SELECT 
        r.region,
        r.state,
        r.tier,
        COUNT(o.order_id) AS order_count
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    GROUP BY r.region, r.state, r.tier
    ORDER BY order_count ASC;
    """
    df_regional_orders = pd.read_sql_query(query_regional_orders, conn)
    print(df_regional_orders.to_string(index=False))

    total_orders = df_regional_orders["order_count"].sum()
    print(f"\nTotal Order Count Sum across all 10 regions: {total_orders}")
    assert total_orders == 2100, f"Expected 2100 total orders, got {total_orders}"

    conn.close()
    print("\n" + "=" * 80)
    print("ALL TASK 2.2 CHECKS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_join_validation()
