"""
Database abstraction layer - supports PostgreSQL and SQLite
NO COST - Use free PostgreSQL hosting or local installation
"""
import os
import sqlite3
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database type detection
# Priority: USE_POSTGRES env var → DATABASE_URL presence → DATABASE_TYPE fallback
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
if not USE_POSTGRES and os.getenv('DATABASE_URL'):
    USE_POSTGRES = True
if not USE_POSTGRES:
    DB_TYPE = os.getenv('DATABASE_TYPE', 'sqlite').lower()
    USE_POSTGRES = DB_TYPE == 'postgresql'

# PostgreSQL connection
postgres_conn = None
print(f"[DB-STARTUP] USE_POSTGRES={USE_POSTGRES}")
if USE_POSTGRES:
    try:
        import psycopg
        from psycopg import connection

        DB_URL = os.getenv('DATABASE_URL', '')
        print(f"[DB-STARTUP] DATABASE_URL set: {bool(DB_URL)}")
        if DB_URL:
            # Parse connection string: postgresql://user:password@host:port/database
            print(f"[DB-STARTUP] Attempting PostgreSQL connection...")
            postgres_conn = psycopg.connect(DB_URL)
            print(f"[DB-STARTUP] [OK] PostgreSQL connected!")
            logger.info("[DB] Connected to PostgreSQL")
        else:
            print(f"[DB-STARTUP] DATABASE_URL not set - falling back to SQLite")
            logger.warning("[DB] DATABASE_URL not set - falling back to SQLite")
            USE_POSTGRES = False
    except ImportError as e:
        print(f"[DB-STARTUP] ImportError: {str(e)}")
        print(f"[DB-STARTUP] psycopg not installed - using SQLite")
        logger.warning(f"[DB] psycopg not installed: {str(e)}")
        USE_POSTGRES = False
    except Exception as e:
        print(f"[DB-STARTUP] PostgreSQL connection failed: {str(e)}")
        logger.error(f"[DB] PostgreSQL connection failed: {str(e)} - falling back to SQLite")
        USE_POSTGRES = False

# Use absolute path to ensure it works regardless of working directory
METRICS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metrics_cache.db')


def store_professional_daily_metric(provider_name, cohort, metric_date, appts_count, capacity,
                                   utilization_pct, qa_score, improvement_score, improvement_total,
                                   status, patient_count, with_lab_data, without_lab_data):
    """Store daily metric in database (PostgreSQL or SQLite)"""

    if USE_POSTGRES and postgres_conn:
        try:
            cursor = postgres_conn.cursor()
            cursor.execute('''
                INSERT INTO professional_daily_metrics
                (provider_name, cohort, metric_date, appts_count, capacity, utilization_pct,
                 qa_score, improvement_score, improvement_total, status,
                 patient_count, with_lab_data, without_lab_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider_name, metric_date) DO UPDATE SET
                    appts_count=EXCLUDED.appts_count,
                    capacity=EXCLUDED.capacity,
                    utilization_pct=EXCLUDED.utilization_pct,
                    qa_score=EXCLUDED.qa_score,
                    improvement_score=EXCLUDED.improvement_score,
                    improvement_total=EXCLUDED.improvement_total,
                    status=EXCLUDED.status,
                    patient_count=EXCLUDED.patient_count,
                    with_lab_data=EXCLUDED.with_lab_data,
                    without_lab_data=EXCLUDED.without_lab_data
            ''', (provider_name, cohort, metric_date, appts_count, capacity, utilization_pct,
                  qa_score, improvement_score, improvement_total, status,
                  patient_count, with_lab_data, without_lab_data))
            postgres_conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"[DB-POSTGRES] Error storing daily metric {provider_name} {metric_date}: {str(e)}")
            postgres_conn.rollback()
            return False
    else:
        # SQLite fallback
        try:
            conn = sqlite3.connect(METRICS_DB_PATH, timeout=60.0)
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            cursor.execute('''
                INSERT OR REPLACE INTO professional_daily_metrics
                (provider_name, cohort, metric_date, appts_count, capacity, utilization_pct,
                 qa_score, improvement_score, improvement_total, status,
                 patient_count, with_lab_data, without_lab_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (provider_name, cohort, metric_date, appts_count, capacity, utilization_pct,
                  qa_score, improvement_score, improvement_total, status,
                  patient_count, with_lab_data, without_lab_data))
            cursor.execute('COMMIT')
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[DB-SQLITE] Error storing daily metric {provider_name}: {str(e)}")
            return False


def query_daily_metrics_by_range(provider_name, start_date, end_date):
    """Query daily metrics for a date range and aggregate"""

    if USE_POSTGRES and postgres_conn:
        try:
            cursor = postgres_conn.cursor()
            cursor.execute('''
                SELECT
                    provider_name,
                    cohort,
                    SUM(appts_count)::INT as total_appts,
                    AVG(capacity)::INT as avg_capacity,
                    AVG(utilization_pct) as avg_utilization,
                    AVG(qa_score) as avg_qa_score,
                    AVG(improvement_score) as avg_improvement,
                    SUM(improvement_total)::INT as total_improved,
                    COUNT(DISTINCT metric_date) as day_count
                FROM professional_daily_metrics
                WHERE provider_name = %s
                  AND metric_date >= %s
                  AND metric_date <= %s
                GROUP BY provider_name, cohort
            ''', (provider_name, start_date, end_date))

            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    'provider_name': result[0],
                    'cohort': result[1],
                    'appts_count': result[2] or 0,
                    'capacity': result[3] or 0,
                    'utilization_pct': round(result[4] or 0, 1),
                    'qa_score': round(result[5] or 0, 1),
                    'improvement_score': round(result[6] or 0, 1),
                    'improvement_total': result[7] or 0,
                    'days_in_range': result[8] or 0
                }
            return None
        except Exception as e:
            logger.error(f"[DB-POSTGRES] Query error: {str(e)}")
            return None
    else:
        # SQLite fallback
        try:
            conn = sqlite3.connect(METRICS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    provider_name,
                    cohort,
                    SUM(appts_count) as total_appts,
                    AVG(capacity) as avg_capacity,
                    AVG(utilization_pct) as avg_utilization,
                    AVG(qa_score) as avg_qa_score,
                    AVG(improvement_score) as avg_improvement,
                    SUM(improvement_total) as total_improved,
                    COUNT(DISTINCT metric_date) as day_count
                FROM professional_daily_metrics
                WHERE provider_name = ?
                  AND metric_date >= ?
                  AND metric_date <= ?
                GROUP BY provider_name, cohort
            ''', (provider_name, start_date, end_date))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'provider_name': result[0],
                    'cohort': result[1],
                    'appts_count': int(result[2] or 0),
                    'capacity': int(result[3] or 0),
                    'utilization_pct': round(result[4] or 0, 1),
                    'qa_score': round(result[5] or 0, 1),
                    'improvement_score': round(result[6] or 0, 1),
                    'improvement_total': int(result[7] or 0),
                    'days_in_range': int(result[8] or 0)
                }
            return None
        except Exception as e:
            logger.error(f"[DB-SQLITE] Query error: {str(e)}")
            return None


