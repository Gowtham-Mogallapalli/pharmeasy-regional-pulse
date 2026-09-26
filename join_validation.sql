-- ============================================================================
-- PharmEasy Regional Pulse -- Task 2.2: JOIN Validation Queries
-- Demonstrating that the zero-match region (Kurnool) survives LEFT JOIN
-- and reproducing the COUNT(*) vs COUNT(fk) aggregation pitfall.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Row-Count Check: LEFT JOIN vs INNER JOIN
-- ----------------------------------------------------------------------------
-- Expected: LEFT JOIN returns 2,101 rows (2,100 matched + 1 unmatched Kurnool row).
-- Expected: INNER JOIN returns 2,100 rows (drops unmatched Kurnool row).
SELECT 'LEFT JOIN' AS join_type, COUNT(*) AS total_rows
FROM regions_master r
LEFT JOIN orders_clean o ON r.region = o.region
UNION ALL
SELECT 'INNER JOIN' AS join_type, COUNT(*) AS total_rows
FROM regions_master r
INNER JOIN orders_clean o ON r.region = o.region;


-- ----------------------------------------------------------------------------
-- 2. Duplicate-Key Check: Verify primary key uniqueness in orders_clean
-- ----------------------------------------------------------------------------
-- Expected: Returns 0 rows (no order_id appears more than once).
SELECT order_id, COUNT(*) AS occurrence_count
FROM orders_clean
GROUP BY order_id
HAVING COUNT(*) > 1;


-- ----------------------------------------------------------------------------
-- 3. Null Check: COUNT(*) vs COUNT(o.order_id) under LEFT JOIN
-- ----------------------------------------------------------------------------
-- Demonstrates the classic COUNT(*) vs COUNT(fk) pitfall:
-- COUNT(*) counts all rows including the NULL-padded row (yielding 1 for Kurnool).
-- COUNT(o.order_id) ignores NULLs in the foreign/matching table (yielding 0 for Kurnool).
SELECT 
    r.region,
    r.state,
    r.tier,
    COUNT(*) AS count_star,
    COUNT(o.order_id) AS count_fk,
    (COUNT(*) - COUNT(o.order_id)) AS diff,
    CASE 
        WHEN COUNT(*) != COUNT(o.order_id) THEN 'DISAGREEMENT (COUNT* Pitfall!)' 
        ELSE 'AGREEMENT' 
    END AS validation_status
FROM regions_master r
LEFT JOIN orders_clean o ON r.region = o.region
GROUP BY r.region, r.state, r.tier
ORDER BY count_fk ASC;


-- ----------------------------------------------------------------------------
-- 4. Per-Region Order Counts via LEFT JOIN + GROUP BY (Ordered Ascending)
-- ----------------------------------------------------------------------------
-- Correctly using COUNT(o.order_id) so zero-order regions report 0 orders.
SELECT 
    r.region,
    r.state,
    r.tier,
    COUNT(o.order_id) AS order_count,
    ROUND(COALESCE(SUM(o.sales_inr), 0.0), 2) AS total_sales_inr,
    ROUND(COALESCE(SUM(o.profit_inr), 0.0), 2) AS total_profit_inr
FROM regions_master r
LEFT JOIN orders_clean o ON r.region = o.region
GROUP BY r.region, r.state, r.tier
ORDER BY order_count ASC;
