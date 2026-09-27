"""
build_db.py -- PharmEasy Regional Pulse SQLite Database Builder.
Implements Task 2.1:
Loads Part 1 clean data into a local SQLite database file `pharmeasy.db`
using Python's built-in sqlite3 as two tables:
- regions_master (from regions_master.csv)
- orders_clean (from orders_clean.csv, 2100 rows)
"""

import logging
import os
import sqlite3
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "pharmeasy.db"
REGIONS_CSV = "regions_master.csv"
ORDERS_CLEAN_CSV = "orders_clean.csv"


def build_database(
    db_path: str = DB_PATH,
    regions_csv_path: str = REGIONS_CSV,
    orders_csv_path: str = ORDERS_CLEAN_CSV,
) -> sqlite3.Connection:
    """Builds and populates the SQLite database with regions_master and orders_clean."""
    logger.info("Initializing SQLite database at '%s'...", db_path)

    # Ensure source CSV files exist, auto-cleaning if missing
    if not os.path.exists(orders_csv_path) or not os.path.exists(regions_csv_path):
        logger.info("Clean dataset not found. Running clean_data.py...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "clean_data.py"])

    # Read data
    regions_df = pd.read_csv(regions_csv_path)
    orders_df = pd.read_csv(orders_csv_path)

    logger.info("Loaded %d regions from '%s'.", len(regions_df), regions_csv_path)
    logger.info("Loaded %d orders from '%s'.", len(orders_df), orders_csv_path)

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables if present to ensure clean rebuild
    cursor.execute("DROP TABLE IF EXISTS orders_clean;")
    cursor.execute("DROP TABLE IF EXISTS regions_master;")

    # Create regions_master table
    cursor.execute("""
        CREATE TABLE regions_master (
            region TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            tier TEXT NOT NULL
        );
    """)

    # Create orders_clean table
    cursor.execute("""
        CREATE TABLE orders_clean (
            order_id TEXT PRIMARY KEY,
            order_date TEXT NOT NULL,
            region TEXT NOT NULL,
            category TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            sales_inr REAL NOT NULL,
            profit_inr REAL NOT NULL,
            FOREIGN KEY (region) REFERENCES regions_master (region)
        );
    """)

    # Create indexes for optimal query performance
    cursor.execute("CREATE INDEX idx_orders_region ON orders_clean(region);")
    cursor.execute("CREATE INDEX idx_orders_date ON orders_clean(order_date);")
    cursor.execute("CREATE INDEX idx_orders_category ON orders_clean(category);")

    # Insert data
    logger.info("Inserting data into 'regions_master'...")
    regions_df.to_sql("regions_master", conn, if_exists="append", index=False)

    logger.info("Inserting data into 'orders_clean'...")
    orders_df.to_sql("orders_clean", conn, if_exists="append", index=False)

    conn.commit()

    # Verification queries
    cursor.execute("SELECT COUNT(*) FROM regions_master;")
    regions_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders_clean;")
    orders_count = cursor.fetchone()[0]

    # Verify zero-order region (Kurnool)
    cursor.execute("""
        SELECT r.region, r.state, r.tier
        FROM regions_master r
        LEFT JOIN orders_clean o ON r.region = o.region
        WHERE o.order_id IS NULL;
    """)
    zero_order_regions = cursor.fetchall()

    logger.info("Verification: 'regions_master' row count = %d", regions_count)
    logger.info("Verification: 'orders_clean' row count = %d", orders_count)
    logger.info("Verification: Zero-order regions found: %s", zero_order_regions)

    assert regions_count == 10, f"Expected 10 regions, got {regions_count}"
    assert orders_count == 2100, f"Expected 2100 orders, got {orders_count}"
    assert len(zero_order_regions) == 1 and zero_order_regions[0][0] == "Kurnool", \
        f"Expected Kurnool as sole zero-order region, got {zero_order_regions}"

    logger.info("Database '%s' built and verified successfully.", db_path)
    return conn


if __name__ == "__main__":
    conn = build_database()
    conn.close()
