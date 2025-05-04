import frappe
import psycopg2
import psycopg2.extras
from typing import Optional, List, Dict, Union
from ...utils.logger import get_logger

logger = get_logger(__name__)

class IC360Client:
    """PostgreSQL client for IC360"""
    
    def __init__(self):
        self.settings = frappe.get_single("DH Setting")
        self.conn = None
        
    def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            if self.conn and not self.conn.closed:
                return True
                
            self.conn = psycopg2.connect(
                host=self.settings.host,
                database=self.settings.database,
                user=self.settings.username,
                password=self.settings.password,
                port=self.settings.port
            )
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def execute_query(self, query: str, params: Union[List, Dict] = None) -> List[Dict]:
        """Execute query and return results as dict
        
        Args:
            query: SQL query string
            params: Parameters for the query, can be list or dict
            
        Returns:
            List of dictionaries for SELECT queries, empty list for others
        """
        cursor = None
        try:
            if not self.connect():
                raise Exception("Failed to connect to database")
                
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # ตรวจสอบประเภทของพารามิเตอร์และดำเนินการตามความเหมาะสม
            if params is None:
                cursor.execute(query)
            elif isinstance(params, dict):
                cursor.execute(query, params)
            elif isinstance(params, list):
                cursor.execute(query, params)
            else:
                # แปลงเป็นลิสต์หากไม่ใช่ dict หรือ list
                cursor.execute(query, [params])
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self.conn.commit()
                return []
                
        except Exception as e:
            error_msg = f"Query error: {str(e)}"
            logger.error(error_msg)
            frappe.log_error(message=f"{error_msg}\nQuery: {query}\nParams: {params}", title="IC360 Query Error")
            if self.conn:
                self.conn.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()

    def get_area_info(self, province_name: str, amphur_name: str, district_name: str) -> List[Dict]:
        """ดึงข้อมูลพื้นที่จาก IC360
        
        Args:
            province_name: ชื่อจังหวัด
            amphur_name: ชื่ออำเภอ
            district_name: ชื่อตำบล
            
        Returns:
            List[Dict]: ข้อมูลพื้นที่ที่ตรงกับเงื่อนไข
        """
        query = """
            SELECT
                province_code,
                province_name,
                amphur_code,
                amphur_name,
                district_code,
                district_name,
                zipcode 
            FROM
                ks_province
            WHERE 
                province_name = %s
                AND amphur_name = %s
                AND district_name = %s
            LIMIT 1
        """
        params = [province_name, amphur_name, district_name]
        return self.execute_query(query, params) 