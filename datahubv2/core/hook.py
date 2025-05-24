import frappe
import requests
import json
from datetime import datetime

def send_webhook_outbound(doc, method=None):
    """ส่งข้อมูล webhook เมื่อสถานะเป็น Pending"""
    if doc.status == "Pending" and doc.webhook_url:
        try:
            # ส่งข้อมูลไปยัง webhook URL
            send_webhook_data(doc)
        except Exception as e:
            frappe.log_error(
                message=f"Webhook send error: {str(e)}", 
                title=f"Webhook Error - {doc.name}"
            )

def send_webhook_data(doc):
    """ส่งข้อมูล webhook ไปยัง URL ปลายทาง"""
    try:
        # เตรียม headers - ใช้ headers ที่ส่งมาใน doc.headers
        headers = {"Content-Type": "application/json"}
        
        if doc.headers:
            try:
                custom_headers = json.loads(doc.headers)
                
                # ถ้าผลลัพธ์เป็น string แสดงว่าเป็น double-encoded JSON
                if isinstance(custom_headers, str):
                    frappe.log_error(
                        message=f"Double-encoded JSON detected, parsing again: {custom_headers}", 
                        title=f"Webhook Double JSON - {doc.name}"
                    )
                    custom_headers = json.loads(custom_headers)
                
                if isinstance(custom_headers, dict):
                    # ใช้ custom_headers โดยตรง แทนการ update
                    headers = custom_headers
                    frappe.log_error(
                        message=f"Using custom headers: {headers}", 
                        title=f"Webhook Custom Headers Applied - {doc.name}"
                    )
                else:
                    frappe.log_error(
                        message=f"Custom headers is still not a dict after parsing: {type(custom_headers)}", 
                        title=f"Webhook Still Not Dict Error - {doc.name}"
                    )
            except json.JSONDecodeError as e:
                frappe.log_error(
                    message=f"JSON decode error: {str(e)}, Headers: {doc.headers}", 
                    title=f"Webhook JSON Error - {doc.name}"
                )
                raise Exception(f"Invalid headers JSON: {str(e)}")
        
        frappe.log_error(
            message=f"Final Headers: {headers}", 
            title=f"Webhook Final Headers - {doc.name}"
        )
        # เตรียม payload
        payload_data = {}
        if doc.payload:
            try:
                payload_data = json.loads(doc.payload)
            except json.JSONDecodeError:
                raise Exception("Invalid payload JSON")
        frappe.log_error(
            message=f"Payload: {payload_data}", 
            title=f"Webhook Payload - {doc.name}"
        )
        # บันทึกเวลาที่เริ่มส่ง
        doc.sent_at = datetime.now()
        doc.save(ignore_permissions=True)
        
        # ส่ง HTTP Request
        response = requests.post(
            doc.webhook_url,
            json=payload_data,
            headers=headers,
            timeout=30
        )
        
        # บันทึกผลลัพธ์
        doc.response_code = str(response.status_code)
        
        # จัดการ response body
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                response_json = response.json()
                doc.response_body = json.dumps(response_json, ensure_ascii=False, indent=2)
            else:
                doc.response_body = response.text
        except:
            doc.response_body = response.text
        
        doc.completed_at = datetime.now()
        
        # ตรวจสอบสถานะ response
        if response.status_code in [200, 201, 202]:
            doc.status = "Sent"
            doc.error_message = ""
        else:
            doc.status = "Failed"
            doc.error_message = f"HTTP {response.status_code}: {response.text}"
            doc.retry_count = (doc.retry_count or 0) + 1
        
    except requests.exceptions.Timeout:
        doc.status = "Failed"
        doc.error_message = "Request timeout (30 seconds)"
        doc.retry_count = (doc.retry_count or 0) + 1
        doc.completed_at = datetime.now()
        
    except requests.exceptions.ConnectionError:
        doc.status = "Failed"
        doc.error_message = "Connection error - Unable to connect to webhook URL"
        doc.retry_count = (doc.retry_count or 0) + 1
        doc.completed_at = datetime.now()
        
    except requests.exceptions.RequestException as e:
        doc.status = "Failed"
        doc.error_message = f"Request error: {str(e)}"
        doc.retry_count = (doc.retry_count or 0) + 1
        doc.completed_at = datetime.now()
        
    except Exception as e:
        doc.status = "Failed"
        doc.error_message = f"Unexpected error: {str(e)}"
        doc.retry_count = (doc.retry_count or 0) + 1
        doc.completed_at = datetime.now()
        
        # Log unexpected errors
        frappe.log_error(
            message=f"Unexpected webhook error: {str(e)}", 
            title=f"Webhook Unexpected Error - {doc.name}"
        )
    
    finally:
        # บันทึกผลลัพธ์สุดท้าย
        doc.save(ignore_permissions=True)

