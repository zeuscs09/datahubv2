import frappe
import json
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..helper import Helper
from ...lib.ic360.client import IC360Client
from ...utils.logger import get_logger

logger = get_logger(__name__)

class SDIncidentService:
    """Service class สำหรับจัดการข้อมูล SD Incident"""
    
    def __init__(self):
        self.helper = Helper()
        self.ic360_client = IC360Client()
        
    def get_incident_api_config(self) -> Dict[str, Any]:
        """ดึงข้อมูล configuration จาก DH Incident API Config"""
        try:
            config = frappe.get_single("DH Incident API Config")
            return {
                'sql_query': config.sql_query,
                'url_endpoint': config.url_endpoint,
                'header': json.loads(config.header) if config.header else {},
                'last_sync': config.last_sync,
                'chunk_size': config.chunk_size or 100,
                'username': config.username,
                'password': config.password,
                'token_last_updated': config.token_last_updated
            }
        except Exception as e:
            logger.error(f"Error getting incident API config: {str(e)}")
            raise
    
    def replace_query_placeholders(self, query: str, config: Dict[str, Any]) -> str:
        """แทนที่ placeholder ใน SQL query ด้วยค่าจาก config"""
        try:
            # Log ข้อมูล config ก่อนแทนที่
            logger.info(f"Original query: {query}")
            logger.info(f"Config last_sync: {config['last_sync']} (type: {type(config['last_sync'])})")
            
            # จัดการ last_sync: ถ้าเป็น NULL ให้ใช้วันที่ 30 วันที่แล้ว
            if config['last_sync']:
                last_sync_value = f"'{config['last_sync']}'"
            else:
                # ใช้วันที่ 30 วันที่แล้วเป็น default ถ้า last_sync เป็น NULL
                from datetime import datetime, timedelta
                default_date = datetime.now() - timedelta(days=30)
                default_date_str = default_date.strftime('%Y-%m-%d %H:%M:%S')
                last_sync_value = f"'{default_date_str}'"
                logger.info(f"last_sync is NULL, using default date: {default_date_str}")
            
            replacements = {
                '{last_sync}': last_sync_value
            }
            
            # แทนที่ placeholder ทั้งหมด
            for placeholder, value in replacements.items():
                query = query.replace(placeholder, str(value))
                logger.info(f"Replaced {placeholder} with {value}")
                
            logger.info(f"Query after placeholder replacement: {query}")
            return query
            
        except Exception as e:
            logger.error(f"Error replacing query placeholders: {str(e)}")
            raise
    
    def fetch_incident_data(self, query: str) -> List[Dict[str, Any]]:
        """ดึงข้อมูลจาก IC360 ทั้งหมด"""
        try:
            logger.info(f"Executing query: {query}")
            
            # ดึงข้อมูลจาก IC360 ทั้งหมด
            all_data = self.ic360_client.execute_query(query)
                    
            logger.info(f"Total records fetched: {len(all_data)}")
            
            # Debug: แสดงข้อมูลตัวอย่างถ้ามี
            if all_data and len(all_data) > 0:
                logger.info(f"Sample record: {all_data[0]}")
            else:
                logger.warning("No data returned from query")
                
            return all_data
            
        except Exception as e:
            logger.error(f"Error fetching incident data: {str(e)}")
            raise
    
    def split_data_into_chunks(self, data: List[Dict[str, Any]], chunk_size: int) -> List[List[Dict[str, Any]]]:
        """แบ่งข้อมูลเป็น chunks ตาม chunk_size"""
        try:
            chunks = []
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                chunks.append(chunk)
            
            logger.info(f"Split {len(data)} records into {len(chunks)} chunks of size {chunk_size}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting data into chunks: {str(e)}")
            raise
    
    def format_data_to_json(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """แปลงข้อมูลเป็น JSON รูปแบบที่ต้องการ"""
        try:
            return {
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error formatting data to JSON: {str(e)}")
            raise
    
    def create_webhook_outbound_record(self, config: Dict[str, Any], payload: Dict[str, Any], chunk_info: str = "") -> str:
        """สร้างระเบียน DH Webhook Outbound"""
        try:
            # สร้าง outbound_id
            outbound_id = self.helper.generate_code()
            
            # สร้าง webhook URL
            webhook_url = f"{config['url_endpoint'].rstrip('/')}/ic360-incidents"
            
            # เพิ่มข้อมูล chunk ใน sent_to ถ้ามี
            sent_to = f"SD_Incident_{chunk_info}" if chunk_info else "SD_Incident"
            
            # สร้างระเบียน DH Webhook Outbound
            doc = frappe.get_doc({
                'doctype': 'DH Webhook Outbound',
                'outbound_id': outbound_id,
                'sent_to': sent_to,
                'webhook_url': webhook_url,
                'payload': json.dumps(payload, ensure_ascii=False, indent=2),
                'headers': json.dumps(config['header'], ensure_ascii=False, indent=2),
                'status': 'Pending',
                'created_at': datetime.now(),
                'retry_count': 0
            })
            
            doc.insert()
            frappe.db.commit()
            
            logger.info(f"Created webhook outbound record: {doc.name} with outbound_id: {outbound_id} ({sent_to})")
            return doc.name
            
        except Exception as e:
            logger.error(f"Error creating webhook outbound record: {str(e)}")
            raise
    
    def sync_incidents_to_sd(self) -> Dict[str, Any]:
        """หลัก function สำหรับ sync incident data ไป SD"""
        try:
            # 1. ดึง configuration
            config = self.get_incident_api_config()
            
            if not config['sql_query']:
                raise Exception("SQL Query not configured in DH Incident API Config")
            
            # 2. แทนที่ placeholder ใน query
            processed_query = self.replace_query_placeholders(config['sql_query'], config)
            
            # 3. ดึงข้อมูลจาก IC360 ทั้งหมด
            incident_data = self.fetch_incident_data(processed_query)
            
            if not incident_data:
                logger.info("No incident data found")
                # อัพเดท last_sync ถึงแม้จะไม่มีข้อมูลใหม่
                self.update_last_sync_time()
                return {
                    'success': True,
                    'message': 'No new incident data to sync',
                    'records_processed': 0,
                    'chunks_created': 0,
                    'outbound_docs': []
                }
            
            # 4. แบ่งข้อมูลเป็น chunks
            data_chunks = self.split_data_into_chunks(incident_data, config['chunk_size'])
            
            # 5. สร้าง webhook outbound สำหรับแต่ละ chunk
            outbound_docs = []
            
            for i, chunk_data in enumerate(data_chunks, 1):
                # แปลงข้อมูลเป็น JSON format สำหรับ chunk นี้
                formatted_payload = self.format_data_to_json(chunk_data)
                
                # สร้างระเบียน webhook outbound สำหรับ chunk นี้
                outbound_doc_name = self.create_webhook_outbound_record(
                    config, 
                    formatted_payload, 
                    chunk_info=f"chunk_{i}_of_{len(data_chunks)}"
                )
                outbound_docs.append(outbound_doc_name)
                
                logger.info(f"Created chunk {i}/{len(data_chunks)} with {len(chunk_data)} records")
            
            # 6. อัพเดท last_sync time
            self.update_last_sync_time()
            
            return {
                'success': True,
                'message': f'Successfully synced {len(incident_data)} incident records in {len(data_chunks)} chunks',
                'records_processed': len(incident_data),
                'chunks_created': len(data_chunks),
                'outbound_docs': outbound_docs
            }
            
        except Exception as e:
            error_msg = f"Error syncing incidents to SD: {str(e)}"
            logger.error(error_msg)
            frappe.log_error(message=error_msg, title="SD Incident Sync Error")
            
            return {
                'success': False,
                'message': error_msg,
                'records_processed': 0,
                'chunks_created': 0,
                'outbound_docs': []
            }
        finally:
            # ปิดการเชื่อมต่อฐานข้อมูล
            self.ic360_client.disconnect()
    
    def update_last_sync_time(self):
        """อัพเดทเวลา last_sync ใน configuration"""
        try:
            config = frappe.get_single("DH Incident API Config")
            config.last_sync = datetime.now()
            config.save()
            frappe.db.commit()
            
            logger.info(f"Updated last_sync time to: {config.last_sync}")
            
        except Exception as e:
            logger.error(f"Error updating last_sync time: {str(e)}")
    
    def prepare_test_query(self, query: str) -> str:
        """เตรียม query สำหรับการทดสอบโดยเพิ่ม LIMIT 5
        
        Args:
            query (str): SQL query ต้นฉบับ
            
        Returns:
            str: Query ที่เพิ่ม LIMIT 5 แล้ว
        """
        try:
            # ลบ whitespace และ semicolon ที่อาจมีอยู่ท้าย query
            clean_query = query.strip().rstrip(';')
            
            # ตรวจสอบว่ามี LIMIT อยู่แล้วหรือไม่ (case insensitive)
            if re.search(r'\bLIMIT\s+\d+', clean_query, re.IGNORECASE):
                # ถ้ามี LIMIT อยู่แล้ว ให้แทนที่ด้วย LIMIT 5
                test_query = re.sub(r'\bLIMIT\s+\d+', 'LIMIT 5', clean_query, flags=re.IGNORECASE)
            else:
                # ถ้าไม่มี LIMIT ให้เพิ่มเข้าไป
                test_query = f"{clean_query} LIMIT 5"
                
            return test_query
            
        except Exception as e:
            logger.error(f"Error preparing test query: {str(e)}")
            # ถ้าเกิดข้อผิดพลาด ให้ใช้ query ต้นฉบับ
            return query
    
    def login_and_get_token(self) -> Dict[str, Any]:
        """Login และดึง token จาก API
        
        Returns:
            Dict[str, Any]: ผลลัพธ์การ login และ token
        """
        try:
            # ดึง config
            config = self.get_incident_api_config()
            
            if not config['username'] or not config['password']:
                raise Exception("Username หรือ Password ไม่ได้ตั้งค่าใน DH Incident API Config")
            
            if not config['url_endpoint']:
                raise Exception("URL Endpoint ไม่ได้ตั้งค่าใน DH Incident API Config")
            
            # สร้าง login URL
            login_url = f"{config['url_endpoint'].rstrip('/')}/login"
            
            # เตรียม payload สำหรับ login
            login_payload = {
                "username": config['username'],
                "password": config['password']
            }
            
            # ใช้ requests.Session และใส่ cookies ใน headers แทน
            session = requests.Session()
            
            # ล้าง cookies ของ session ให้เหมือนเริ่มต้นใหม่
            session.cookies.clear()
            
            # เตรียม headers ตาม curl ที่ใช้งานได้ (รวม cookies)
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime/7.39.0",
                "Cookie": "ak_bmsc=19494F905D64A9FA8FFDD6EB922EBA78~000000000000000000000000000000~YAAQJPObenNoVrGYAQAAdj01yBwSDBCB9M/tYBp0vQZx7sH5AxYc6uugc+JDJ80BzJ6Ayfi15t8xE1kg8J3YgTH2l1Ob2kzF0sQT7E3KHzlbarlAllcwpZWywbByNKekSpHRLW/gcisvGLbFNBHT5+Vt6VDYYxuxr0h6OCTnRuwV6owCPAut+EsaNruEbz1MtfvBQE5PJelDaer/qTxepS87SNPsthKfas0WqZBZkTUBywfLhmASjJ2bN1kRPeOtjH2wzVf+7m2qwgeNfmnslCH8vzas4UWAHCUg3zDn1NfqJ0CgZElJX9D+HmLoOKbGD3PeMegjFZ801tlSHQwueXIiKVxG7BgTeQG9LHclMP09kG6NKw5o1Ws7"
            }
            
            logger.info(f"Attempting login to: {login_url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Payload: {login_payload}")
            
            # ส่ง POST request เพื่อ login ผ่าน session
            response = session.post(
                login_url,
                headers=headers,
                json=login_payload,
                timeout=30,
                verify=False  # ปิด SSL verification ชั่วคราว
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Session cookies: {dict(session.cookies)}")
            
            # แสดง response text เสมอเพื่อ debug
            try:
                response_text = response.text[:500]  # แสดงแค่ 500 characters แรก
                logger.info(f"Response text (first 500 chars): {response_text}")
            except:
                logger.info("Could not read response text")
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                # ลองใช้ data แทน json
                logger.info("Retrying with data instead of json...")
                
                response = session.post(
                    login_url,
                    headers=headers,
                    data=json.dumps(login_payload),
                    timeout=30,
                    verify=False
                )
                
                logger.info(f"Retry response status: {response.status_code}")
                try:
                    retry_response_text = response.text[:500]
                    logger.info(f"Retry response text (first 500 chars): {retry_response_text}")
                except:
                    logger.info("Could not read retry response text")
                    
                if response.status_code != 200:
                    logger.error(f"Retry failed - HTTP {response.status_code}: {response.text}")
                    
            # ปิด session
            session.close()
            
            # ตรวจสอบ response status
            response.raise_for_status()
            
            # แปลง response เป็น JSON
            response_data = response.json()
            
            # ตรวจสอบว่า login สำเร็จหรือไม่
            if not response_data.get('success'):
                raise Exception(f"Login failed: {response_data.get('message', 'Unknown error')}")
            
            # ดึง token จาก response
            token_data = response_data.get('token', {})
            token = token_data.get('token')
            
            if not token:
                raise Exception("ไม่พบ token ใน response จาก API")
            
            logger.info("Login successful, token received")
            
            return {
                'success': True,
                'token': token,
                'user_info': response_data.get('user', {}),
                'response_data': response_data
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during login: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'token': None
            }
        except Exception as e:
            error_msg = f"Error logging in to get token: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'token': None
            }
    
    def update_token_in_config(self, token: str) -> Dict[str, Any]:
        """อัพเดท token ใน configuration ต่างๆ
        
        Args:
            token (str): JWT token ที่ได้จาก login
            
        Returns:
            Dict[str, Any]: ผลลัพธ์การอัพเดท
        """
        try:
            # สร้าง header ใหม่ที่มี token
            new_header = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # อัพเดท DH Incident API Config
            config = frappe.get_single("DH Incident API Config")
            config.header = json.dumps(new_header, ensure_ascii=False, indent=2)
            config.token_last_updated = datetime.now()
            config.save()
            
            # อัพเดท DH Setting sd_header
            try:
                dh_setting = frappe.get_doc("DH Setting", "DH Setting")
                dh_setting.sd_header = json.dumps(new_header, ensure_ascii=False, indent=2)
                dh_setting.save()
                logger.info("Updated DH Setting sd_header successfully")
            except frappe.DoesNotExistError:
                logger.warning("DH Setting document not found, skipping sd_header update")
            except Exception as e:
                logger.warning(f"Could not update DH Setting sd_header: {str(e)}")
            
            # Commit การเปลี่ยนแปลง
            frappe.db.commit()
            
            logger.info(f"Token updated successfully in configuration at {datetime.now()}")
            
            return {
                'success': True,
                'message': 'Token updated in configuration successfully',
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error updating token in config: {str(e)}"
            logger.error(error_msg)
            frappe.db.rollback()
            
            return {
                'success': False,
                'message': error_msg
            }
    
    def refresh_token(self) -> Dict[str, Any]:
        """Refresh token โดยการ login ใหม่และอัพเดท configuration
        
        Returns:
            Dict[str, Any]: ผลลัพธ์การ refresh token
        """
        try:
            # Login เพื่อดึง token ใหม่
            login_result = self.login_and_get_token()
            
            if not login_result['success']:
                return {
                    'success': False,
                    'message': f"Login failed: {login_result['message']}",
                    'login_attempted': True
                }
            
            # อัพเดท token ใน configuration
            update_result = self.update_token_in_config(login_result['token'])
            
            if not update_result['success']:
                return {
                    'success': False,
                    'message': f"Token received but failed to update config: {update_result['message']}",
                    'login_attempted': True,
                    'token_received': True
                }
            
            return {
                'success': True,
                'message': 'Token refreshed and updated successfully',
                'login_attempted': True,
                'token_received': True,
                'config_updated': True,
                'updated_at': update_result['updated_at'],
                'user_info': login_result.get('user_info', {})
            }
            
        except Exception as e:
            error_msg = f"Error refreshing token: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'login_attempted': False
            }

# Utility functions สำหรับเรียกใช้จาก API หรือ background job
def sync_incidents():
    """Wrapper function สำหรับเรียกใช้จาก external"""
    service = SDIncidentService()
    return service.sync_incidents_to_sd()

@frappe.whitelist()
def manual_sync_incidents():
    """API endpoint สำหรับ manual sync
    
    ใช้เรียกจาก:
    - Browser console: frappe.call({method: 'datahubv2.core.sd_incident.service.manual_sync_incidents'})
    - API: POST /api/method/datahubv2.core.sd_incident.service.manual_sync_incidents
    """
    if not frappe.has_permission("DH Incident API Config", "write"):
        frappe.throw("Insufficient permissions")
    
    return sync_incidents()

@frappe.whitelist()
def test_sql_query(sql_query):
    """ทดสอบ SQL Query สำหรับใช้ใน JS
    
    Args:
        sql_query (str): SQL Query ที่จะทดสอบ
        
    Returns:
        dict: ผลลัพธ์การทดสอบ
    """
    if not frappe.has_permission("DH Incident API Config", "write"):
        frappe.throw("Insufficient permissions")
    
    service = None
    try:
        service = SDIncidentService()
        
        # ดึง config เพื่อแทนที่ placeholder
        config = service.get_incident_api_config()
        
        # แทนที่ placeholder ใน query
        processed_query = service.replace_query_placeholders(sql_query, config)
        
        # เตรียม query สำหรับทดสอบ (เพิ่ม LIMIT 5 อย่างปลอดภัย)
        test_query = service.prepare_test_query(processed_query)
        
        # ทดสอบ query
        test_data = service.ic360_client.execute_query(test_query)
        
        return {
            'success': True,
            'message': f'Query ทำงานได้ - พบข้อมูล {len(test_data)} records',
            'data': test_data,
            'processed_query': test_query
        }
        
    except Exception as e:
        error_msg = f"Error testing SQL query: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'message': error_msg,
            'data': []
        }
    finally:
        # ปิดการเชื่อมต่อฐานข้อมูล
        if service:
            service.ic360_client.disconnect()

