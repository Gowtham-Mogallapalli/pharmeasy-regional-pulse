"""
monthly_metrics.py -- PharmEasy Regional Pulse Task 2.3: Monthly Metrics & MoM Growth.
Computes total sales_inr per region per month (April/May/June 2026) via SQL GROUP BY,
and calculates Month-on-Month (MoM) growth for April->May and May->June using:
    (Current Month - Previous Month) / Previous Month * 100
"""

import sqlite3
import pandas as pd

DB_PATH = "pharmeasy.db"


def compute_monthly_metrics(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)

    print("=" * 95)
    print("TASK 2.3: REGION x MONTH METRICS & MONTH-ON-MONTH (MoM) GROWTH ANALYSIS")
    print("=" * 95)

    # 1. Monthly sales per region via SQL GROUP BY
    print("\n--- 1. TOTAL SALES_INR PER REGION PER MONTH (SQL GROUP BY) ---")
    query_monthly = """
    SELECT 
        r.region,
        r.tier,
        COALESCE(strftime('%Y-%m', o.order_date), 'No Orders') AS month,
        COUNT(o.order_id) AS order_count,
        ROUND(COALESCE(SUM(o.sales_inr), 0.0), 2) AS total_sales_inr,
        ROUND(COALESCE(SUM(o.profit_inr), 0.0), 2) AS total_profit_inr
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    GROUP BY r.region, r.tier, strftime('%Y-%m', o.order_date)
    ORDER BY r.region, month;
    """
    df_monthly = pd.read_sql_query(query_monthly, conn)
    print(df_monthly.to_string(index=False))

    # 2. Pivoted view with MoM growth rates
    print("\n" + "-" * 95)
    print("--- 2. REGION x MONTH PIVOT & MoM GROWTH (%) ---")
    query_pivot = """
    WITH monthly_agg AS (
        SELECT 
            r.region,
            r.state,
            r.tier,
            ROUND(COALESCE(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '2026-04' THEN o.sales_inr ELSE 0 END), 0.0), 2) AS apr_sales_inr,
            ROUND(COALESCE(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '2026-05' THEN o.sales_inr ELSE 0 END), 0.0), 2) AS may_sales_inr,
            ROUND(COALESCE(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '2026-06' THEN o.sales_inr ELSE 0 END), 0.0), 2) AS jun_sales_inr
        FROM regions_master r
        LEFT JOIN orders_clean o ON r.region = o.region
        GROUP BY r.region, r.state, r.tier
    )
    SELECT 
        region,
        tier,
        apr_sales_inr,
        may_sales_inr,
        jun_sales_inr,
        CASE 
            WHEN apr_sales_inr > 0 
            THEN ROUND(((may_sales_inr - apr_sales_inr) * 100.0) / apr_sales_inr, 2)
            ELSE NULL 
        END AS mom_apr_to_may_pct,
        CASE 
            WHEN may_sales_inr > 0 
            THEN ROUND(((jun_sales_inr - may_sales_inr) * 100.0) / may_sales_inr, 2)
            ELSE NULL 
        END AS mom_may_to_jun_pct,
        ROUND(apr_sales_inr + may_sales_inr + jun_sales_inr, 2) AS q2_total_sales_inr
    FROM monthly_agg
    ORDER BY q2_total_sales_inr DESC;
    """
    df_pivot = pd.read_sql_query(query_pivot, conn)
    print(df_pivot.to_string(index=False))

    conn.close()
    return df_pivot


if __name__ == "__main__":
    compute_monthly_metrics()
