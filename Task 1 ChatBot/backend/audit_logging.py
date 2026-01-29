"""Audit Logging Module for tracking token usage and query history"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
import json


class AuditLogger:
    """Audit logger for tracking token usage and query history"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the audit logger with database connection"""
        if db_path is None:
            # Default to backend directory
            db_path = Path(__file__).parent / "audit_logs.db"
        self.db_path = Path(db_path)
        self._init_database()
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize the audit logs database table"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create audit_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    llm_provider TEXT NOT NULL,
                    llm_model TEXT NOT NULL,
                    
                    -- Token usage
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    
                    -- Query metadata
                    collections_searched TEXT,  -- JSON array
                    num_sources_found INTEGER,
                    num_sources_cited INTEGER,
                    max_results INTEGER,
                    min_score REAL,
                    
                    -- Response metadata
                    answer_length INTEGER,
                    response_time_ms INTEGER,
                    
                    -- Error tracking
                    error_message TEXT,
                    success INTEGER NOT NULL DEFAULT 1  -- 1 for success, 0 for error
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_llm_provider ON audit_logs(llm_provider)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_success ON audit_logs(success)
            """)
            
            conn.commit()
    
    def log_query(
        self,
        question: str,
        answer: Optional[str] = None,
        llm_provider: str = "unknown",
        llm_model: str = "unknown",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        collections_searched: Optional[List[str]] = None,
        num_sources_found: int = 0,
        num_sources_cited: int = 0,
        max_results: int = 5,
        min_score: float = 0.5,
        answer_length: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        success: bool = True
    ) -> int:
        """
        Log a query with token usage information
        
        Returns:
            int: The ID of the inserted log entry
        """
        timestamp = datetime.now().isoformat()
        
        # Calculate total tokens if not provided
        if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens
        
        # Calculate answer length if not provided
        if answer_length is None and answer:
            answer_length = len(answer)
        
        # Convert collections to JSON
        collections_json = json.dumps(collections_searched) if collections_searched else "[]"
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (
                    timestamp, question, answer, llm_provider, llm_model,
                    prompt_tokens, completion_tokens, total_tokens,
                    collections_searched, num_sources_found, num_sources_cited,
                    max_results, min_score, answer_length, response_time_ms,
                    error_message, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, question, answer, llm_provider, llm_model,
                prompt_tokens, completion_tokens, total_tokens,
                collections_json, num_sources_found, num_sources_cited,
                max_results, min_score, answer_length, response_time_ms,
                error_message, 1 if success else 0
            ))
            return cursor.lastrowid
    
    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        llm_provider: Optional[str] = None,
        success_only: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            llm_provider: Filter by LLM provider
            success_only: Only return successful queries
            start_date: Filter logs from this date (ISO format)
            end_date: Filter logs until this date (ISO format)
        
        Returns:
            List of log dictionaries
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if llm_provider:
            query += " AND llm_provider = ?"
            params.append(llm_provider)
        
        if success_only:
            query += " AND success = 1"
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            logs = []
            for row in rows:
                log = dict(row)
                # Parse collections JSON
                if log['collections_searched']:
                    try:
                        log['collections_searched'] = json.loads(log['collections_searched'])
                    except:
                        log['collections_searched'] = []
                else:
                    log['collections_searched'] = []
                logs.append(log)
            
            return logs
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics from audit logs"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute("SELECT COUNT(*) as total FROM audit_logs")
            total_queries = cursor.fetchone()['total']
            
            # Successful queries
            cursor.execute("SELECT COUNT(*) as total FROM audit_logs WHERE success = 1")
            successful_queries = cursor.fetchone()['total']
            
            # Total tokens used
            cursor.execute("SELECT SUM(total_tokens) as total FROM audit_logs WHERE total_tokens IS NOT NULL")
            total_tokens_result = cursor.fetchone()
            total_tokens = total_tokens_result['total'] if total_tokens_result['total'] else 0
            
            # Average tokens per query
            cursor.execute("SELECT AVG(total_tokens) as avg FROM audit_logs WHERE total_tokens IS NOT NULL")
            avg_tokens_result = cursor.fetchone()
            avg_tokens = avg_tokens_result['avg'] if avg_tokens_result['avg'] else 0
            
            # Token usage by provider
            cursor.execute("""
                SELECT 
                    llm_provider,
                    COUNT(*) as query_count,
                    SUM(total_tokens) as total_tokens,
                    AVG(total_tokens) as avg_tokens
                FROM audit_logs
                WHERE total_tokens IS NOT NULL
                GROUP BY llm_provider
            """)
            provider_stats = [dict(row) for row in cursor.fetchall()]
            
            # Most common collections
            cursor.execute("""
                SELECT collections_searched, COUNT(*) as count
                FROM audit_logs
                WHERE collections_searched IS NOT NULL AND collections_searched != '[]'
                GROUP BY collections_searched
                ORDER BY count DESC
                LIMIT 10
            """)
            collection_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'failed_queries': total_queries - successful_queries,
                'total_tokens': total_tokens,
                'average_tokens_per_query': round(avg_tokens, 2) if avg_tokens else 0,
                'token_usage_by_provider': provider_stats,
                'most_common_collections': collection_stats
            }
    
    def clear_logs(self, days_to_keep: Optional[int] = None):
        """Clear old logs, optionally keeping logs from the last N days"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            if days_to_keep:
                cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                from datetime import timedelta
                cutoff_date = cutoff_date - timedelta(days=days_to_keep)
                cutoff_iso = cutoff_date.isoformat()
                cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_iso,))
            else:
                cursor.execute("DELETE FROM audit_logs")
            
            deleted_count = cursor.rowcount
            return deleted_count


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