@frappe.whitelist()
def debug_sync_query():
    """Debug function เพื่อดู query ที่จะใช้ใน sync จริง
    
    Returns:
        dict: ข้อมูล debug query และ config
    """
    if not frappe.has_permission("DH Incident API Config", "write"):
        frappe.throw("Insufficient permissions")
    
    service = None
    try:
        service = SDIncidentService()
        
        # ดึง config
        config = service.get_incident_api_config()
        
        # แทนที่ placeholder ใน query
        if not config['sql_query']:
            return {
                'success': False,
                'message': 'SQL Query not configured in DH Incident API Config',
                'data': {}
            }
            
        processed_query = service.replace_query_placeholders(config['sql_query'], config)
        
        # เพิ่มข้อมูล default date ถ้า last_sync เป็น NULL
        default_date_info = None
        if not config['last_sync']:
            from datetime import datetime, timedelta
            default_date = datetime.now() - timedelta(days=30)
            default_date_info = default_date.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'success': True,
            'message': 'Debug query information',
            'data': {
                'original_query': config['sql_query'],
                'processed_query': processed_query,
                'last_sync': config['last_sync'],
                'last_sync_type': str(type(config['last_sync'])),
                'default_date_used': default_date_info,
                'url_endpoint': config['url_endpoint'],
                'chunk_size': config['chunk_size'],
                'header_keys': list(config['header'].keys()) if config['header'] else []
            }
        }
        
    except Exception as e:
        error_msg = f"Error debugging sync query: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'message': error_msg,
            'data': {}
        }
    finally:
        if service:
            service.ic360_client.disconnect()

