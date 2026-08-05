"""
Data Cache Manager for Clinical Operations Portal
Pre-calculates metrics daily and serves from cache for performance
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

CACHE_DIR = Path("data_cache")
CACHE_DIR.mkdir(exist_ok=True)

class DataCache:
    def __init__(self):
        self.db_path = CACHE_DIR / "metrics.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for caching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cache tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_cache (
                dietician TEXT PRIMARY KEY,
                cohort TEXT,
                improvement_pct REAL,
                with_lab_data INTEGER,
                improved_count INTEGER,
                calculated_date DATE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS biomarker_cache (
                dietician TEXT PRIMARY KEY,
                biomarker_improvement REAL,
                calculated_date DATE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engagement_cache (
                dietician TEXT PRIMARY KEY,
                engagement_score REAL,
                calculated_date DATE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS programme_cache (
                programme_name TEXT PRIMARY KEY,
                patient_count INTEGER,
                appointment_count INTEGER,
                improvement_pct REAL,
                calculated_date DATE
            )
        ''')

        conn.commit()
        conn.close()

    def get_improvement_data(self, dietician=None):
        """Get cached improvement % data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dietician:
            cursor.execute('SELECT * FROM improvement_cache WHERE dietician = ?', (dietician,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        else:
            cursor.execute('SELECT * FROM improvement_cache ORDER BY improvement_pct DESC')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def set_improvement_data(self, data):
        """Cache improvement % data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for item in data:
            cursor.execute('''
                INSERT OR REPLACE INTO improvement_cache
                (dietician, cohort, improvement_pct, with_lab_data, improved_count, calculated_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                item.get('dietician'),
                item.get('cohort'),
                item.get('improvement_pct'),
                item.get('with_lab_data', 0),
                item.get('improved_count', 0),
                datetime.now().date()
            ))

        conn.commit()
        conn.close()

    def get_biomarker_data(self, dietician=None):
        """Get cached biomarker improvement data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dietician:
            cursor.execute('SELECT * FROM biomarker_cache WHERE dietician = ?', (dietician,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        else:
            cursor.execute('SELECT * FROM biomarker_cache')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def set_biomarker_data(self, data):
        """Cache biomarker improvement data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for item in data:
            cursor.execute('''
                INSERT OR REPLACE INTO biomarker_cache
                (dietician, biomarker_improvement, calculated_date)
                VALUES (?, ?, ?)
            ''', (
                item.get('dietician'),
                item.get('biomarker_improvement'),
                datetime.now().date()
            ))

        conn.commit()
        conn.close()

    def get_engagement_data(self, dietician=None):
        """Get cached engagement score data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dietician:
            cursor.execute('SELECT * FROM engagement_cache WHERE dietician = ?', (dietician,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        else:
            cursor.execute('SELECT * FROM engagement_cache')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def set_engagement_data(self, data):
        """Cache engagement score data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for item in data:
            cursor.execute('''
                INSERT OR REPLACE INTO engagement_cache
                (dietician, engagement_score, calculated_date)
                VALUES (?, ?, ?)
            ''', (
                item.get('dietician'),
                item.get('engagement_score'),
                datetime.now().date()
            ))

        conn.commit()
        conn.close()

    def is_cache_valid(self, hours=24):
        """Check if cache is still valid"""
        if not self.db_path.exists():
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if data exists and is recent
        cursor.execute('SELECT MAX(calculated_date) FROM improvement_cache')
        result = cursor.fetchone()
        conn.close()

        if not result or not result[0]:
            return False

        last_calc = datetime.strptime(result[0], '%Y-%m-%d')
        return datetime.now() - last_calc < timedelta(hours=hours)

# Global cache instance
cache = DataCache()
