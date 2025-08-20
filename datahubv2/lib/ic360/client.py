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
            
    def test_connection(self) -> Dict:
        """ทดสอบการเชื่อมต่อฐานข้อมูล
        
        Returns:
            Dict: ผลลัพธ์การทดสอบ
        """
        try:
            logger.info("IC360Client: Testing database connection")
            
            # ทดสอบการเชื่อมต่อ
            if not self.connect():
                return {
                    'success': False,
                    'message': 'Failed to connect to database',
                    'connection_info': None
                }
            
            # ทดสอบ query ง่ายๆ
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 as test_value, NOW() as current_time")
            result = cursor.fetchone()
            cursor.close()
            
            return {
                'success': True,
                'message': 'Database connection successful',
                'connection_info': {
                    'host': self.settings.host,
                    'database': self.settings.database,
                    'user': self.settings.username,
                    'port': self.settings.port,
                    'connection_status': 'Connected',
                    'test_query_result': result
                }
            }
            
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'connection_info': {
                    'host': getattr(self.settings, 'host', 'N/A'),
                    'database': getattr(self.settings, 'database', 'N/A'),
                    'user': getattr(self.settings, 'username', 'N/A'),
                    'port': getattr(self.settings, 'port', 'N/A'),
                    'connection_status': 'Failed'
                }
            }
        finally:
            self.disconnect()
            
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
            logger.info(f"IC360Client: Attempting to execute query")
            logger.info(f"IC360Client: Query length: {len(query)} characters")
            logger.info(f"IC360Client: Query preview: {query[:200]}...")
            
            if not self.connect():
                raise Exception("Failed to connect to database")
                
            logger.info(f"IC360Client: Database connection successful")
            logger.info(f"IC360Client: Connection closed status: {self.conn.closed}")
            
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info(f"IC360Client: Cursor created successfully")
            
            # แปลงค่าว่างเป็น None สำหรับฟิลด์ที่เป็น integer
            if params:
                logger.info(f"IC360Client: Processing parameters: {type(params)}")
                # สำหรับ dict parameters
                if isinstance(params, dict):
                    for key, value in params.items():
                        if value == '':
                            params[key] = None
                # สำหรับ list parameters
                elif isinstance(params, list):
                    params = [None if x == '' else x for x in params]
            
            # ตรวจสอบประเภทของพารามิเตอร์และดำเนินการตามความเหมาะสม
            logger.info(f"IC360Client: Executing query with params: {params}")
            
            if params is None:
                cursor.execute(query)
            elif isinstance(params, dict):
                cursor.execute(query, params)
            elif isinstance(params, list):
                cursor.execute(query, params)
            else:
                # แปลงเป็นลิสต์หากไม่ใช่ dict หรือ list
                cursor.execute(query, [None if params == '' else params])
            
            logger.info(f"IC360Client: Query executed successfully")
            
            if query.strip().upper().startswith('SELECT'):
                logger.info(f"IC360Client: Fetching SELECT query results")
                results = cursor.fetchall()
                logger.info(f"IC360Client: Raw fetchall() returned {len(results)} rows")
                
                if results:
                    logger.info(f"IC360Client: Sample raw result (first row): {dict(results[0])}")
                
                converted_results = [dict(row) for row in results]
                logger.info(f"IC360Client: Converted to {len(converted_results)} dict records")
                
                if converted_results:
                    logger.info(f"IC360Client: Sample converted result: {converted_results[0]}")
                else:
                    logger.warning(f"IC360Client: No results after conversion")
                
                return converted_results
            else:
                logger.info(f"IC360Client: Non-SELECT query, committing")
                self.conn.commit()
                return []
                
        except Exception as e:
            error_msg = f"IC360Client Query error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"IC360Client: Exception type: {type(e)}")
            frappe.log_error(message=f"{error_msg}\nQuery: {query}\nParams: {params}", title="IC360 Query Error")
            if self.conn:
                self.conn.rollback()
            raise
            
        finally:
            if cursor:
                logger.info(f"IC360Client: Closing cursor")
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
                province_name = %(province_name)s
                AND amphur_name = %(amphur_name)s
                AND district_name = %(district_name)s
            LIMIT 1
        """
        params = {
            "province_name": province_name,
            "amphur_name": amphur_name,
            "district_name": district_name
        }
        return self.execute_query(query, params) 