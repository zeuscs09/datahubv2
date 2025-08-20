import json
import frappe
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Dict, Any, Optional


class PGClient:
    """PostgreSQL Client for connecting to external PostgreSQL database"""
    
    def __init__(self):
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load PostgreSQL configuration from PG Logs doctype"""
        try:
            self.config = frappe.get_single("PG Logs")
        except Exception as e:
            frappe.log_error(f"Failed to load PG Logs config: {str(e)}", "PGClient Config Error")
            raise
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters from config"""
        if not self.config:
            raise Exception("PG Logs configuration not found")
        
        return {
            'host': self.config.host,
            'port': int(self.config.port) if self.config.port else 5432,
            'database': self.config.db_name,
            'user': self.config.user_name,
            'password': self.config.password
        }
    
    @contextmanager
    def get_connection(self):
        """Get PostgreSQL connection with context manager"""
        conn = None
        try:
            params = self.get_connection_params()
            conn = psycopg2.connect(**params)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            frappe.log_error(f"PostgreSQL connection error: {str(e)}", "PGClient Connection Error")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Get PostgreSQL cursor with context manager"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor, conn
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()


class PGLogger:
    """PostgreSQL Logger for inserting data logs"""
    
    def __init__(self):
        self.client = PGClient()
        self.table_name = "my_data_log"
    
    def create_log_table_if_not_exists(self):
        """Create the log table if it doesn't exist"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            ref_id VARCHAR(255) NOT NULL,
            ref_module VARCHAR(255) NOT NULL,
            json_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_ref_id ON {self.table_name} (ref_id);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_ref_module ON {self.table_name} (ref_module);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created_at ON {self.table_name} (created_at);
        """
        
        try:
            with self.client.get_cursor() as (cursor, conn):
                cursor.execute(create_table_sql)
                conn.commit()
                frappe.logger().info(f"Log table {self.table_name} created or already exists")
        except Exception as e:
            frappe.log_error(f"Failed to create log table: {str(e)}", "PGLogger Table Creation Error")
            raise
    
    def insert_log(self, ref_id: str, ref_module: str, json_data: Dict[str, Any]) -> bool:
        """
        Insert a log entry into the PostgreSQL database
        
        Args:
            ref_id (str): Reference ID for the log entry
            ref_module (str): Module name that generated the log
            json_data (dict): JSON data to be stored
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            insert_sql = f"""
            INSERT INTO {self.table_name} (ref_id, ref_module, json_data)
            VALUES (%s, %s, %s)
            """
            
            with self.client.get_cursor() as (cursor, conn):
                cursor.execute(insert_sql, (ref_id, ref_module, json.dumps(json_data)))
                conn.commit()
                
                frappe.logger().info(f"Successfully inserted log for ref_id: {ref_id}, module: {ref_module}")
                return True
                
        except Exception as e:
            error_msg = f"Failed to insert log for ref_id: {ref_id}, module: {ref_module}. Error: {str(e)}"
            frappe.log_error(error_msg, "PGLogger Insert Error")
            return False
    
    def insert_log_with_before_after(self, ref_id: str, ref_module: str, 
                                   before_data: Dict[str, Any], 
                                   after_data: Dict[str, Any]) -> bool:
        """
        Convenience method to insert log with before/after data structure
        
        Args:
            ref_id (str): Reference ID for the log entry
            ref_module (str): Module name that generated the log
            before_data (dict): Data before the change
            after_data (dict): Data after the change
        
        Returns:
            bool: True if successful, False otherwise
        """
        json_data = {
            "before": before_data,
            "after": after_data
        }
        
        return self.insert_log(ref_id, ref_module, json_data)
    
    def get_logs(self, ref_id: Optional[str] = None, ref_module: Optional[str] = None, 
                 limit: int = 100, offset: int = 0) -> list:
        """
        Retrieve logs from the database
        
        Args:
            ref_id (str, optional): Filter by reference ID
            ref_module (str, optional): Filter by module
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip
        
        Returns:
            list: List of log records
        """
        try:
            where_conditions = []
            params = []
            
            if ref_id:
                where_conditions.append("ref_id = %s")
                params.append(ref_id)
            
            if ref_module:
                where_conditions.append("ref_module = %s")
                params.append(ref_module)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"""
            SELECT * FROM {self.table_name}
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            
            with self.client.get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            frappe.log_error(f"Failed to retrieve logs: {str(e)}", "PGLogger Retrieve Error")
            return []


# Convenience functions for easy import
def get_pg_client() -> PGClient:
    """Get a PostgreSQL client instance"""
    return PGClient()


def get_pg_logger() -> PGLogger:
    """Get a PostgreSQL logger instance"""
    return PGLogger()


def log_to_postgres(ref_id: str, ref_module: str, json_data: Dict[str, Any]) -> bool:
    """
    Quick function to log data to PostgreSQL
    
    Args:
        ref_id (str): Reference ID for the log entry
        ref_module (str): Module name that generated the log
        json_data (dict): JSON data to be stored
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger = get_pg_logger()
    return logger.insert_log(ref_id, ref_module, json_data)


def log_before_after_to_postgres(ref_id: str, ref_module: str, 
                                before_data: Dict[str, Any], 
                                after_data: Dict[str, Any]) -> bool:
    """
    Quick function to log before/after data to PostgreSQL
    
    Args:
        ref_id (str): Reference ID for the log entry
        ref_module (str): Module name that generated the log
        before_data (dict): Data before the change
        after_data (dict): Data after the change
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger = get_pg_logger()
    return logger.insert_log_with_before_after(ref_id, ref_module, before_data, after_data)