def send_pending_webhook():
    """ส่ง webhook ที่สถานะเป็น Pending"""
    webhooks = frappe.get_all("DH Webhook Outbound", filters={"status": "Pending"}, fields=["name"])
    for webhook in webhooks:
        doc = frappe.get_doc("DH Webhook Outbound", webhook.name)
        send_webhook_data(doc)

def retry_failed_webhooks():
    """ฟังก์ชันสำหรับ retry webhook ที่ล้มเหลว"""
    try:
        # ดึง webhook ที่ล้มเหลวและยังไม่เกิน retry limit
        failed_webhooks = frappe.get_all(
            "DH Webhook Outbound",
            filters={
                "status": "Failed",
                "retry_count": ["<", 3]  # retry สูงสุด 3 ครั้ง
            },
            fields=["name", "webhook_url", "retry_count"]
        )
        
        frappe.log_error(
            message=f"Found {len(failed_webhooks)} failed webhooks to retry", 
            title="Webhook Retry Process"
        )
        
        for webhook in failed_webhooks:
            try:
                doc = frappe.get_doc("DH Webhook Outbound", webhook.name)
                doc.status = "Pending"  # เปลี่ยนสถานะกลับเป็น Pending เพื่อ retry
                doc.error_message = f"Retrying... (Attempt {(doc.retry_count or 0) + 1}/3)"
                doc.save(ignore_permissions=True)
                
                # ส่งข้อมูลใหม่
                send_webhook_data(doc)
                
            except Exception as e:
                frappe.log_error(
                    message=f"Error retrying webhook {webhook.name}: {str(e)}", 
                    title="Webhook Retry Error"
                )
                
    except Exception as e:
        frappe.log_error(
            message=f"Error in retry_failed_webhooks: {str(e)}", 
            title="Webhook Retry Process Error"
        )

def get_webhook_stats():
    """ดึงสถิติการส่ง webhook"""
    try:
        stats = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count,
                sent_to,
                DATE(creation) as date
            FROM `tabDH Webhook Outbound`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY status, sent_to, DATE(creation)
            ORDER BY date DESC, sent_to, status
        """, as_dict=True)
        
        return stats
        
    except Exception as e:
        frappe.log_error(
            message=f"Error getting webhook stats: {str(e)}", 
            title="Webhook Stats Error"
        )
        return []

def cleanup_old_webhooks(days=30):
    """ลบ webhook records เก่าที่เกินกำหนด"""
    try:
        # ลบ records ที่เก่ากว่า X วัน และสถานะเป็น Sent
        deleted_count = frappe.db.sql("""
            DELETE FROM `tabDH Webhook Outbound`
            WHERE creation < DATE_SUB(NOW(), INTERVAL %s DAY)
            AND status = 'Sent'
        """, (days,))
        
        frappe.log_error(
            message=f"Cleaned up {deleted_count} old webhook records", 
            title="Webhook Cleanup"
        )
        
        return deleted_count
        
    except Exception as e:
        frappe.log_error(
            message=f"Error cleaning up webhooks: {str(e)}", 
            title="Webhook Cleanup Error"
        )
        return 0