@frappe.whitelist()
def test_ic360_connection():
    """ทดสอบการเชื่อมต่อ IC360 database
    
    Returns:
        dict: ผลลัพธ์การทดสอบ connection
    """
    if not frappe.has_permission("DH Incident API Config", "write"):
        frappe.throw("Insufficient permissions")
    
    try:
        service = SDIncidentService()
        connection_result = service.ic360_client.test_connection()
        
        return {
            'success': connection_result['success'],
            'message': connection_result['message'],
            'data': connection_result['connection_info']
        }
        
    except Exception as e:
        error_msg = f"Error testing IC360 connection: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'message': error_msg,
            'data': None
        }

@frappe.whitelist()
def refresh_auth_token():
    """API endpoint สำหรับ refresh token ของ SD API
    
    Returns:
        dict: ผลลัพธ์การ refresh token
    """
    if not frappe.has_permission("DH Incident API Config", "write"):
        frappe.throw("Insufficient permissions")
    
    try:
        service = SDIncidentService()
        result = service.refresh_token()
        
        return result
        
    except Exception as e:
        error_msg = f"Error refreshing auth token: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'message': error_msg,
            'login_attempted': False
        }

# Wrapper function สำหรับ background job
def refresh_token_job():
    """Background job สำหรับ refresh token อัตโนมัติ"""
    try:
        service = SDIncidentService()
        result = service.refresh_token()
        
        if result['success']:
            logger.info(f"Scheduled token refresh successful: {result['message']}")
        else:
            logger.error(f"Scheduled token refresh failed: {result['message']}")
            frappe.log_error(
                message=f"Token refresh failed: {result['message']}", 
                title="SD Incident Token Refresh Error"
            )
        
        return result
        
    except Exception as e:
        error_msg = f"Error in scheduled token refresh: {str(e)}"
        logger.error(error_msg)
        frappe.log_error(message=error_msg, title="SD Incident Token Refresh Job Error")
        
        return {
            'success': False,
            'message': error_msg
        }

