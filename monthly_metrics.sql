-- ============================================================================
-- PharmEasy Regional Pulse -- Task 2.3: Region x Month Metrics & MoM Growth
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Monthly Total sales_inr per Region via SQL GROUP BY
-- ----------------------------------------------------------------------------
SELECT 
    r.region,
    r.tier,
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(o.order_id) AS order_count,
    ROUND(COALESCE(SUM(o.sales_inr), 0.0), 2) AS total_sales_inr,
    ROUND(COALESCE(SUM(o.profit_inr), 0.0), 2) AS total_profit_inr
FROM regions_master r
LEFT JOIN orders_clean o ON r.region = o.region
GROUP BY r.region, r.tier, strftime('%Y-%m', o.order_date)
ORDER BY r.region, month;


-- ----------------------------------------------------------------------------
-- 2. Pivoted Region x Month Sales with Explicit MoM Growth Percentages
-- Formula: ((Current Month - Previous Month) / Previous Month) * 100
-- ----------------------------------------------------------------------------
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
    state,
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
    END AS mom_may_to_jun_pct
FROM monthly_agg
ORDER BY apr_sales_inr + may_sales_inr + jun_sales_inr DESC;


-- ----------------------------------------------------------------------------
-- 3. Window Function (LAG) Implementation of Month-on-Month Growth
-- ----------------------------------------------------------------------------
WITH active_months AS (
    SELECT '2026-04' AS month
    UNION ALL SELECT '2026-05'
    UNION ALL SELECT '2026-06'
),
grid AS (
    SELECT r.region, r.state, r.tier, m.month
    FROM regions_master r
    CROSS JOIN active_months m
),
sales AS (
    SELECT 
        g.region,
        g.state,
        g.tier,
        g.month,
        ROUND(COALESCE(SUM(o.sales_inr), 0.0), 2) AS sales_inr
    FROM grid g
    LEFT JOIN orders_clean o 
        ON g.region = o.region 
       AND strftime('%Y-%m', o.order_date) = g.month
    GROUP BY g.region, g.state, g.tier, g.month
),
calc AS (
    SELECT 
        region,
        state,
        tier,
        month,
        sales_inr,
        LAG(sales_inr) OVER (PARTITION BY region ORDER BY month) AS prev_sales_inr
    FROM sales
)
SELECT 
    region,
    tier,
    month,
    sales_inr,
    prev_sales_inr,
    CASE 
        WHEN prev_sales_inr IS NULL OR prev_sales_inr = 0 THEN NULL
        ELSE ROUND(((sales_inr - prev_sales_inr) * 100.0) / prev_sales_inr, 2)
    END AS mom_growth_pct
FROM calc
ORDER BY region, month;