def store_professional_metric(provider_name, cohort, start_date, end_date, appts_count, capacity,
                             utilization_pct, qa_score, improvement_score, improvement_total,
                             status, forecast_7d, patient_count, with_lab_data, without_lab_data):
    """Store metrics in database (PostgreSQL or SQLite)"""

    if USE_POSTGRES and postgres_conn:
        try:
            cursor = postgres_conn.cursor()
            cursor.execute('''
                INSERT INTO professional_metrics
                (provider_name, cohort, start_date, end_date, appts_count, capacity, utilization_pct,
                 qa_score, improvement_score, improvement_total, status, forecast_7d,
                 patient_count, with_lab_data, without_lab_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider_name, start_date, end_date) DO UPDATE SET
                    appts_count=EXCLUDED.appts_count,
                    capacity=EXCLUDED.capacity,
                    utilization_pct=EXCLUDED.utilization_pct,
                    qa_score=EXCLUDED.qa_score,
                    improvement_score=EXCLUDED.improvement_score,
                    improvement_total=EXCLUDED.improvement_total,
                    status=EXCLUDED.status,
                    forecast_7d=EXCLUDED.forecast_7d,
                    patient_count=EXCLUDED.patient_count,
                    with_lab_data=EXCLUDED.with_lab_data,
                    without_lab_data=EXCLUDED.without_lab_data
            ''', (provider_name, cohort, start_date, end_date, appts_count, capacity, utilization_pct,
                  qa_score, improvement_score, improvement_total, status, forecast_7d,
                  patient_count, with_lab_data, without_lab_data))
            postgres_conn.commit()
            cursor.close()
            logger.info(f"[DB-POSTGRES] Stored {provider_name}")
            return True
        except Exception as e:
            logger.error(f"[DB-POSTGRES] Error storing {provider_name}: {str(e)}")
            postgres_conn.rollback()
            return False
    else:
        # Fall back to SQLite with improved locking
        import time
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(METRICS_DB_PATH, timeout=60.0, isolation_level=None)
                cursor = conn.cursor()

                # Use immediate transaction to reduce lock time
                cursor.execute('BEGIN IMMEDIATE')
                cursor.execute('''
                    INSERT OR REPLACE INTO professional_metrics
                    (provider_name, cohort, start_date, end_date, appts_count, capacity, utilization_pct,
                     qa_score, improvement_score, improvement_total, status, forecast_7d,
                     patient_count, with_lab_data, without_lab_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (provider_name, cohort, start_date, end_date, appts_count, capacity, utilization_pct,
                      qa_score, improvement_score, improvement_total, status, forecast_7d,
                      patient_count, with_lab_data, without_lab_data))
                cursor.execute('COMMIT')
                conn.close()
                logger.info(f"[DB-SQLITE] Stored {provider_name}")
                return True
            except sqlite3.OperationalError as e:
                if 'locked' in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    logger.warning(f"[DB-SQLITE] Locked, retry {attempt+1}/{max_retries}")
                    continue
                else:
                    logger.error(f"[DB-SQLITE] Error storing {provider_name}: {str(e)}")
                    return False
            except Exception as e:
                logger.error(f"[DB-SQLITE] Error storing {provider_name}: {str(e)}")
                return False


def query_professional_metrics(start_date, end_date):
    """Query metrics for a date range - returns BEST MATCHING period per provider"""

    logger.info(f"[QUERY] Params: USE_POSTGRES={USE_POSTGRES}, postgres_conn={postgres_conn is not None}, start={start_date}, end={end_date}")

    if USE_POSTGRES and postgres_conn:
        try:
            # psycopg3 cursor with dict-like rows
            cursor = postgres_conn.cursor()
            logger.info(f"[DB-POSTGRES] Executing: Fetch ALL overlapping periods for {start_date} to {end_date}")
            # Fetch ALL overlapping periods - Python will select best match
            cursor.execute('''
                SELECT provider_name, cohort, appts_count, capacity, utilization_pct,
                       qa_score, improvement_score, improvement_total, status, forecast_7d,
                       patient_count, with_lab_data, without_lab_data, start_date, end_date
                FROM professional_metrics
                WHERE start_date <= %s AND end_date >= %s
                ORDER BY provider_name, end_date DESC, start_date DESC
            ''', (end_date, start_date))

            rows = cursor.fetchall()
            cursor.close()

            # Convert psycopg3 rows to dict
            raw_results = []
            if rows:
                # Get column names from cursor description
                col_names = [desc[0] for desc in cursor.description] if cursor.description else []
                for row in rows:
                    raw_results.append(dict(zip(col_names, row)))

            # SELECT BEST MATCHING PERIOD FOR EACH PROVIDER (in Python)
            from datetime import datetime as dt
            user_span_days = (dt.strptime(end_date, '%Y-%m-%d') - dt.strptime(start_date, '%Y-%m-%d')).days

            best_per_provider = {}
            for row in raw_results:
                provider = row['provider_name']
                period_span = (row['end_date'] - row['start_date']).days
                span_diff = abs(period_span - user_span_days)

                # Select if no prior entry, or if this period is a better match
                if provider not in best_per_provider:
                    best_per_provider[provider] = (row, span_diff)
                elif span_diff < best_per_provider[provider][1]:
                    best_per_provider[provider] = (row, span_diff)

            # Build final results (remove span_diff from output)
            results = [v[0] for v in best_per_provider.values()]

            logger.info(f"[DB-POSTGRES] SUCCESS: Selected best period for {len(results)} providers")
            return results
        except Exception as e:
            logger.error(f"[DB-POSTGRES] ERROR: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    else:
        # Fall back to SQLite
        logger.info(f"[DB-SQLITE] Using SQLite (USE_POSTGRES={USE_POSTGRES}, conn={postgres_conn is not None})")
        try:
            conn = sqlite3.connect(METRICS_DB_PATH)
            cursor = conn.cursor()
            logger.info(f"[DB-SQLITE] Executing: Fetch ALL overlapping periods for {start_date} to {end_date}")
            # Fetch ALL overlapping periods - Python will select best match
            cursor.execute('''
                SELECT provider_name, cohort, appts_count, capacity, utilization_pct,
                       qa_score, improvement_score, improvement_total, status, forecast_7d,
                       patient_count, with_lab_data, without_lab_data, start_date, end_date
                FROM professional_metrics
                WHERE start_date <= ? AND end_date >= ?
                ORDER BY provider_name, end_date DESC, start_date DESC
            ''', (end_date, start_date))

            rows = cursor.fetchall()
            conn.close()

            # Convert rows to dicts
            raw_results = []
            for row in rows:
                raw_results.append({
                    'provider_name': row[0],
                    'cohort': row[1],
                    'appts_count': row[2],
                    'capacity': row[3],
                    'utilization_pct': row[4],
                    'qa_score': row[5],
                    'improvement_score': row[6],
                    'improvement_total': row[7],
                    'status': row[8],
                    'forecast_7d': row[9],
                    'patient_count': row[10],
                    'with_lab_data': row[11],
                    'without_lab_data': row[12],
                    'start_date': row[13],
                    'end_date': row[14]
                })

            # SELECT BEST MATCHING PERIOD FOR EACH PROVIDER (in Python)
            from datetime import datetime as dt
            user_span_days = (dt.strptime(end_date, '%Y-%m-%d') - dt.strptime(start_date, '%Y-%m-%d')).days

            best_per_provider = {}
            for row in raw_results:
                provider = row['provider_name']
                period_span = (row['end_date'] - row['start_date']).days
                span_diff = abs(period_span - user_span_days)

                # Select if no prior entry, or if this period is a better match
                if provider not in best_per_provider:
                    best_per_provider[provider] = (row, span_diff)
                elif span_diff < best_per_provider[provider][1]:
                    best_per_provider[provider] = (row, span_diff)

            # Build final results (remove span_diff and date fields from output)
            results = []
            for row, _ in best_per_provider.values():
                # Remove start_date and end_date from output
                row_copy = row.copy()
                row_copy.pop('start_date', None)
                row_copy.pop('end_date', None)
                results.append(row_copy)

            logger.info(f"[DB-SQLITE] Selected best period for {len(results)} providers")
            return results
        except Exception as e:
            logger.error(f"[DB-SQLITE] Query error: {str(e)}")
            return []


def clear_metrics_for_date_range(start_date, end_date):
    """Delete metrics for a date range"""

    if USE_POSTGRES and postgres_conn:
        try:
            cursor = postgres_conn.cursor()
            cursor.execute('''
                DELETE FROM professional_metrics
                WHERE start_date = %s AND end_date = %s
            ''', (start_date, end_date))
            postgres_conn.commit()
            cursor.close()
            logger.info(f"[DB-POSTGRES] Cleared {start_date} to {end_date}")
            return True
        except Exception as e:
            logger.error(f"[DB-POSTGRES] Clear error: {str(e)}")
            postgres_conn.rollback()
            return False
    else:
        # Fall back to SQLite
        try:
            conn = sqlite3.connect(METRICS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM professional_metrics WHERE start_date = ? AND end_date = ?",
                          (start_date, end_date))
            conn.commit()
            conn.close()
            logger.info(f"[DB-SQLITE] Cleared {start_date} to {end_date}")
            return True
        except Exception as e:
            logger.error(f"[DB-SQLITE] Clear error: {str(e)}")
            return False


def init_postgres_schema():
    """Create PostgreSQL tables if they don't exist"""
    if USE_POSTGRES and postgres_conn:
        try:
            cursor = postgres_conn.cursor()

            # New daily metrics table (daily snapshots instead of periods)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_daily_metrics (
                    id SERIAL PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    cohort TEXT NOT NULL,
                    metric_date DATE NOT NULL,
                    appts_count INTEGER DEFAULT 0,
                    capacity INTEGER DEFAULT 0,
                    utilization_pct FLOAT DEFAULT 0,
                    qa_score FLOAT DEFAULT 0,
                    improvement_score FLOAT DEFAULT 0,
                    improvement_total INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'NA',
                    patient_count INTEGER DEFAULT 0,
                    with_lab_data INTEGER DEFAULT 0,
                    without_lab_data INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(provider_name, metric_date)
                );

                CREATE INDEX IF NOT EXISTS idx_daily_date ON professional_daily_metrics(metric_date);
                CREATE INDEX IF NOT EXISTS idx_daily_provider ON professional_daily_metrics(provider_name);
                CREATE INDEX IF NOT EXISTS idx_daily_provider_date ON professional_daily_metrics(provider_name, metric_date);
            ''')

            # Keep old table for compatibility (will deprecate later)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_metrics (
                    id SERIAL PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    cohort TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    appts_count INTEGER DEFAULT 0,
                    capacity INTEGER DEFAULT 0,
                    utilization_pct FLOAT DEFAULT 0,
                    qa_score FLOAT DEFAULT 0,
                    improvement_score FLOAT DEFAULT 0,
                    improvement_total INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'NA',
                    forecast_7d INTEGER DEFAULT 0,
                    patient_count INTEGER DEFAULT 0,
                    with_lab_data INTEGER DEFAULT 0,
                    without_lab_data INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(provider_name, start_date, end_date)
                );

                CREATE INDEX IF NOT EXISTS idx_date_range ON professional_metrics(start_date, end_date);
                CREATE INDEX IF NOT EXISTS idx_provider ON professional_metrics(provider_name);
            ''')

            postgres_conn.commit()
            cursor.close()
            logger.info("[DB-POSTGRES] Schema initialized (daily metrics + legacy periods)")
            return True
        except Exception as e:
            logger.error(f"[DB-POSTGRES] Schema init error: {str(e)}")
            postgres_conn.rollback()
            return False
    return True