# Example configuration สำหรับ DH Incident API Config:
"""
SQL Query Example:
SELECT 
    phonenumber,
    incident_no,
    open_date,
    last_updated,
    contact_channel,
    cate,
    subcate,
    sub_subcate,
    moreinfo,
    status,
    product,
    formula,
    subject,
    activity_detail,
    solution_comment
FROM incidents 
WHERE last_updated > {last_sync}
ORDER BY last_updated ASC

URL Endpoint Example:
https://api.sd-system.com/v1/

Header Example:
{
    "Content-Type": "application/json",
    "Authorization": "Bearer your-api-token-here",
    "X-API-Key": "your-api-key-here"
}

Chunk Size Example: 100

วิธีการทำงาน:
1. ดึงข้อมูลจาก IC360 ทั้งหมดตาม SQL Query
2. แบ่งข้อมูลเป็น chunks ตาม chunk_size 
3. สร้าง DH Webhook Outbound แยกสำหรับแต่ละ chunk
4. แต่ละ chunk จะมี sent_to เป็น "SD_Incident_chunk_1_of_5" เป็นต้น

ผลลัพธ์:
- หากมีข้อมูล 250 records และ chunk_size = 100
- จะสร้าง webhook outbound 3 อัน:
  * SD_Incident_chunk_1_of_3 (100 records)
  * SD_Incident_chunk_2_of_3 (100 records)  
  * SD_Incident_chunk_3_of_3 (50 records)

สำหรับการใช้งานใน Background Job:
1. เพิ่มใน hooks.py:
   scheduler_events = {
       "cron": {
           "0 */6 * * *": [  # ทุก 6 ชั่วโมง
               "datahubv2.core.sd_incident.service.sync_incidents"
           ]
       }
   }

2. หรือเรียกใช้ manual:
   frappe.enqueue('datahubv2.core.sd_incident.service.sync_incidents', queue='long')
"""
