#!/usr/bin/env python3
"""
Setup tracking functionality in the existing database.
"""

import sqlite3
from datetime import datetime

def setup_tracking_table():
    """Add tracking table to the existing database."""
    conn = sqlite3.connect('net_rate_data.db')
    cursor = conn.cursor()
    
    # Create tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            driver TEXT NOT NULL,
            baseline_value REAL,
            baseline_date TEXT,
            date_added TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Tracking table created successfully!")

if __name__ == "__main__":
    setup_tracking_table()