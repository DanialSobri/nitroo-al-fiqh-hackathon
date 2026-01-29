"""SQLite database for storing scraper sources and schedules"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager

# Database file path
DB_FILE = Path(__file__).parent / "scraper_data.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create scraper_sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraper_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                collection_name TEXT NOT NULL,
                output_dir TEXT,
                type TEXT NOT NULL DEFAULT 'custom',
                scraping_strategy TEXT DEFAULT 'direct_links',
                form_selector TEXT,
                form_button_selector TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Create scraper_schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraper_schedules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                use_selenium INTEGER NOT NULL DEFAULT 0,
                interval_value INTEGER,
                interval_unit TEXT,
                cron_year TEXT,
                cron_month TEXT,
                cron_day TEXT,
                cron_week TEXT,
                cron_day_of_week TEXT,
                cron_hour TEXT,
                cron_minute TEXT,
                cron_second TEXT,
                run_at TEXT,
                created_at TEXT,
                updated_at TEXT,
                last_run TEXT,
                next_run TEXT
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedules_source ON scraper_schedules(source)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON scraper_schedules(enabled)
        """)
        
        conn.commit()


# Initialize database on import
init_database()


def migrate_from_json():
    """Migrate existing JSON data to SQLite if JSON files exist"""
    import json
    from pathlib import Path
    
    # Migrate scraper sources
    sources_file = Path(__file__).parent / "scraper_sources.json"
    if sources_file.exists():
        try:
            with open(sources_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                custom_sources = data.get('custom_sources', {})
                
                # Check if we already have custom sources in DB
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM scraper_sources WHERE type = 'custom'")
                    count = cursor.fetchone()[0]
                    
                    # Only migrate if DB is empty
                    if count == 0 and custom_sources:
                        print(f"Migrating {len(custom_sources)} custom sources from JSON to SQLite...")
                        for source_id, source_data in custom_sources.items():
                            try:
                                add_custom_source(source_data)
                                print(f"  Migrated source: {source_id}")
                            except Exception as e:
                                print(f"  Error migrating source {source_id}: {e}")
                        print("Migration complete!")
        except Exception as e:
            print(f"Error migrating sources: {e}")
    
    # Migrate schedules
    schedules_file = Path(__file__).parent / "scraper_schedules.json"
    if schedules_file.exists():
        try:
            with open(schedules_file, 'r', encoding='utf-8') as f:
                schedules = json.load(f)
                
                # Check if we already have schedules in DB
                existing_schedules = get_all_schedules()
                
                # Only migrate if DB is empty
                if len(existing_schedules) == 0 and schedules:
                    print(f"Migrating {len(schedules)} schedules from JSON to SQLite...")
                    for schedule_data in schedules:
                        try:
                            add_schedule(schedule_data)
                            print(f"  Migrated schedule: {schedule_data.get('id', 'unknown')}")
                        except Exception as e:
                            print(f"  Error migrating schedule: {e}")
                    print("Migration complete!")
        except Exception as e:
            print(f"Error migrating schedules: {e}")


# Run migration on import (only if JSON files exist)
migrate_from_json()


# ==================== Scraper Sources Functions ====================

def get_all_sources() -> List[Dict[str, Any]]:
    """Get all scraper sources (default + custom)"""
    sources = []
    
    # Add default sources
    default_sources = {
        "bnm": {
            "id": "bnm",
            "name": "Bank Negara Malaysia",
            "url": "https://www.bnm.gov.my/banking-islamic-banking",
            "collection_name": "bnm_pdfs",
            "output_dir": "pdfs/bnm",
            "type": "default",
            "scraping_strategy": "direct_links",
            "form_selector": None,
            "form_button_selector": None,
            "created_at": None
        },
        "iifa": {
            "id": "iifa",
            "name": "IIFA Resolutions",
            "url": "https://iifa-aifi.org/en/resolutions",
            "collection_name": "iifa_resolutions",
            "output_dir": "pdfs/iifa",
            "type": "default",
            "scraping_strategy": "direct_links",
            "form_selector": None,
            "form_button_selector": None,
            "created_at": None
        },
        "sc": {
            "id": "sc",
            "name": "Securities Commission",
            "url": "https://www.sc.com.my/development/icm/shariah/resolutions-of-the-shariah-advisory-council-of-the-sc",
            "collection_name": "sc_resolutions",
            "output_dir": "pdfs/sc",
            "type": "default",
            "scraping_strategy": "direct_links",
            "form_selector": None,
            "form_button_selector": None,
            "created_at": None
        }
    }
    
    sources.extend(default_sources.values())
    
    # Get custom sources from database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scraper_sources WHERE type = 'custom'
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        for row in rows:
            source = dict(row)
            # Convert None strings to None
            for key in ['form_selector', 'form_button_selector', 'output_dir']:
                if source.get(key) == 'None' or source.get(key) == '':
                    source[key] = None
            sources.append(source)
    
    return sources


def get_source(source_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific source by ID"""
    # Check default sources first
    default_sources = {
        "bnm": {
            "id": "bnm",
            "name": "Bank Negara Malaysia",
            "url": "https://www.bnm.gov.my/banking-islamic-banking",
            "collection_name": "bnm_pdfs",
            "output_dir": "pdfs/bnm",
            "type": "default",
            "scraping_strategy": "direct_links",
            "form_selector": None,
            "form_button_selector": None,
            "created_at": None
        },
        "iifa": {
            "id": "iifa",
            "name": "IIFA Resolutions",
            "url": "https://iifa-aifi.org/en/resolutions",
            "collection_name": "iifa_resolutions",
            "output_dir": "pdfs/iifa",
            "type": "default",
            "scraping_strategy": "direct_links",
            "form_selector": None,
            "form_button_selector": None,
            "created_at": None
        },
        "sc": {
            "id": "sc",
            "name": "Securities Commission",
            "url": "https://www.sc.com.my/development/icm/shariah/resolutions-of-the-shariah-advisory-council-of-the-sc",
            "collection_name": "sc_resolutions",
            "output_dir": "pdfs/sc",
            "type": "default",
            "scraping_strategy": "direct_links",
            "form_selector": None,
            "form_button_selector": None,
            "created_at": None
        }
    }
    
    if source_id in default_sources:
        return default_sources[source_id]
    
    # Check custom sources in database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scraper_sources WHERE id = ?
        """, (source_id,))
        row = cursor.fetchone()
        
        if row:
            source = dict(row)
            # Convert None strings to None
            for key in ['form_selector', 'form_button_selector', 'output_dir']:
                if source.get(key) == 'None' or source.get(key) == '':
                    source[key] = None
            return source
    
    return None


def add_custom_source(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new custom source"""
    source_id = source_data.get('id')
    if not source_id:
        import uuid
        source_id = str(uuid.uuid4())
        source_data['id'] = source_id
    
    now = datetime.now().isoformat()
    source_data['type'] = 'custom'
    source_data['created_at'] = now
    source_data['updated_at'] = now
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scraper_sources (
                id, name, url, collection_name, output_dir, type,
                scraping_strategy, form_selector, form_button_selector,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_data['id'],
            source_data['name'],
            source_data['url'],
            source_data['collection_name'],
            source_data.get('output_dir'),
            source_data['type'],
            source_data.get('scraping_strategy', 'direct_links'),
            source_data.get('form_selector'),
            source_data.get('form_button_selector'),
            source_data['created_at'],
            source_data['updated_at']
        ))
    
    return source_data


def update_custom_source(source_id: str, source_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing custom source"""
    source_data['updated_at'] = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scraper_sources SET
                name = ?,
                url = ?,
                collection_name = ?,
                output_dir = ?,
                scraping_strategy = ?,
                form_selector = ?,
                form_button_selector = ?,
                updated_at = ?
            WHERE id = ? AND type = 'custom'
        """, (
            source_data.get('name'),
            source_data.get('url'),
            source_data.get('collection_name'),
            source_data.get('output_dir'),
            source_data.get('scraping_strategy', 'direct_links'),
            source_data.get('form_selector'),
            source_data.get('form_button_selector'),
            source_data['updated_at'],
            source_id
        ))
        
        if cursor.rowcount == 0:
            return None
    
    return get_source(source_id)


def delete_custom_source(source_id: str) -> bool:
    """Delete a custom source"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM scraper_sources WHERE id = ? AND type = 'custom'
        """, (source_id,))
        
        return cursor.rowcount > 0


# ==================== Scraper Schedules Functions ====================

def get_all_schedules() -> List[Dict[str, Any]]:
    """Get all schedules from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scraper_schedules
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        schedules = []
        for row in rows:
            schedule = dict(row)
            # Convert integer booleans to Python booleans
            schedule['enabled'] = bool(schedule.get('enabled', 1))
            schedule['use_selenium'] = bool(schedule.get('use_selenium', 0))
            schedules.append(schedule)
        
        return schedules


def get_schedule(schedule_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific schedule by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scraper_schedules WHERE id = ?
        """, (schedule_id,))
        row = cursor.fetchone()
        
        if row:
            schedule = dict(row)
            # Convert integer booleans to Python booleans
            schedule['enabled'] = bool(schedule.get('enabled', 1))
            schedule['use_selenium'] = bool(schedule.get('use_selenium', 0))
            return schedule
    
    return None


def add_schedule(schedule_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new schedule"""
    schedule_id = schedule_data.get('id')
    if not schedule_id:
        import uuid
        schedule_id = str(uuid.uuid4())
        schedule_data['id'] = schedule_id
    
    now = datetime.now().isoformat()
    schedule_data['created_at'] = now
    schedule_data['updated_at'] = now
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scraper_schedules (
                id, name, source, schedule_type, enabled, use_selenium,
                interval_value, interval_unit,
                cron_year, cron_month, cron_day, cron_week, cron_day_of_week,
                cron_hour, cron_minute, cron_second,
                run_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule_data['id'],
            schedule_data['name'],
            schedule_data['source'],
            schedule_data['schedule_type'],
            1 if schedule_data.get('enabled', True) else 0,
            1 if schedule_data.get('use_selenium', False) else 0,
            schedule_data.get('interval_value'),
            schedule_data.get('interval_unit'),
            schedule_data.get('cron_year'),
            schedule_data.get('cron_month'),
            schedule_data.get('cron_day'),
            schedule_data.get('cron_week'),
            schedule_data.get('cron_day_of_week'),
            schedule_data.get('cron_hour'),
            schedule_data.get('cron_minute'),
            schedule_data.get('cron_second'),
            schedule_data.get('run_at'),
            schedule_data['created_at'],
            schedule_data['updated_at']
        ))
    
    return schedule_data


def update_schedule(schedule_id: str, schedule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing schedule"""
    schedule_data['updated_at'] = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scraper_schedules SET
                name = ?,
                source = ?,
                schedule_type = ?,
                enabled = ?,
                use_selenium = ?,
                interval_value = ?,
                interval_unit = ?,
                cron_year = ?,
                cron_month = ?,
                cron_day = ?,
                cron_week = ?,
                cron_day_of_week = ?,
                cron_hour = ?,
                cron_minute = ?,
                cron_second = ?,
                run_at = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            schedule_data.get('name'),
            schedule_data.get('source'),
            schedule_data.get('schedule_type'),
            1 if schedule_data.get('enabled', True) else 0,
            1 if schedule_data.get('use_selenium', False) else 0,
            schedule_data.get('interval_value'),
            schedule_data.get('interval_unit'),
            schedule_data.get('cron_year'),
            schedule_data.get('cron_month'),
            schedule_data.get('cron_day'),
            schedule_data.get('cron_week'),
            schedule_data.get('cron_day_of_week'),
            schedule_data.get('cron_hour'),
            schedule_data.get('cron_minute'),
            schedule_data.get('cron_second'),
            schedule_data.get('run_at'),
            schedule_data['updated_at'],
            schedule_id
        ))
        
        if cursor.rowcount == 0:
            return None
    
    return get_schedule(schedule_id)


def delete_schedule(schedule_id: str) -> bool:
    """Delete a schedule"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM scraper_schedules WHERE id = ?
        """, (schedule_id,))
        
        return cursor.rowcount > 0


def update_schedule_last_run(schedule_id: str, last_run: str):
    """Update the last_run timestamp for a schedule"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scraper_schedules SET last_run = ? WHERE id = ?
        """, (last_run, schedule_id))
